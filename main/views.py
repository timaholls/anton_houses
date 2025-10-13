from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.contrib import messages
from .models import ResidentialComplex, Article, Tag, CompanyInfo, CatalogLanding, SecondaryProperty, Category, \
    Employee, EmployeeReview, FutureComplex
from .models import Vacancy
from .models import BranchOffice
from .models import Gallery, MortgageProgram, SpecialOffer
from django.db import models
from pymongo import MongoClient
from bson import ObjectId
import os
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime


def home(request):
    """Главная страница"""
    # Получаем 9 популярных ЖК для главной страницы
    complexes = ResidentialComplex.objects.filter(is_featured=True).order_by('-created_at')[:6]

    # Если популярных ЖК меньше 9, добавляем обычные
    if complexes.count() < 6:
        remaining_count = 6 - complexes.count()
        additional_complexes = ResidentialComplex.objects.filter(is_featured=False).order_by('-created_at')[
                               :remaining_count]
        complexes = list(complexes) + list(additional_complexes)

    # Получаем информацию о компании
    company_info = CompanyInfo.get_active()
    # Галерея компании
    company_gallery = []
    if company_info:
        company_gallery = company_info.get_images()[:6]
    # Статьи для главной
    home_articles = Article.objects.filter(show_on_home=True).order_by('-published_date')[:3]

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
                img.url = ('/media/' + photos[0]) if photos else '/media/gallery/placeholders.png'
                main.image = img
                offer.get_main_image = main
                items.append(offer)
            return items
        except Exception:
            return list(SpecialOffer.get_active_offers())

    offers = build_offer_adapters()

    context = {
        'complexes': complexes,
        'company_info': company_info,
        'company_gallery': company_gallery,
        'home_articles': home_articles,
        'offers': offers,
    }
    return render(request, 'main/home.html', context)


def catalog(request):
    """Каталог ЖК"""
    page = request.GET.get('page', 1)

    # Получаем параметры фильтрации
    rooms = request.GET.get('rooms', '')
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')
    street = request.GET.get('street', '')
    area_from = request.GET.get('area_from', '')
    area_to = request.GET.get('area_to', '')
    price_from = request.GET.get('price_from', '')
    price_to = request.GET.get('price_to', '')
    delivery_date = request.GET.get('delivery_date', '')
    has_offers = request.GET.get('has_offers', '')
    sort = request.GET.get('sort', 'price_asc')

    # Базовый queryset
    complexes = ResidentialComplex.objects.all()

    # Применяем фильтры только если есть параметры поиска
    filters_applied = False
    if rooms or city or district or street or area_from or area_to or price_from or price_to or delivery_date or has_offers:
        filters_applied = True

        if rooms:
            complexes = complexes.filter(rooms=rooms)
        if city:
            complexes = complexes.filter(city=city)
        if district:
            complexes = complexes.filter(district=district)
        if street:
            complexes = complexes.filter(street=street)
        if area_from:
            try:
                complexes = complexes.filter(area_from__gte=float(area_from))
            except ValueError:
                pass
        if area_to:
            try:
                complexes = complexes.filter(area_to__lte=float(area_to))
            except ValueError:
                pass
        if price_from:
            try:
                complexes = complexes.filter(price_from__gte=float(price_from))
            except ValueError:
                pass
        if price_to:
            try:
                complexes = complexes.filter(price_from__lte=float(price_to))
            except ValueError:
                pass
        if delivery_date:
            complexes = complexes.filter(delivery_date__lte=delivery_date)
        if has_offers:
            complexes = complexes.filter(offers__is_active=True).distinct()

    # Применяем сортировку
    if sort == 'price_asc':
        complexes = complexes.order_by('price_from')
    elif sort == 'price_desc':
        complexes = complexes.order_by('-price_from')
    elif sort == 'area_desc':
        complexes = complexes.order_by('-area_to')
    elif sort == 'area_asc':
        complexes = complexes.order_by('area_from')

    # Пагинация по 9 элементов
    paginator = Paginator(complexes, 9)
    page_obj = paginator.get_page(page)

    # Получаем уникальные города для фильтра
    cities = ResidentialComplex.objects.values_list('city', flat=True).distinct()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': cities,
        'rooms_choices': ResidentialComplex.ROOMS_CHOICES,
        'filters': {
            'rooms': rooms,
            'city': city,
            'district': district,
            'street': street,
            'area_from': area_from,
            'area_to': area_to,
            'price_from': price_from,
            'price_to': price_to,
            'delivery_date': delivery_date,
            'has_offers': has_offers,
            'sort': sort,
        },
        'filters_applied': filters_applied,
        'dataset_type': 'newbuild'  # По умолчанию показываем новостройки
    }
    return render(request, 'main/catalog.html', context)


def catalog_api(request):
    """API для каталога ЖК из MongoDB unified_houses"""
    page = int(request.GET.get('page', 1))
    per_page = 9
    search = request.GET.get('search', '').strip()
    
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Формируем фильтр (поддержка обеих структур)
        filter_query = {}
        if search:
            filter_query['$or'] = [
                # Старая структура
                {'domrf.name': {'$regex': search, '$options': 'i'}},
                {'avito.development.name': {'$regex': search, '$options': 'i'}},
                {'domclick.development.complex_name': {'$regex': search, '$options': 'i'}},
                # Новая структура
                {'development.name': {'$regex': search, '$options': 'i'}}
            ]
        
        # Получаем общее количество
        total_count = unified_col.count_documents(filter_query)
        
        # Пагинация
        skip = (page - 1) * per_page
        records = list(unified_col.find(filter_query).skip(skip).limit(per_page))
        
        # Форматируем данные для каталога
        complexes_data = []
        for record in records:
            # Определяем структуру записи
            is_new_structure = 'development' in record and 'avito' not in record
            
            if is_new_structure:
                # === НОВАЯ УПРОЩЕННАЯ СТРУКТУРА ===
                development = record.get('development', {})
                
                name = development.get('name', 'Без названия')
                address_full = development.get('address', '')
                address = address_full.split('/')[0].strip() if address_full else ''
                price_range = development.get('price_range', 'Цена не указана')
                photos = development.get('photos', [])
                latitude = record.get('latitude')
                longitude = record.get('longitude')
                parameters = development.get('parameters', {})
                
            else:
                # === СТАРАЯ СТРУКТУРА ===
                avito_dev = record.get('avito', {}).get('development', {}) if record.get('avito') else {}
                domclick_dev = record.get('domclick', {}).get('development', {}) if record.get('domclick') else {}
                domrf_data = record.get('domrf', {})
                
                # Название (приоритет: avito -> domclick -> domrf)
                name = avito_dev.get('name') or domclick_dev.get('complex_name') or domrf_data.get('name', 'Без названия')
                
                # Адрес из avito - обрезаем до первого слеша
                address_full = avito_dev.get('address', '')
                address = address_full.split('/')[0].strip() if address_full else ''
                
                # Цена из avito
                price_range = avito_dev.get('price_range', 'Цена не указана')
                
                # Фото из domclick - берем ВСЕ фото
                photos = domclick_dev.get('photos', [])
                
                # Координаты из domrf
                latitude = domrf_data.get('latitude')
                longitude = domrf_data.get('longitude')
                
                # Параметры из avito
                parameters = avito_dev.get('parameters', {})

            complexes_data.append({
                'id': str(record['_id']),
                'name': name,
                'address': address,
                'price_range': price_range,
                'price_display': price_range,
                'photos': photos,  # Все фото для галереи
                'image_url': f"/media/{photos[0]}" if photos else None,
                'image_2_url': f"/media/{photos[1]}" if len(photos) > 1 else None,
                'image_3_url': f"/media/{photos[2]}" if len(photos) > 2 else None,
                'image_4_url': f"/media/{photos[3]}" if len(photos) > 3 else None,
                'lat': latitude,
                'lng': longitude,
                'latitude': latitude,
                'longitude': longitude,
                'parameters': parameters,
                'completion_date': parameters.get('Срок сдачи', ''),
                'housing_class': parameters.get('Класс жилья', ''),
                'housing_type': parameters.get('Тип жилья', ''),
                'avito_url': record.get('avito', {}).get('url', '') if record.get('avito') else '',
                'domclick_url': record.get('domclick', {}).get('url', '') if record.get('domclick') else '',
                'total_apartments': record.get('avito', {}).get('total_apartments', 0) if record.get('avito') else 0,
                'location': address,
                'city': 'Уфа',  # можно парсить из address
            })
        
        total_pages = (total_count + per_page - 1) // per_page

        return JsonResponse({
            'complexes': complexes_data,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        # Возвращаем пустой результат при ошибке
        return JsonResponse({
            'complexes': [],
            'has_previous': False,
            'has_next': False,
            'current_page': 1,
            'total_pages': 0,
            'total_count': 0,
            'error': str(e)
        })


def articles(request):
    """Страница статей"""
    category = request.GET.get('category', '')
    article_type = request.GET.get('type', 'news')  # По умолчанию показываем новости

    # Получаем статьи по типу
    articles_list = Article.objects.filter(article_type=article_type)

    # Дополнительная фильтрация по категории
    if category:
        try:
            category_obj = Category.objects.get(slug=category)
            articles_list = articles_list.filter(category=category_obj)
        except Category.DoesNotExist:
            articles_list = Article.objects.none()

    # Получаем статьи по категориям для отображения в секциях (только для текущего типа)
    try:
        mortgage_category = Category.objects.get(slug='mortgage')
        mortgage_articles = Article.objects.filter(article_type=article_type, category=mortgage_category,
                                                   is_featured=True)[:3]
    except Category.DoesNotExist:
        mortgage_articles = Article.objects.none()

    try:
        laws_category = Category.objects.get(slug='laws')
        laws_articles = Article.objects.filter(article_type=article_type, category=laws_category)[:3]
    except Category.DoesNotExist:
        laws_articles = Article.objects.none()

    try:
        instructions_category = Category.objects.get(slug='instructions')
        instructions_articles = Article.objects.filter(article_type=article_type, category=instructions_category)[:3]
    except Category.DoesNotExist:
        instructions_articles = Article.objects.none()

    try:
        market_category = Category.objects.get(slug='market')
        market_articles = Article.objects.filter(article_type=article_type, category=market_category)[:3]
    except Category.DoesNotExist:
        market_articles = Article.objects.none()

    try:
        tips_category = Category.objects.get(slug='tips')
        tips_articles = Article.objects.filter(article_type=article_type, category=tips_category)[:3]
    except Category.DoesNotExist:
        tips_articles = Article.objects.none()

    # Получаем все категории для фильтрации
    categories = Category.objects.filter(is_active=True)

    # Получаем популярные теги
    popular_tags = Tag.objects.all()[:10]

    # Получаем рекомендуемые статьи для блока "Похожие статьи"
    featured_articles = Article.objects.filter(is_featured=True).order_by('-views_count')[:3]

    context = {
        'articles': articles_list,
        'mortgage_articles': mortgage_articles,
        'laws_articles': laws_articles,
        'instructions_articles': instructions_articles,
        'market_articles': market_articles,
        'tips_articles': tips_articles,
        'categories': categories,
        'current_category': category,
        'current_type': article_type,
        'popular_tags': popular_tags,
        'featured_articles': featured_articles,
    }
    return render(request, 'main/articles.html', context)


def article_detail(request, slug):
    """Детальная страница статьи"""
    article = get_object_or_404(Article, slug=slug)

    # Увеличиваем счетчик просмотров
    article.views_count += 1
    article.save()

    # Обновляем статистику автора
    if article.author:
        article.author.articles_count = article.author.article_set.count()
        article.author.total_views = sum(article.author.article_set.values_list('views_count', flat=True))
        article.author.total_likes = sum(article.author.article_set.values_list('likes_count', flat=True))
        article.author.save()

    # Получаем похожие статьи (сначала из связанных, потом по категории)
    related_articles = article.related_articles.all()
    if not related_articles.exists():
        related_articles = Article.objects.filter(category=article.category).exclude(id=article.id)[:3]

    # Если все еще нет похожих статей, берем последние статьи
    if not related_articles.exists():
        related_articles = Article.objects.exclude(id=article.id).order_by('-published_date')[:3]

    # Получаем теги статьи
    article_tags = article.tags.all()

    # Получаем популярные теги
    popular_tags = Tag.objects.all()[:10]

    context = {
        'article': article,
        'related_articles': related_articles,
        'article_tags': article_tags,
        'popular_tags': popular_tags,
    }
    return render(request, 'main/article_detail_new.html', context)


def tag_detail(request, slug):
    """Страница тега"""
    tag = get_object_or_404(Tag, slug=slug)
    articles = tag.articles.all()

    context = {
        'tag': tag,
        'articles': articles,
    }
    return render(request, 'main/tag_detail.html', context)


def vacancies(request):
    """Список вакансий"""
    vacancies_qs = Vacancy.objects.filter(is_active=True)

    paginator = Paginator(vacancies_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'vacancies': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
    }
    return render(request, 'main/vacancies.html', context)


def vacancy_detail(request, slug):
    """Детальная страница вакансии"""
    vacancy = get_object_or_404(Vacancy, slug=slug, is_active=True)
    return render(request, 'main/vacancy_detail.html', {'vacancy': vacancy})


def offices(request):
    """Список офисов продаж"""
    city = request.GET.get('city', '')
    offices_qs = BranchOffice.objects.filter(is_active=True)
    if city:
        offices_qs = offices_qs.filter(city__iexact=city)

    paginator = Paginator(offices_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    cities = BranchOffice.objects.values_list('city', flat=True).distinct()

    context = {
        'offices': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': cities,
        'filters': {
            'city': city,
        }
    }
    return render(request, 'main/offices.html', context)


def office_detail(request, slug):
    """Детальная страница офиса с сотрудниками"""
    office = get_object_or_404(BranchOffice, slug=slug, is_active=True)
    employees = office.employees.filter(is_active=True).order_by('full_name')

    context = {
        'office': office,
        'employees': employees
    }
    return render(request, 'main/office_detail.html', context)


def videos(request):
    """Видеообзоры из Mongo `residential_videos`"""
    category = request.GET.get('category', '')
    complex_id = request.GET.get('complex', '')
    db = get_mongo_connection()
    videos_col = db['residential_videos']
    unified = db['unified_houses']

    q = {'is_active': True}
    if complex_id:
        try:
            q['complex_id'] = ObjectId(str(complex_id))
        except Exception:
            q['complex_id'] = None

    docs = list(videos_col.find(q).sort('created_at', -1))

    adapted = []
    for d in docs:
        comp_name = ''
        try:
            comp = unified.find_one({'_id': d.get('complex_id')}) if isinstance(d.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(d.get('complex_id')))})
            if comp:
                if 'development' in comp and 'avito' not in comp:
                    comp_name = (comp.get('development', {}) or {}).get('name', '')
                else:
                    comp_name = (comp.get('avito', {}) or {}).get('development', {}) .get('name') or (comp.get('domclick', {}) or {}).get('development', {}) .get('complex_name', '')
        except Exception:
            comp_name = ''
        adapted.append(type('V', (), {
            'id': str(d.get('_id')),
            'title': d.get('title', ''),
            'video_url': d.get('url', ''),
            'residential_complex_name': comp_name,
            'created_at': d.get('created_at') or datetime.utcnow()
        }))

    page = int(request.GET.get('page', 1))
    per_page = 12
    total = len(adapted)
    start = (page - 1) * per_page
    end = start + per_page
    page_slice = adapted[start:end]

    paginator = Paginator(range(total), per_page)
    page_obj = paginator.get_page(page)

    categories = [
        {'value': 'newbuild', 'name': 'Новостройки'},
        {'value': 'secondary', 'name': 'Вторичная недвижимость'},
    ]

    return render(request, 'main/videos.html', {
        'videos': page_slice,
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
        'filters': {'category': category, 'complex': complex_id},
        'no_videos_for_complex': bool(complex_id and total == 0)
    })


def video_detail(request, video_id):
    """Детальная страница видеообзора (Mongo)"""
    db = get_mongo_connection()
    videos_col = db['residential_videos']
    unified = db['unified_houses']
    d = videos_col.find_one({'_id': ObjectId(str(video_id))})
    if not d:
        raise Http404("Видео не найдено")

    # Формируем embed URL
    video_embed_url = None
    url = (d.get('url') or '').strip()
    if url:

        # Проверяем, является ли это iframe кодом
        if url.startswith('<iframe'):
            # Извлекаем src из iframe
            import re
            src_match = re.search(r'src=["\']([^"\']+)["\']', url)
            if src_match:
                video_embed_url = src_match.group(1)
            else:
                video_embed_url = url
        # YouTube обработка
        elif 'youtu.be/' in url:
            vid = url.split('youtu.be/')[-1].split('?')[0]
            video_embed_url = f'https://www.youtube.com/embed/{vid}'
        elif 'watch?v=' in url:
            vid = url.split('watch?v=')[-1].split('&')[0]
            video_embed_url = f'https://www.youtube.com/embed/{vid}'
        # Rutube обработка
        elif 'rutube.ru' in url:
            # Если это уже embed URL
            if '/play/embed/' in url:
                video_embed_url = url
            else:
                # Если это обычная ссылка, пытаемся извлечь ID
                import re
                rutube_match = re.search(r'rutube\.ru/video/([a-f0-9]+)', url)
                if rutube_match:
                    rvid = rutube_match.group(1)
                    video_embed_url = f'https://rutube.ru/play/embed/{rvid}/'
                else:
                    video_embed_url = url
        else:
            video_embed_url = url

    # ЖК имя и другие видео этого же ЖК
    comp_name = ''
    same_complex_videos = []
    if d.get('complex_id'):
        comp = unified.find_one({'_id': d.get('complex_id')}) if isinstance(d.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(d.get('complex_id')))})
        if comp:
            if 'development' in comp and 'avito' not in comp:
                comp_name = (comp.get('development', {}) or {}).get('name', '')
            else:
                comp_name = (comp.get('avito', {}) or {}).get('development', {}) .get('name') or (comp.get('domclick', {}) or {}).get('development', {}) .get('complex_name', '')
        for sd in videos_col.find({'complex_id': d.get('complex_id'), '_id': {'$ne': d['_id']}, 'is_active': True}).limit(5):
            same_complex_videos.append(type('V', (), {'id': str(sd.get('_id')), 'title': sd.get('title','')}))

    # Похожие видео (из других объектов того же города)
    if video.category == 'residential_video':
        complex_ids = ResidentialComplex.objects.filter(city=residential_complex.city).exclude(
            id=video.object_id).values_list('id', flat=True)
    else:
        complex_ids = SecondaryProperty.objects.filter(city=residential_complex.city).exclude(
            id=video.object_id).values_list('id', flat=True)

    similar_videos = []

    video_obj = type('V', (), {
        'id': str(d.get('_id')),
        'title': d.get('title',''),
        'description': d.get('description',''),
        'residential_complex_name': comp_name
    })

    context = {
        'video': video_obj,
        'video_embed_url': video_embed_url,
        'residential_complex': None,
        'same_complex_videos': same_complex_videos,
        'similar_videos': similar_videos,
        'object_type': 'ЖК',
    }
    return render(request, 'main/video_detail.html', context)


# Быстрые ссылки каталога
def catalog_completed(request):
    """Сданные ЖК"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(status='completed')

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': ResidentialComplex.objects.values_list('name', flat=True).distinct(),
        'house_types': ResidentialComplex.HOUSE_TYPE_CHOICES,
        'filters': {},
        'filters_applied': True,
        'page_title': 'Сданные ЖК',
        'page_description': 'Готовые к заселению жилые комплексы'
    }
    return render(request, 'main/catalog.html', context)


def catalog_construction(request):
    """Строящиеся ЖК"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(status='construction')

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': ResidentialComplex.objects.values_list('name', flat=True).distinct(),
        'house_types': ResidentialComplex.HOUSE_TYPE_CHOICES,
        'filters': {},
        'filters_applied': True,
        'page_title': 'Строящиеся ЖК',
        'page_description': 'Жилые комплексы в стадии строительства'
    }
    return render(request, 'main/catalog.html', context)


def catalog_economy(request):
    """Эконом-класс"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(house_class='economy')

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': ResidentialComplex.objects.values_list('name', flat=True).distinct(),
        'house_types': ResidentialComplex.HOUSE_TYPE_CHOICES,
        'filters': {},
        'filters_applied': True,
        'page_title': 'Эконом-класс',
        'page_description': 'Доступное жилье эконом-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_comfort(request):
    """Комфорт-класс"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(house_class='comfort')

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': ResidentialComplex.objects.values_list('name', flat=True).distinct(),
        'house_types': ResidentialComplex.HOUSE_TYPE_CHOICES,
        'filters': {},
        'filters_applied': True,
        'page_title': 'Комфорт-класс',
        'page_description': 'Жилые комплексы комфорт-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_premium(request):
    """Премиум-класс"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(house_class='premium')

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': ResidentialComplex.objects.values_list('name', flat=True).distinct(),
        'house_types': ResidentialComplex.HOUSE_TYPE_CHOICES,
        'filters': {},
        'filters_applied': True,
        'page_title': 'Премиум-класс',
        'page_description': 'Жилые комплексы премиум-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_finished(request):
    """С отделкой"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(finishing='finished')

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': ResidentialComplex.objects.values_list('name', flat=True).distinct(),
        'house_types': ResidentialComplex.HOUSE_TYPE_CHOICES,
        'filters': {},
        'filters_applied': True,
        'page_title': 'С отделкой',
        'page_description': 'Квартиры с готовой отделкой'
    }
    return render(request, 'main/catalog.html', context)


def catalog_unfinished(request):
    """Без отделки"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(finishing='unfinished')

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': ResidentialComplex.objects.values_list('name', flat=True).distinct(),
        'house_types': ResidentialComplex.HOUSE_TYPE_CHOICES,
        'filters': {},
        'filters_applied': True,
        'page_title': 'Без отделки',
        'page_description': 'Квартиры без отделки'
    }
    return render(request, 'main/catalog.html', context)


def detail(request, complex_id):
    """Детальная страница ЖК (MongoDB или SQL)"""
    
    # Получаем ипотечные программы (нужны для обоих версий)
    mortgage_programs = list(MortgageProgram.objects.filter(is_active=True))
    if not mortgage_programs:
        class P:
            def __init__(self, name, rate):
                self.name, self.rate = name, rate
        mortgage_programs = [
            P('Базовая', 18.0),
            P('IT-ипотека', 6.0),
            P('Семейная', 6.0),
        ]
    
    # Проверяем, является ли ID MongoDB ObjectId (24 hex символа)
    is_mongodb_id = len(str(complex_id)) == 24 and all(c in '0123456789abcdef' for c in str(complex_id).lower())
    
    if is_mongodb_id:
        # ============ MONGODB VERSION ============
        try:
            db = get_mongo_connection()
            unified_col = db['unified_houses']
            
            # Получаем запись по ID
            record = unified_col.find_one({'_id': ObjectId(complex_id)})
            
            if not record:
                raise Http404("ЖК не найден")
            
            # Проверяем структуру: старая (с вложенностью) или новая (упрощенная)
            is_new_structure = 'development' in record and 'avito' not in record
            
            # Инициализируем переменные для обеих структур
            avito_data = {}
            domclick_data = {}
            
            if is_new_structure:
                # === НОВАЯ УПРОЩЕННАЯ СТРУКТУРА ===
                development = record.get('development', {})
                
                # Основные данные
                name = development.get('name', 'Без названия')
                address = development.get('address', '').split('/')[0].strip()
                price_range = development.get('price_range', '')
                
                # Фото ЖК
                photos = development.get('photos', [])
                
                # Координаты напрямую в корне
                latitude = record.get('latitude')
                longitude = record.get('longitude')
                
                # Параметры ЖК
                parameters = development.get('parameters', {})
                korpuses = development.get('korpuses', [])
                
                # Типы квартир уже в упрощенной структуре
                apartment_types_data = record.get('apartment_types', {})
                
            else:
                # === СТАРАЯ СТРУКТУРА (для обратной совместимости) ===
                avito_data = record.get('avito', {})
                domclick_data = record.get('domclick', {})
                domrf_data = record.get('domrf', {})
                
                avito_dev = avito_data.get('development', {}) if avito_data else {}
                domclick_dev = domclick_data.get('development', {}) if domclick_data else {}
                
                # Основные данные
                name = avito_dev.get('name') or domclick_dev.get('complex_name') or domrf_data.get('name', 'Без названия')
                address = avito_dev.get('address', '').split('/')[0].strip() if avito_dev.get('address') else ''
                price_range = avito_dev.get('price_range', '')
                
                # Фото ЖК из domclick
                photos = domclick_dev.get('photos', [])
                
                # Координаты
                latitude = domrf_data.get('latitude')
                longitude = domrf_data.get('longitude')
                
                # Параметры ЖК
                parameters = avito_dev.get('parameters', {})
                korpuses = avito_dev.get('korpuses', [])
            
            # Обработка типов квартир в зависимости от структуры
            apartment_variants = []
            apartment_types_list = []
            
            if is_new_structure:
                # === НОВАЯ СТРУКТУРА: данные уже объединены ===
                for apt_type, apt_data in apartment_types_data.items():
                    apartments = apt_data.get('apartments', [])
                    
                    if apartments:
                        apartment_types_list.append(apt_type)
                        
                        for apt in apartments:
                            # Получаем все фото планировки - это уже массив!
                            layout_photos = apt.get('image', [])
                            # Если это не массив, а строка - преобразуем в массив
                            if isinstance(layout_photos, str):
                                layout_photos = [layout_photos] if layout_photos else []
                            
                            apartment_variants.append({
                                'type': apt_type,
                                'title': apt.get('title', ''),
                                'price': apt.get('price', ''),
                                'price_per_square': apt.get('pricePerSquare', ''),
                                'completion_date': apt.get('completionDate', ''),
                                'image': layout_photos[0] if layout_photos else '',  # Первое фото для превью
                                'url': apt.get('url', ''),
                                'layout_photos': layout_photos  # Все фото для галереи
                            })
            
            else:
                # === СТАРАЯ СТРУКТУРА: нужно объединять данные ===
                avito_apartment_types = avito_data.get('apartment_types', {})
                domclick_apartment_types = domclick_data.get('apartment_types', {})
                
                for apt_type, apt_data in avito_apartment_types.items():
                    apartments = apt_data.get('apartments', [])
                    
                    # Добавляем тип в список если есть квартиры
                    if apartments and apt_type not in apartment_types_list:
                        apartment_types_list.append(apt_type)
                    
                    # Ищем фото планировок из domclick для этого типа
                    domclick_photos = []
                    if apt_type in domclick_apartment_types:
                        dc_apartments = domclick_apartment_types[apt_type].get('apartments', [])
                        for dc_apt in dc_apartments:
                            domclick_photos.extend(dc_apt.get('photos', []))
                    
                    for apt in apartments:
                        apartment_variants.append({
                            'type': apt_type,
                            'title': apt.get('title', ''),
                            'price': apt.get('price', ''),
                            'price_per_square': apt.get('pricePerSquare', ''),
                            'completion_date': apt.get('completionDate', ''),
                            'image': apt.get('image', {}).get('128x96', ''),
                            'url': apt.get('urlPath', ''),
                            'layout_photos': domclick_photos[:5]  # Первые 5 фото планировок
                        })
            
            # Формируем контекст для MongoDB версии
            import json
            context = {
                'complex': {
                    'id': str(record['_id']),
                    'name': name,
                    'address': address,
                    'city': 'Уфа',
                    'price_range': price_range,
                    'photos': photos,
                    'photos_json': json.dumps(photos),
                    'latitude': latitude,
                    'longitude': longitude,
                    'parameters': parameters,
                    'korpuses': korpuses,
                    'apartment_variants': apartment_variants,
                    'apartment_variants_json': json.dumps(apartment_variants),
                    'apartment_types': apartment_types_list,
                    'total_apartments': avito_data.get('total_apartments', 0),
                    'avito_url': avito_data.get('url', ''),
                    'domclick_url': domclick_data.get('url', ''),
                },
                'mortgage_programs': mortgage_programs,
                'is_mongodb': True,
                'is_secondary': False,
            }
            
            return render(request, 'main/detail.html', context)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Http404(f"Ошибка загрузки ЖК: {str(e)}")
    
    else:
        # ============ SQL VERSION (старая логика) ============
    complex = get_object_or_404(ResidentialComplex, id=complex_id)

    # Проверяем, пришли ли мы от агента
    agent_id = request.GET.get('agent_id')
    agent = None
    agent_other_properties = []

    if agent_id:
        try:
            agent = Employee.objects.get(id=agent_id, is_active=True)
            # Получаем другие объекты этого агента (исключая текущий ЖК)
            agent_residential = agent.residential_complexes.exclude(id=complex_id)[:3]
            agent_secondary = agent.secondary_properties.all()[:3]

            # Объединяем объекты агента
            for complex_obj in agent_residential:
                agent_other_properties.append({
                    'type': 'residential',
                    'object': complex_obj,
                    'name': complex_obj.name,
                    'price': complex_obj.price_from,
                    'location': f"{complex_obj.district or complex_obj.city}",
                    'image': complex_obj.get_main_image(),
                    'url': f"/complex/{complex_obj.id}/",
                })

            for property_obj in agent_secondary:
                agent_other_properties.append({
                    'type': 'secondary',
                    'object': property_obj,
                    'name': property_obj.name,
                    'price': property_obj.price,
                    'location': f"{property_obj.district or property_obj.city}",
                    'image': property_obj.get_main_image(),
                    'url': f"/secondary/{property_obj.id}/",
                })
        except Employee.DoesNotExist:
            pass

    # Получаем общие похожие ЖК (если нет других объектов агента или их мало)
    similar_complexes = ResidentialComplex.objects.filter(
        city=complex.city,
        house_class=complex.house_class
    ).exclude(id=complex.id)

    # Если есть объекты агента, ограничиваем количество общих похожих
    if agent_other_properties:
        remaining_slots = max(0, 6 - len(agent_other_properties))
        similar_complexes = similar_complexes[:remaining_slots]
    else:
        similar_complexes = similar_complexes[:3]

    # Получаем акции для данного ЖК
    from django.utils import timezone
    complex_offers = SpecialOffer.objects.filter(
        residential_complex=complex,
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).order_by('-priority', '-created_at')

    # Первое активное видеообзор этого ЖК
    video = complex.get_main_video()
    video_embed_url = None
    if video and video.video_url:
        url = video.video_url
        if 'youtu.be/' in url:
            vid = url.split('youtu.be/')[-1].split('?')[0]
            video_embed_url = f'https://www.youtube.com/embed/{vid}'
        elif 'watch?v=' in url:
            vid = url.split('watch?v=')[-1].split('&')[0]
            video_embed_url = f'https://www.youtube.com/embed/{vid}'
        else:
            video_embed_url = url

    context = {
        'complex': complex,
        'similar_complexes': similar_complexes,
        'complex_offers': complex_offers,
        'video': video,
        'video_embed_url': video_embed_url,
        'videos': getattr(complex, 'get_videos', lambda: [])() if hasattr(complex, 'get_videos') else [],
        'mortgage_programs': mortgage_programs,
        'agent': agent,
        'agent_other_properties': agent_other_properties,
        'is_secondary': False,
    }
    return render(request, 'main/detail.html', context)


def secondary_detail(request, pk: int):
    obj = get_object_or_404(SecondaryProperty, pk=pk)

    # Используем существующий шаблон detail.html с минимальным контекстом-адаптером
    class Adapter:
        pass

    complex = Adapter()
    complex.name = obj.name

    complex.price_from = obj.price
    complex.city = obj.city
    complex.district = obj.district
    complex.street = obj.street
    complex.commute_time = obj.commute_time
    complex.area_from = obj.area
    complex.area_to = obj.area
    complex.developer = 'Собственник'
    complex.total_apartments = 1
    complex.completion_start = ''
    complex.completion_end = ''
    complex.has_completed = True
    complex.get_house_class_display = ''
    complex.get_house_type_display = obj.get_house_type_display if hasattr(obj,
                                                                           'get_house_type_display') else lambda: ''
    complex.get_finishing_display = lambda: ''

    return render(request, 'main/detail.html', {
        'complex': complex,
        'similar_complexes': [],
        'is_secondary': True,
        'mortgage_programs': [],
        'videos': obj.get_videos(),
    })


def secondary_api(request):
    """API для вторичной недвижимости (AJAX)"""
    page = int(request.GET.get('page', 1))
    stype = request.GET.get('stype', '')
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')
    street = request.GET.get('street', '')
    area_from = request.GET.get('area_from', '')
    area_to = request.GET.get('area_to', '')
    price_from = request.GET.get('price_from', '')
    price_to = request.GET.get('price_to', '')

    qs = SecondaryProperty.objects.all()
    if stype:
        qs = qs.filter(house_type=stype)
    if city:
        qs = qs.filter(city=city)
    if district:
        qs = qs.filter(district=district)
    if street:
        qs = qs.filter(street=street)
    if area_from:
        try:
            qs = qs.filter(area__gte=float(area_from))
        except ValueError:
            pass
    if area_to:
        try:
            qs = qs.filter(area__lte=float(area_to))
        except ValueError:
            pass
    if price_from:
        try:
            qs = qs.filter(price__gte=float(price_from))
        except ValueError:
            pass
    if price_to:
        try:
            qs = qs.filter(price__lte=float(price_to))
        except ValueError:
            pass

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(page)

    items = []
    for obj in page_obj:
        # Получаем изображения для каталога
        catalog_images = obj.get_catalog_images()

        # Подготавливаем отдельные URL для каждого изображения
        image_url = None
        image_2_url = None
        image_3_url = None
        image_4_url = None

        if catalog_images:
            # Главное изображение
            if len(catalog_images) > 0 and catalog_images[0].image:
                image_url = catalog_images[0].image.url

            # Дополнительные изображения
            if len(catalog_images) > 1 and catalog_images[1].image:
                image_2_url = catalog_images[1].image.url
            if len(catalog_images) > 2 and catalog_images[2].image:
                image_3_url = catalog_images[2].image.url
            if len(catalog_images) > 3 and catalog_images[3].image:
                image_4_url = catalog_images[3].image.url

        items.append({
            'id': obj.id if obj.id else 0,
            'name': obj.name,
            'price_from': float(obj.price),
            'city': obj.city,
            'district': obj.district,
            'street': obj.street,
            'image_url': image_url,
            'image_2_url': image_2_url,
            'image_3_url': image_3_url,
            'image_4_url': image_4_url,
            'lat': obj.latitude,
            'lng': obj.longitude,
        })

    return JsonResponse({
        'items': items,
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
    })


def districts_api(request):
    """API для получения районов по городу"""
    city = request.GET.get('city', '')
    if city:
        districts = ResidentialComplex.objects.filter(city=city).values_list('district', flat=True).distinct()
        districts = [district for district in districts if district]  # Убираем пустые значения
    else:
        districts = []

    return JsonResponse({'districts': list(districts)})


def streets_api(request):
    """API для получения улиц по городу"""
    city = request.GET.get('city', '')

    if city:
        streets = ResidentialComplex.objects.filter(city=city).values_list('street', flat=True).distinct()
        streets = [street for street in streets if street]  # Убираем пустые значения
    else:
        streets = []

    return JsonResponse({'streets': list(streets)})


def article_view_api(request, article_id):
    """API для увеличения счетчика просмотров статьи"""
    if request.method == 'POST':
        try:
            article = Article.objects.get(id=article_id)
            article.views_count += 1
            article.save()
            return JsonResponse({'success': True, 'views_count': article.views_count})
        except Article.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Статья не найдена'}, status=404)
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)


def privacy_policy(request):
    """Страница политики конфиденциальности"""
    return render(request, 'main/privacy.html')


def catalog_landing(request, slug):
    landing = get_object_or_404(CatalogLanding, slug=slug)

    # Базовый queryset в зависимости от типа
    if landing.kind == 'secondary':
        queryset = SecondaryProperty.objects.all()
    else:
        queryset = ResidentialComplex.objects.filter(status='construction')

    # Категории
    category_map = {
        'apartment': 'apartment',
        'house': 'house',
        'cottage': 'cottage',
        'townhouse': 'townhouse',
        'commercial': None,  # коммерция отсутствует — оставляем как есть
        'all': None,
    }
    house_type = category_map.get(landing.category)
    if house_type:
        if landing.kind == 'secondary':
            queryset = queryset.filter(house_type=house_type)
        else:
            queryset = queryset.filter(house_type=house_type)

    paginator = Paginator(queryset, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    categories = CatalogLanding.objects.filter(kind=landing.kind).order_by('name')

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': ResidentialComplex.objects.values_list('city', flat=True).distinct(),
        'rooms_choices': ResidentialComplex.ROOMS_CHOICES,
        'filters': {},
        'filters_applied': True,
        'page_title': landing.name,
        'page_description': landing.meta_description or landing.name,
        'landing': landing,
        'landing_categories': categories,
        'dataset_type': 'secondary' if landing.kind == 'secondary' else 'newbuild',
    }

    return render(request, 'main/catalog.html', context)


def _catalog_fallback(request, kind: str, title: str):
    """Рендер каталога без необходимости иметь запись CatalogLanding.
    kind: 'newbuild'|'secondary'
    """
    if kind == 'secondary':
        # Для вторички читаем из собственной таблицы
        queryset = SecondaryProperty.objects.all()
        stype = request.GET.get('stype', '')
        if stype in ['apartment', 'cottage', 'townhouse', 'commercial']:
            queryset = queryset.filter(house_type=stype)
    else:
        queryset = ResidentialComplex.objects.filter(status='construction')

    paginator = Paginator(queryset, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': ResidentialComplex.objects.values_list('city', flat=True).distinct(),
        'rooms_choices': ResidentialComplex.ROOMS_CHOICES,
        'filters': ({'stype': request.GET.get('stype', '')} if kind == 'secondary' else {}),
        'filters_applied': True,
        'page_title': title,
        'page_description': title,
        'landing': None,
        'landing_categories': CatalogLanding.objects.filter(kind=kind).order_by('name'),
        'dataset_type': kind,
    }
    return render(request, 'main/catalog.html', context)


def newbuild_index(request):
    # Стартовая страница новостроек
    landing = CatalogLanding.objects.filter(kind='newbuild', category='all').first()
    if landing:
        return catalog_landing(request, slug=landing.slug)
    return _catalog_fallback(request, kind='newbuild', title='Новостройки')


def secondary_index(request):
    # Стартовая страница вторички
    landing = CatalogLanding.objects.filter(kind='secondary', category='all').first()
    if landing:
        return catalog_landing(request, slug=landing.slug)
    return _catalog_fallback(request, kind='secondary', title='Вторичная недвижимость')


def team(request):
    """Страница команды"""
    employees = Employee.objects.filter(is_active=True).order_by('-is_featured', 'full_name')

    context = {
        'employees': employees,
    }
    return render(request, 'main/team.html', context)


def agent_properties(request, employee_id):
    """Страница объектов агента"""
    employee = get_object_or_404(Employee, id=employee_id, is_active=True)

    # Получаем параметры фильтрации и сортировки
    property_type = request.GET.get('property_type', '')
    sort_by = request.GET.get('sort_by', 'date-desc')

    # Получаем все объекты агента (новостройки и вторичная недвижимость)
    residential_complexes = ResidentialComplex.objects.filter(agent=employee)
    secondary_properties = SecondaryProperty.objects.filter(agent=employee)

    # Фильтрация по типу недвижимости
    if property_type == 'residential':
        secondary_properties = SecondaryProperty.objects.none()
    elif property_type == 'secondary':
        residential_complexes = ResidentialComplex.objects.none()

    # Объединяем все объекты
    all_properties = []

    # Добавляем новостройки
    for complex in residential_complexes:
        all_properties.append({
            'type': 'residential',
            'object': complex,
            'name': complex.name,
            'price': complex.price_from,
            'location': f"{complex.district or complex.city}",
            'image': complex.get_main_image(),
            'url': f"/complex/{complex.id}/",
            'created_at': complex.created_at,
        })

    # Добавляем вторичную недвижимость
    for property in secondary_properties:
        all_properties.append({
            'type': 'secondary',
            'object': property,
            'name': property.name,
            'price': property.price,
            'location': f"{property.district or property.city}",
            'image': property.get_main_image(),
            'url': f"/secondary/{property.id}/",
            'created_at': property.created_at,
        })

    # Применяем сортировку
    if sort_by == 'date-desc':
        all_properties.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == 'date-asc':
        all_properties.sort(key=lambda x: x['created_at'])
    elif sort_by == 'price-asc':
        all_properties.sort(key=lambda x: float(x['price']))
    elif sort_by == 'price-desc':
        all_properties.sort(key=lambda x: float(x['price']), reverse=True)
    elif sort_by == 'name-asc':
        all_properties.sort(key=lambda x: x['name'].lower())

    # Пагинация по 9 элементов
    paginator = Paginator(all_properties, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'employee': employee,
        'properties': page_obj,
        'page_obj': page_obj,
        'total_count': len(all_properties),
        'residential_count': ResidentialComplex.objects.filter(agent=employee).count(),
        'secondary_count': SecondaryProperty.objects.filter(agent=employee).count(),
        'current_property_type': property_type,
        'current_sort': sort_by,
    }
    return render(request, 'main/agent_properties.html', context)


def future_complexes(request):
    """Страница будущих ЖК"""
    # Получаем параметры фильтрации
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')
    price_from = request.GET.get('price_from', '')
    price_to = request.GET.get('price_to', '')
    delivery_date = request.GET.get('delivery_date', '')
    sort = request.GET.get('sort', 'delivery_date_asc')

    # Базовый queryset
    complexes = FutureComplex.objects.filter(is_active=True)

    # Применяем фильтры
    if city:
        complexes = complexes.filter(city__icontains=city)
    if district:
        complexes = complexes.filter(district__icontains=district)
    if price_from:
        try:
            complexes = complexes.filter(price_from__gte=float(price_from))
        except ValueError:
            pass
    if price_to:
        try:
            complexes = complexes.filter(price_from__lte=float(price_to))
        except ValueError:
            pass
    if delivery_date:
        complexes = complexes.filter(delivery_date__lte=delivery_date)

    # Применяем сортировку
    if sort == 'delivery_date_asc':
        complexes = complexes.order_by('delivery_date')
    elif sort == 'delivery_date_desc':
        complexes = complexes.order_by('-delivery_date')
    elif sort == 'price_asc':
        complexes = complexes.order_by('price_from')
    elif sort == 'price_desc':
        complexes = complexes.order_by('-price_from')
    elif sort == 'name_asc':
        complexes = complexes.order_by('name')
    else:
        complexes = complexes.order_by('-is_featured', 'delivery_date')

    # Пагинация
    paginator = Paginator(complexes, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'filters': {
            'city': city,
            'district': district,
            'price_from': price_from,
            'price_to': price_to,
            'delivery_date': delivery_date,
            'sort': sort,
        }
    }
    return render(request, 'main/future_complexes.html', context)


def future_complex_detail(request, complex_id):
    """Детальная страница будущего ЖК"""
    try:
        complex = FutureComplex.objects.get(id=complex_id, is_active=True)
    except FutureComplex.DoesNotExist:
        raise Http404("ЖК не найден")

    # Получаем изображения ЖК
    images = complex.get_images()

    # Получаем другие будущие ЖК для блока "Другие проекты"
    other_complexes = FutureComplex.objects.filter(
        is_active=True
    ).exclude(id=complex_id).order_by('?')[:6]

    context = {
        'complex': complex,
        'images': images,
        'other_complexes': other_complexes,
    }
    return render(request, 'main/future_complex_detail.html', context)


def employee_detail(request, employee_id):
    """Детальная страница сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id, is_active=True)

    # Получаем объекты недвижимости агента (по 2 новостройки и 2 вторички = 4 всего)
    residential_complexes = employee.residential_complexes.all()[:2]
    secondary_properties = employee.secondary_properties.all()[:2]

    # Считаем общее количество объектов
    total_properties_count = employee.residential_complexes.count() + employee.secondary_properties.count()

    # Получаем опубликованные отзывы
    reviews = employee.reviews.filter(is_approved=True, is_published=True).order_by('-created_at')[:10]

    # Обработка формы отзыва
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        rating = request.POST.get('rating', 5)
        text = request.POST.get('text', '').strip()

        if name and text and rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    EmployeeReview.objects.create(
                        employee=employee,
                        name=name,
                        email=email,
                        phone=phone,
                        rating=rating,
                        text=text
                    )
                    messages.success(request, 'Спасибо! Ваш отзыв отправлен на модерацию.')
                    return redirect('main:employee_detail', employee_id=employee.id)
            except ValueError:
                pass

        messages.error(request, 'Пожалуйста, заполните все обязательные поля корректно.')

    context = {
        'employee': employee,
        'residential_complexes': residential_complexes,
        'secondary_properties': secondary_properties,
        'reviews': reviews,
        'total_properties_count': total_properties_count,
    }
    return render(request, 'main/employee_detail.html', context)


def mortgage(request):
    """Страница ипотеки с калькулятором"""
    # Получаем ипотечные программы для калькулятора
    mortgage_programs = MortgageProgram.objects.filter(is_active=True).order_by('rate')

    # Если нет программ, создаем базовую
    if not mortgage_programs.exists():
        mortgage_programs = [
            type('MortgageProgram', (), {
                'name': 'Базовая',
                'rate': 11.4
            })()
        ]

    context = {
        'mortgage_programs': mortgage_programs,
    }
    return render(request, 'main/mortgage.html', context)


def all_offers(request):
    """Страница всех акций (Mongo promotions; fallback SQL)."""
    def build_all_offers():
        try:
            db = get_mongo_connection()
            promotions = db['promotions']
            unified = db['unified_houses']
            q = {'is_active': True}
            adapters = []
            for p in promotions.find(q).sort('created_at', -1):
                class _Img: pass
                class _MainImg: pass
                class _RC: pass
                class _Offer: pass
                offer = _Offer()
                offer.id = str(p.get('_id'))
                offer.title = p.get('title', '')
                offer.description = p.get('description', '')
                offer.expires_at = p.get('expires_at')
                rc = _RC()
                comp = unified.find_one({'_id': p.get('complex_id')}) if isinstance(p.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(p.get('complex_id')))})
                rc.name = (comp.get('development', {}) or {}).get('name') if comp else ''
                rc.id = str(comp.get('_id')) if comp and comp.get('_id') else ''
                offer.residential_complex = rc
                photos = []
                if comp:
                    if 'development' in comp and 'avito' not in comp:
                        photos = comp.get('development', {}).get('photos', []) or []
                    else:
                        photos = (comp.get('domclick', {}) or {}).get('development', {}).get('photos', []) or []
                m = _MainImg(); i = _Img(); i.url = ('/media/' + photos[0]) if photos else '/media/gallery/placeholders.png'; m.image = i
                offer.get_main_image = m
                adapters.append(offer)
            return adapters
        except Exception:
            from django.utils import timezone
            return list(SpecialOffer.objects.filter(is_active=True).filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())).select_related('residential_complex').order_by('?'))

    offers = build_all_offers()

    context = {
        'offers': offers,
    }
    return render(request, 'main/all_offers.html', context)


def offer_detail(request, offer_id):
    """Детальная страница акции (Mongo promotions со спадением на SQL)."""
    def build_offer_and_others(offer_id_str):
        try:
            db = get_mongo_connection()
            promotions = db['promotions']
            unified = db['unified_houses']
            p = promotions.find_one({'_id': ObjectId(str(offer_id_str))})
            if not p:
                raise Exception('not found')
            class _Img: pass
            class _MainImg: pass
            class _RC: pass
            class _Offer: pass
            def adapt(doc):
                comp = unified.find_one({'_id': doc.get('complex_id')}) if isinstance(doc.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(doc.get('complex_id')))})
                offer = _Offer()
                offer.id = str(doc.get('_id'))
                offer.title = doc.get('title', '')
                offer.description = doc.get('description', '')
                offer.expires_at = doc.get('expires_at')
                rc = _RC(); rc.name = (comp.get('development', {}) or {}).get('name') if comp else ''
                rc.id = str(comp.get('_id')) if comp and comp.get('_id') else ''
                offer.residential_complex = rc
                photos = []
                if comp:
                    if 'development' in comp and 'avito' not in comp:
                        photos = comp.get('development', {}).get('photos', []) or []
                    else:
                        photos = (comp.get('domclick', {}) or {}).get('development', {}).get('photos', []) or []
                m=_MainImg(); i=_Img(); i.url = ('/media/' + photos[0]) if photos else '/media/gallery/placeholders.png'; m.image=i
                offer.get_main_image = m
                return offer
            offer = adapt(p)
            others = [adapt(doc) for doc in promotions.find({'_id': {'$ne': p['_id']}, 'is_active': True}).sort('created_at', -1).limit(8)]
            return offer, others
        except Exception:
            from django.utils import timezone
            offer = get_object_or_404(SpecialOffer, id=int(offer_id_str), is_active=True)
            other_offers = SpecialOffer.objects.filter(is_active=True).filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())).exclude(id=offer.id).select_related('residential_complex').order_by('?')[:8]
            return offer, list(other_offers)

    offer, other_offers = build_offer_and_others(offer_id)
    return render(request, 'main/offer_detail.html', {'offer': offer, 'other_offers': other_offers})


def videos_objects_api(request):
    """API: список объектов для фильтра (Mongo версия для newbuild)."""
    category = request.GET.get('category', '')
    objects = []
    if category == 'newbuild':
        db = get_mongo_connection()
        unified = db['unified_houses']
        # Берём первые 1000 для селекта
        for r in unified.find({}, {'development.name': 1}).limit(1000):
            name = (r.get('development', {}) or {}).get('name') or (r.get('avito', {}) or {}).get('development', {}) .get('name') or (r.get('domclick', {}) or {}).get('development', {}) .get('complex_name') or 'ЖК'
            objects.append({'id': str(r.get('_id')), 'name': name})
    return JsonResponse({'success': True, 'objects': objects})


# ===================== MONGO VIDEOS API =====================
@csrf_exempt
@require_http_methods(["POST"]) 
def videos_create(request):
    """Создать видеообзор (residential_videos)."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        complex_id = payload.get('complex_id')
        url = (payload.get('url') or '').strip()
        title = (payload.get('title') or '').strip()
        description = (payload.get('description') or '').strip()
        is_active = bool(payload.get('is_active', True))
        if not complex_id or not url or not title:
            return JsonResponse({'success': False, 'error': 'complex_id, url и title обязательны'}, status=400)

        db = get_mongo_connection()
        videos_col = db['residential_videos']
        doc = {
            'complex_id': ObjectId(str(complex_id)),
            'url': url,
            'title': title[:200],
            'description': description[:2000],
            'is_active': is_active,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        res = videos_col.insert_one(doc)
        return JsonResponse({'success': True, 'id': str(res.inserted_id)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"]) 
def videos_list(request):
    """Список видеообзоров (для админ-UI/страницы)."""
    try:
        active = request.GET.get('active')
        db = get_mongo_connection()
        videos_col = db['residential_videos']
        unified = db['unified_houses']
        q = {}
        if active in ('1', 'true', 'True'):
            q['is_active'] = True
        items = []
        for d in videos_col.find(q).sort('created_at', -1):
            comp_name = ''
            try:
                comp = unified.find_one({'_id': d.get('complex_id')}) if isinstance(d.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(d.get('complex_id')))})
                if comp:
                    if 'development' in comp and 'avito' not in comp:
                        comp_name = (comp.get('development', {}) or {}).get('name', '')
                    else:
                        comp_name = (comp.get('avito', {}) or {}).get('development', {}) .get('name') or (comp.get('domclick', {}) or {}).get('development', {}) .get('complex_name', '')
            except Exception:
                comp_name = ''
            items.append({
                '_id': str(d.get('_id')),
                'complex_id': str(d.get('complex_id')) if d.get('complex_id') else None,
                'complex_name': comp_name,
                'title': d.get('title'),
                'description': d.get('description'),
                'is_active': d.get('is_active', True),
                'created_at': d.get('created_at').isoformat() if d.get('created_at') else None,
            })
        return JsonResponse({'success': True, 'data': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"]) 
def videos_by_complex(request, complex_id):
    """Видео по конкретному ЖК для детальной страницы."""
    try:
        db = get_mongo_connection()
        videos_col = db['residential_videos']
        vids = []
        q = {'is_active': True}
        try:
            q['complex_id'] = ObjectId(str(complex_id))
        except Exception:
            return JsonResponse({'success': True, 'data': []})
        for d in videos_col.find(q).sort('created_at', -1):
            url = (d.get('url') or '').strip()
            embed = None
            if url.startswith('<iframe'):
                import re
                m = re.search(r'src=["\']([^"\']+)["\']', url)
                embed = m.group(1) if m else url
            elif 'youtu.be/' in url:
                vid = url.split('youtu.be/')[-1].split('?')[0]
                embed = f'https://www.youtube.com/embed/{vid}'
            elif 'watch?v=' in url:
                vid = url.split('watch?v=')[-1].split('&')[0]
                embed = f'https://www.youtube.com/embed/{vid}'
            elif 'rutube.ru' in url:
                if '/play/embed/' in url:
                    embed = url
                else:
                    import re
                    rm = re.search(r'rutube\.ru/video/([a-f0-9]+)', url)
                    embed = f'https://rutube.ru/play/embed/{rm.group(1)}/' if rm else url
            else:
                embed = url
            vids.append({'id': str(d.get('_id')), 'title': d.get('title',''), 'video_url': embed})
        return JsonResponse({'success': True, 'data': vids})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PATCH"]) 
def videos_toggle(request, video_id):
    try:
        db = get_mongo_connection()
        videos_col = db['residential_videos']
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        if 'is_active' in payload:
            new_val = bool(payload.get('is_active'))
        else:
            doc = videos_col.find_one({'_id': ObjectId(video_id)})
            current = bool(doc.get('is_active', True)) if doc else True
            new_val = not current
        videos_col.update_one({'_id': ObjectId(video_id)}, {'$set': {'is_active': new_val, 'updated_at': datetime.utcnow()}})
        return JsonResponse({'success': True, 'is_active': new_val})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============== РУЧНОЕ СОПОСТАВЛЕНИЕ MONGODB ===============

def get_mongo_connection():
    """Получить подключение к MongoDB"""
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:Kfleirb_17@176.98.177.188:27017/admin")
    DB_NAME = os.getenv("DB_NAME", "houses")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db


def manual_matching(request):
    """Интерфейс ручного сопоставления данных из MongoDB"""
    return render(request, 'main/manual_matching.html')


@require_http_methods(["GET"])
def get_unmatched_records(request):
    """API: Получить несопоставленные записи из трех коллекций"""
    try:
        db = get_mongo_connection()
        
        # Получаем коллекции
        domrf_col = db['domrf']
        avito_col = db['avito']
        domclick_col = db['domclick']
        unified_col = db['unified_houses']
        
        # Получаем ID уже сопоставленных записей
        matched_records = list(unified_col.find({}, {
            'domrf.name': 1, 
            'avito._id': 1, 
            'domclick._id': 1
        }))
        
        # Собираем ID сопоставленных записей
        matched_domrf_names = set()
        matched_avito_ids = set()
        matched_domclick_ids = set()
        
        for record in matched_records:
            if record.get('domrf', {}).get('name'):
                matched_domrf_names.add(record['domrf']['name'])
            if record.get('avito', {}).get('_id'):
                matched_avito_ids.add(ObjectId(record['avito']['_id']))
            if record.get('domclick', {}).get('_id'):
                matched_domclick_ids.add(ObjectId(record['domclick']['_id']))
        
        # Получаем параметры пагинации и поиска
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 50))  # Увеличиваем до 50 записей
        search = request.GET.get('search', '').strip()
        
        # Формируем фильтры для поиска
        domrf_filter = {}
        avito_filter = {}
        domclick_filter = {}
        
        if search:
            domrf_filter['objCommercNm'] = {'$regex': search, '$options': 'i'}
            avito_filter['development.name'] = {'$regex': search, '$options': 'i'}
            domclick_filter['development.complex_name'] = {'$regex': search, '$options': 'i'}
        
        # Получаем несопоставленные записи (убираем ограничение для лучшего отображения)
        domrf_records = list(domrf_col.find(domrf_filter).limit(100))
        domrf_unmatched = [
            {
                '_id': str(r['_id']),
                'name': r.get('objCommercNm', 'Без названия'),
                'url': r.get('url', ''),
                'address': r.get('address', ''),
                'latitude': r.get('latitude'),
                'longitude': r.get('longitude')
            }
            for r in domrf_records 
            if r.get('objCommercNm') not in matched_domrf_names
        ][:per_page]
        
        avito_records = list(avito_col.find(avito_filter).limit(100))
        avito_unmatched = [
            {
                '_id': str(r['_id']),
                'name': r.get('development', {}).get('name', 'Без названия'),
                'url': r.get('url', ''),
                'address': r.get('location', {}).get('address', ''),
            }
            for r in avito_records 
            if r['_id'] not in matched_avito_ids
        ][:per_page]
        
        domclick_records = list(domclick_col.find(domclick_filter).limit(100))
        domclick_unmatched = [
            {
                '_id': str(r['_id']),
                'name': r.get('development', {}).get('complex_name', 'Без названия'),
                'url': r.get('url', ''),
                'address': r.get('location', {}).get('address', ''),
            }
            for r in domclick_records 
            if r['_id'] not in matched_domclick_ids
        ][:per_page]
        
        # Считаем общее количество
        total_domrf = domrf_col.count_documents(domrf_filter)
        total_avito = avito_col.count_documents(avito_filter)
        total_domclick = domclick_col.count_documents(domclick_filter)
        
        return JsonResponse({
            'success': True,
            'data': {
                'domrf': domrf_unmatched,
                'avito': avito_unmatched,
                'domclick': domclick_unmatched
            },
            'totals': {
                'domrf': len(domrf_unmatched),
                'avito': len(avito_unmatched),
                'domclick': len(domclick_unmatched),
                'total_domrf': total_domrf - len(matched_domrf_names),
                'total_avito': total_avito - len(matched_avito_ids),
                'total_domclick': total_domclick - len(matched_domclick_ids)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def save_manual_match(request):
    """API: Сохранить ручное сопоставление (новая упрощенная структура)"""
    try:
        data = json.loads(request.body)
        domrf_id = data.get('domrf_id')
        avito_id = data.get('avito_id')
        domclick_id = data.get('domclick_id')
        
        # Проверка: должен быть хотя бы один DomRF и еще один источник
        if not domrf_id:
            return JsonResponse({
                'success': False,
                'error': 'DomRF обязателен для сопоставления'
            }, status=400)
        
        if not avito_id and not domclick_id:
            return JsonResponse({
                'success': False,
                'error': 'Необходимо выбрать хотя бы Avito или DomClick'
            }, status=400)
        
        db = get_mongo_connection()
        
        # Получаем полные записи
        domrf_col = db['domrf']
        avito_col = db['avito']
        domclick_col = db['domclick']
        unified_col = db['unified_houses']
        
        domrf_record = domrf_col.find_one({'_id': ObjectId(domrf_id)})
        if not domrf_record:
            return JsonResponse({
                'success': False,
                'error': 'Запись DomRF не найдена'
            }, status=404)
        
        avito_record = None
        if avito_id:
            avito_record = avito_col.find_one({'_id': ObjectId(avito_id)})
        
        domclick_record = None
        if domclick_id:
            domclick_record = domclick_col.find_one({'_id': ObjectId(domclick_id)})
        
        # === НОВАЯ УПРОЩЕННАЯ СТРУКТУРА ===
        
        # 1. Координаты из DomRF (только это!)
        unified_record = {
            'latitude': domrf_record.get('latitude'),
            'longitude': domrf_record.get('longitude'),
            'source': 'manual',
            'created_by': 'manual'
        }
        
        # 2. Development из Avito + photos из DomClick
        if avito_record:
            avito_dev = avito_record.get('development', {})
            unified_record['development'] = {
                'name': avito_dev.get('name', ''),
                'address': avito_dev.get('address', ''),
                'price_range': avito_dev.get('price_range', ''),
                'parameters': avito_dev.get('parameters', {}),
                'korpuses': avito_dev.get('korpuses', []),
                'photos': []  # Будет заполнено из DomClick
            }
            
            # Добавляем фото ЖК из DomClick
            if domclick_record:
                domclick_dev = domclick_record.get('development', {})
                unified_record['development']['photos'] = domclick_dev.get('photos', [])
        
        # 3. Объединяем apartment_types (Avito + фото из DomClick)
        unified_record['apartment_types'] = {}
        
        if avito_record and domclick_record:
            avito_apt_types = avito_record.get('apartment_types', {})
            domclick_apt_types = domclick_record.get('apartment_types', {})
            
            # Маппинг старых названий на новые упрощенные
            name_mapping = {
                # Студия
                'Студия': 'Студия',
                # 1-комнатные (разные варианты названий из Avito и DomClick)
                '1 ком.': '1',
                '1-комн': '1',
                '1-комн.': '1',
                # 2-комнатные
                '2': '2',
                '2-комн': '2',
                '2-комн.': '2',
                # 3-комнатные
                '3': '3',
                '3-комн': '3',
                '3-комн.': '3',
                # 4-комнатные
                '4': '4',
                '4-комн': '4',
                '4-комн.': '4',
                '4-комн.+': '4',
                '4-комн+': '4'
            }
            
            # Сначала обрабатываем все типы из DomClick (чтобы не пропустить 1-комнатные)
            processed_types = set()
            
            for dc_type_name, dc_type_data in domclick_apt_types.items():
                # Упрощаем название типа
                simplified_name = name_mapping.get(dc_type_name, dc_type_name)
                
                # Пропускаем если уже обработали этот упрощенный тип
                if simplified_name in processed_types:
                    continue
                processed_types.add(simplified_name)
                
                # Получаем квартиры из DomClick
                dc_apartments = dc_type_data.get('apartments', [])
                if not dc_apartments:
                    continue
                
                # Ищем соответствующий тип в Avito
                avito_apartments = []
                for avito_type_name, avito_data in avito_apt_types.items():
                    avito_simplified = name_mapping.get(avito_type_name, avito_type_name)
                    if avito_simplified == simplified_name:
                        avito_apartments = avito_data.get('apartments', [])
                        break
                
                # Объединяем: количество квартир = количество квартир в DomClick
                combined_apartments = []
                
                for i, dc_apt in enumerate(dc_apartments):
                    # Получаем ВСЕ фото этой квартиры из DomClick как МАССИВ
                    apartment_photos = dc_apt.get('photos', [])
                    
                    # Если фото нет - пропускаем эту квартиру
                    if not apartment_photos:
                        continue
                    
                    # Берем соответствующую квартиру из Avito (циклически)
                    avito_apt = avito_apartments[i % len(avito_apartments)] if avito_apartments else {}
                    
                    combined_apartments.append({
                        'title': avito_apt.get('title', ''),
                        'price': avito_apt.get('price', ''),
                        'pricePerSquare': avito_apt.get('pricePerSquare', ''),
                        'completionDate': avito_apt.get('completionDate', ''),
                        'url': avito_apt.get('urlPath', ''),
                        'image': apartment_photos  # МАССИВ всех фото этой планировки!
                    })
                
                # Добавляем в результат только если есть квартиры с фото
                if combined_apartments:
                    unified_record['apartment_types'][simplified_name] = {
                        'apartments': combined_apartments
                    }
        
        # Сохраняем ссылки на исходные записи для отладки
        unified_record['_source_ids'] = {
            'domrf': str(domrf_record['_id']),
            'avito': str(avito_record['_id']) if avito_record else None,
            'domclick': str(domclick_record['_id']) if domclick_record else None
        }
        
        # Сохраняем
        result = unified_col.insert_one(unified_record)

    return JsonResponse({
        'success': True,
            'message': 'Сопоставление успешно сохранено',
            'unified_id': str(result.inserted_id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_unified_records(request):
    """API: Получить уже объединенные записи"""
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Параметры пагинации
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        skip = (page - 1) * per_page
        
        # Получаем записи
        records = list(unified_col.find({}).skip(skip).limit(per_page))
        total = unified_col.count_documents({})
        
        # Форматируем записи
        formatted_records = []
        for record in records:
            # Имя ЖК для новой и старой структуры
            unified_name = None
            if 'development' in record and 'avito' not in record:
                unified_name = record.get('development', {}).get('name')
            if not unified_name:
                unified_name = (record.get('avito', {}) or {}).get('development', {}) .get('name') or \
                               (record.get('domclick', {}) or {}).get('development', {}) .get('complex_name') or \
                               (record.get('domrf', {}) or {}).get('name', 'N/A')

            formatted_records.append({
                '_id': str(record['_id']),
                'name': unified_name or 'N/A',
                'domrf_name': record.get('domrf', {}).get('name', 'N/A'),
                'avito_name': record.get('avito', {}).get('development', {}).get('name', 'N/A') if record.get('avito') else 'N/A',
                'domclick_name': record.get('domclick', {}).get('development', {}).get('complex_name', 'N/A') if record.get('domclick') else 'N/A',
                'source': record.get('source', 'unknown')
            })
        
        return JsonResponse({
            'success': True,
            'data': formatted_records,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"]) 
def promotions_create(request):
    """Создать акцию для ЖК (MongoDB promotions)."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        complex_id = payload.get('complex_id')
        title = (payload.get('title') or '').strip()
        description = (payload.get('description') or '').strip()
        starts_at = payload.get('starts_at')
        ends_at = payload.get('ends_at')

        if not complex_id or not title:
            return JsonResponse({'success': False, 'error': 'complex_id и title обязательны'}, status=400)

        db = get_mongo_connection()
        promotions = db['promotions']

        doc = {
            'complex_id': ObjectId(complex_id),
            'title': title[:120],
            'description': description[:2000],
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        if starts_at: doc['starts_at'] = starts_at
        if ends_at: doc['ends_at'] = ends_at

        inserted = promotions.insert_one(doc)
        return JsonResponse({'success': True, 'id': str(inserted.inserted_id)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"]) 
def promotions_list(request):
    """Список акций (опционально только активные)."""
    try:
        active = request.GET.get('active')
        db = get_mongo_connection()
        promotions = db['promotions']
        q = {}
        if active in ('1', 'true', 'True'):
            q['is_active'] = True
        items = []
        unified = db['unified_houses']
        for p in promotions.find(q).sort('created_at', -1):
            comp_name = ''
            try:
                comp = unified.find_one({'_id': ObjectId(str(p.get('complex_id')))})
                if comp:
                    if 'development' in comp and 'avito' not in comp:
                        comp_name = (comp.get('development', {}) or {}).get('name', '')
                    else:
                        comp_name = (comp.get('avito', {}) or {}).get('development', {}) .get('name') or (comp.get('domclick', {}) or {}).get('development', {}) .get('complex_name', '')
            except Exception:
                comp_name = ''
            items.append({
                '_id': str(p.get('_id')),
                'complex_id': str(p.get('complex_id')) if p.get('complex_id') else None,
                'complex_name': comp_name,
                'title': p.get('title'),
                'description': p.get('description'),
                'is_active': p.get('is_active', True)
            })
        return JsonResponse({'success': True, 'data': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"]) 
def promotions_delete(request, promo_id):
    try:
        db = get_mongo_connection()
        promotions = db['promotions']
        promotions.delete_one({'_id': ObjectId(promo_id)})
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PATCH"]) 
def promotions_toggle(request, promo_id):
    try:
        db = get_mongo_connection()
        promotions = db['promotions']
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        if 'is_active' in payload:
            new_val = bool(payload.get('is_active'))
        else:
            doc = promotions.find_one({'_id': ObjectId(promo_id)})
            current = bool(doc.get('is_active', True)) if doc else True
            new_val = not current
        promotions.update_one({'_id': ObjectId(promo_id)}, {'$set': {'is_active': new_val, 'updated_at': datetime.utcnow()}})
        return JsonResponse({'success': True, 'is_active': new_val})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"]) 
def unified_delete(request, unified_id):
    try:
        db = get_mongo_connection()
        unified = db['unified_houses']
        unified.delete_one({'_id': ObjectId(unified_id)})
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
