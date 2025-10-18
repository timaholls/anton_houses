"""
Главный файл views с импортами из модулей для обратной совместимости.
Все функции теперь организованы в соответствующие модули.
"""

# Импорты из модулей для обратной совместимости с urls.py
from .services.auth_service import login_view, logout_view
from .utils import extract_price_from_range, get_video_thumbnail
from .services.mongo_service import (
    get_mongo_connection,
    get_mongo_user,
    get_residential_complexes_from_mongo,
    get_special_offers_from_mongo,
    get_future_complexes_from_mongo,
)

# Views
from .view_modules.home_views import home, privacy_policy
from .view_modules.catalog_views import (
    catalog,
    detail,
    secondary_detail_mongo,
    secondary_detail,
    catalog_completed,
    catalog_construction,
    catalog_economy,
    catalog_comfort,
    catalog_premium,
    catalog_finished,
    catalog_unfinished,
    catalog_landing,
    _catalog_fallback,
    newbuild_index,
    secondary_index,
)
from .view_modules.article_views import articles, article_detail, tag_detail
from .view_modules.vacancy_views import vacancies, vacancy_detail
from .view_modules.office_views import offices, office_detail
from .view_modules.video_views import videos, video_detail
from .view_modules.employee_views import team, agent_properties, employee_detail
from .view_modules.mortgage_views import mortgage
from .view_modules.offer_views import all_offers, offer_detail
from .view_modules.future_complex_views import future_complexes, future_complex_detail
from .view_modules.management_views import content_management, company_management, manual_matching

# Явно экспортируем все функции для использования в urls.py
__all__ = [
    # Auth
    'login_view', 
    'logout_view',
    # Home & General
    'home', 
    'privacy_policy',
    # Catalog Views
    'catalog', 
    'detail', 
    'secondary_detail_mongo', 
    'secondary_detail',
    'catalog_completed', 
    'catalog_construction', 
    'catalog_economy', 
    'catalog_comfort',
    'catalog_premium', 
    'catalog_finished', 
    'catalog_unfinished', 
    'catalog_landing',
    'newbuild_index', 
    'secondary_index',
    # Articles
    'articles', 
    'article_detail', 
    'tag_detail',
    # Vacancies
    'vacancies', 
    'vacancy_detail',
    # Offices
    'offices', 
    'office_detail',
    # Videos
    'videos', 
    'video_detail',
    # Employees
    'team', 
    'agent_properties', 
    'employee_detail',
    # Mortgage
    'mortgage',
    # Offers
    'all_offers', 
    'offer_detail',
    # Future complexes
    'future_complexes', 
    'future_complex_detail',
    # Management
    'content_management', 
    'company_management', 
    'manual_matching',
    # API functions (defined below in this file)
    'catalog_api', 
    'secondary_api', 
    'secondary_api_list',
    'districts_api', 
    'streets_api', 
    'article_view_api',
]

# Дополнительные импорты для API
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime
import json


# ===== ДОПОЛНИТЕЛЬНЫЕ API ФУНКЦИИ =====

@require_http_methods(["GET"])
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
        from .s3_service import PLACEHOLDER_IMAGE_URL

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
                name = avito_dev.get('name') or domclick_dev.get('complex_name') or domrf_data.get('name',
                                                                                                   'Без названия')

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
                'photos': photos,
                'image_url': photos[0] if photos else None,
                'image_2_url': photos[1] if len(photos) > 1 else None,
                'image_3_url': photos[2] if len(photos) > 2 else None,
                'image_4_url': photos[3] if len(photos) > 3 else None,
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
                'city': 'Уфа',
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
        return JsonResponse({
            'complexes': [],
            'has_previous': False,
            'has_next': False,
            'current_page': 1,
            'total_pages': 0,
            'total_count': 0,
            'error': str(e)
        })


def secondary_api(request):
    """API для вторичной недвижимости (AJAX) - legacy"""
    return secondary_api_list(request)


def secondary_api_list(request):
    """API для получения списка объектов вторичной недвижимости с фильтрацией"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 12))
        city = request.GET.get('city')
        district = request.GET.get('district')
        rooms = request.GET.get('rooms')
        stype = request.GET.get('stype')
        area_from = request.GET.get('area_from')
        area_to = request.GET.get('area_to')
        price_from = request.GET.get('price_from')
        price_to = request.GET.get('price_to')
        sort_by = request.GET.get('sort_by', 'created_at')
        sort_order = request.GET.get('sort_order', 'desc')

        db = get_mongo_connection()
        collection = db['secondary_properties']

        filter_dict = {}
        if city:
            filter_dict['city'] = {'$regex': city, '$options': 'i'}
        if district:
            filter_dict['district'] = {'$regex': district, '$options': 'i'}
        if rooms:
            filter_dict['rooms'] = int(rooms)
        if stype:
            filter_dict['house_type'] = stype

        show_all = request.GET.get('admin', 'false').lower() == 'true'
        if not show_all:
            filter_dict['is_active'] = True

        if area_from:
            filter_dict['area'] = {'$gte': float(area_from)}
        if area_to:
            if 'area' in filter_dict:
                filter_dict['area']['$lte'] = float(area_to)
            else:
                filter_dict['area'] = {'$lte': float(area_to)}
        if price_from:
            filter_dict['price'] = {'$gte': int(price_from)}
        if price_to:
            if 'price' in filter_dict:
                filter_dict['price']['$lte'] = int(price_to)
            else:
                filter_dict['price'] = {'$lte': int(price_to)}

        total_count = collection.count_documents(filter_dict)
        skip = (page - 1) * per_page
        sort_direction = -1 if sort_order == 'desc' else 1
        sort_field = sort_by if sort_by in ['created_at', 'price_from', 'area_from', 'name'] else 'created_at'

        cursor = collection.find(filter_dict).skip(skip).limit(per_page).sort(sort_field, sort_direction)

        items = []
        for doc in cursor:
            image_url = None
            if doc.get('photos'):
                image_url = doc['photos'][0]

            price_range = None
            if doc.get('price'):
                price_range = f"{doc.get('price'):,.0f}".replace(',', ' ') + ' ₽'

            items.append({
                'id': str(doc['_id']),
                'name': doc.get('name', ''),
                'city': doc.get('city', ''),
                'district': doc.get('district', ''),
                'rooms': doc.get('rooms'),
                'area_from': doc.get('area'),
                'area_to': None,
                'price_range': price_range,
                'price_display': price_range,
                'image_url': image_url,
                'photos': doc.get('photos', []),
                'description': doc.get('description', ''),
                'address': doc.get('address', ''),
                'total_floors': doc.get('total_floors'),
                'finishing': doc.get('finishing', ''),
                'is_active': doc.get('is_active', True),
                'created_at': doc.get('created_at', datetime.now()),
            })

        total_pages = (total_count + per_page - 1) // per_page

        return JsonResponse({
            'success': True,
            'data': items,
            'items': items,
            'total_count': total_count,
            'current_page': page,
            'total_pages': total_pages,
            'per_page': per_page,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def districts_api(request):
    """API для получения районов по городу - данные из MongoDB"""
    city = request.GET.get('city', '')
    if city:
        try:
            db = get_mongo_connection()
            collection = db['residential_complexes']
            districts = collection.distinct('address.district', {'address.city': city})
            districts = [district for district in districts if district]
        except Exception:
            districts = []
    else:
        districts = []

    return JsonResponse({'districts': list(districts)})


def streets_api(request):
    """API для получения улиц по городу - данные из MongoDB"""
    city = request.GET.get('city', '')

    if city:
        try:
            db = get_mongo_connection()
            collection = db['residential_complexes']
            streets = collection.distinct('address.street', {'address.city': city})
            streets = [street for street in streets if street]
        except Exception:
            streets = []
    else:
        streets = []

    return JsonResponse({'streets': list(streets)})


def article_view_api(request, article_id):
    """API для увеличения счетчика просмотров статьи - MongoDB"""
    if request.method == 'POST':
        try:
            db = get_mongo_connection()
            result = db['articles'].update_one(
                {'_id': ObjectId(article_id)},
                {'$inc': {'views_count': 1}}
            )
            if result.matched_count > 0:
                article = db['articles'].find_one({'_id': ObjectId(article_id)})
                return JsonResponse({'success': True, 'views_count': article.get('views_count', 0)})
            return JsonResponse({'success': False, 'error': 'Статья не найдена'}, status=404)
        except:
            return JsonResponse({'success': False, 'error': 'Статья не найдена'}, status=404)
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
