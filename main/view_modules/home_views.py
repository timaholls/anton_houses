"""Views для главной страницы и общих страниц"""
from django.shortcuts import render
from bson import ObjectId
from datetime import datetime
from ..services.mongo_service import get_mongo_connection, get_special_offers_from_mongo
from ..s3_service import PLACEHOLDER_IMAGE_URL


def home(request):
    """Главная страница"""
    # Получаем 9 популярных ЖК для главной страницы из unified_houses
    try:
        db = get_mongo_connection()
        unified_collection = db['unified_houses']
        
        # Получаем все ЖК с флагом is_featured
        featured_complexes = list(unified_collection.find({'is_featured': True}))
        
        if len(featured_complexes) > 9:
            # Если больше 9, показываем 9 случайных
            complexes = list(unified_collection.aggregate([
                {'$match': {'is_featured': True}},
                {'$sample': {'size': 9}}
            ]))
        else:
            # Если меньше или равно 9, показываем все
            complexes = featured_complexes
        
        # Добавляем поле id для совместимости с шаблонами
        for complex in complexes:
            complex['id'] = str(complex.get('_id'))
    except Exception as e:
        complexes = []

    # Получаем информацию о компании из MongoDB
    try:
        company_info = db['company_info'].find_one({'is_active': True})
        # Галерея компании - используем массив images
        company_gallery = []
        if company_info and company_info.get('images'):
            company_gallery = [{'image': img, 'title': 'Фото компании', 'description': ''} for img in company_info.get('images', [])[:6]]
    except Exception:
        company_info = None
        company_gallery = []
    
    # Статьи для главной из MongoDB
    try:
        import logging
        logger = logging.getLogger(__name__)
        home_articles = list(db['articles'].find({'show_on_home': True, 'is_active': True}).sort('published_date', -1).limit(3))
        logger.info(f"Home articles query: {{'show_on_home': True, 'is_active': True}}")
        logger.info(f"Found {len(home_articles)} home articles")
        for article in home_articles:
            logger.info(f"Home: {article.get('title', 'No title')} - Show on home: {article.get('show_on_home', 'No status')} - Active: {article.get('is_active', 'No status')}")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading home articles: {e}")
        home_articles = []

    # Акции для главной - теперь из MongoDB promotions (с падением назад на SQL)
    def build_offer_adapters(limit=9):
        try:
            db = get_mongo_connection()
            promotions = db['promotions']
            unified = db['unified_houses']
            q = {'is_active': True}
            items = []
            for p in promotions.find(q).sort('created_at', -1).limit(limit):
                complex_doc = unified.find_one({'_id': p.get('complex_id')}) if isinstance(p.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(p.get('complex_id')))})
                # Адаптер для совместимости с шаблонами
                class _Img: pass
                class _MainImg: pass
                class _RC: pass
                class _Offer: pass
                offer = _Offer()
                offer.id = str(p.get('_id'))
                offer.title = p.get('title', '')
                offer.description = p.get('description', '')
                offer.expires_at = p.get('expires_at')
                # residential_complex.name
                rc = _RC()
                rc.name = (complex_doc.get('development', {}) or {}).get('name') if complex_doc else ''
                rc.id = str(complex_doc.get('_id')) if complex_doc and complex_doc.get('_id') else ''
                offer.residential_complex = rc
                # get_main_image.image.url
                photos = []
                if complex_doc:
                    if 'development' in complex_doc and 'avito' not in complex_doc:
                        photos = complex_doc.get('development', {}).get('photos', []) or []
                    else:
                        photos = (complex_doc.get('domclick', {}) or {}).get('development', {}).get('photos', []) or []
                main = _MainImg()
                img = _Img()
                img.url = photos[0] if photos else PLACEHOLDER_IMAGE_URL
                main.image = img
                offer.get_main_image = main
                items.append(offer)
            return items
        except Exception:
            return get_special_offers_from_mongo()

    offers = build_offer_adapters()

    context = {
        'complexes': complexes,
        'company_info': company_info,
        'company_gallery': company_gallery,
        'home_articles': home_articles,
        'offers': offers,
        'PLACEHOLDER_IMAGE_URL': PLACEHOLDER_IMAGE_URL,
    }
    return render(request, 'main/home.html', context)


def privacy_policy(request):
    """Страница политики конфиденциальности"""
    return render(request, 'main/privacy.html')

