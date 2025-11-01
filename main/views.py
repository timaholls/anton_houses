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
from .view_modules.home_views import home, privacy_policy, unsubscribe_page
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
from .view_modules.services_views import services
from .view_modules.mortgage_views import mortgage
from .view_modules.offer_views import all_offers, offer_detail
from .view_modules.future_complex_views import future_complexes, future_complex_detail
from .view_modules.management_views import content_management, company_management, manual_matching
from .view_modules.not_recommended_views import not_recommended, not_recommended_detail

# API imports
from .api.manual_matching_api import (
    get_unmatched_records,
    save_manual_match,
    preview_manual_match,
    get_unified_records,
    unified_delete,
    unified_get,
    unified_update,
    toggle_featured,
    domrf_create,
    delete_record,
    get_future_projects,
    create_future_project,
    get_domrf_data,
    delete_photo,
    get_apartment_stats,
)
from .api.content_management_api import (
    # Tags API
    tags_api_list, tags_api_create, tags_api_get, tags_api_update, tags_api_toggle, tags_api_delete,
    # Categories API  
    categories_api_list, categories_api_create, categories_api_get, categories_api_update, categories_api_toggle, categories_api_delete,
    # Authors API
    authors_api_list, authors_api_create, authors_api_toggle, authors_api_delete,
    # Articles API
    articles_api_list, articles_api_create, articles_api_get, articles_api_update, articles_api_toggle, articles_api_delete,
    # Catalog Landings API
    catalog_landings_api_list, catalog_landings_api_create, catalog_landings_api_get, catalog_landings_api_update, 
    catalog_landings_api_toggle, catalog_landings_api_delete,
)
from .api.company_management_api import (
    # Employee Reviews API
    employee_reviews_api, employee_review_toggle, employee_review_update, employee_review_delete,
    # Company Info API
    company_info_api_list, company_info_api_create, company_info_api_detail, company_info_api_update, 
    company_info_api_toggle, company_info_api_delete, company_info_delete_image,
    # Branch Office API
    branch_office_api_list, branch_office_api_create, branch_office_api_detail, branch_office_api_update, 
    branch_office_api_toggle, branch_office_api_delete,
    # Employee API
    employee_api_list, employee_api_create, employee_api_detail, employee_api_update, 
    employee_api_toggle, employee_api_delete,
)

# Дополнительные API модули
from .api.vacancies_api import (
    vacancies_api_list, vacancies_api_create, vacancies_api_toggle, vacancies_api_delete,
)
from .api.videos_api import (
    videos_objects_api, videos_create, videos_list, videos_by_complex, videos_toggle, videos_api_delete,
)
from .api.mortgage_api import (
    mortgage_programs_list, mortgage_programs_create, mortgage_programs_update, mortgage_programs_delete,
)
from .api.promotions_api import (
    promotions_create, promotions_list, promotions_delete, promotions_toggle,
)
from .api.secondary_api import (
    secondary_list, secondary_create, secondary_api_toggle, secondary_api_get, 
    secondary_api_update, secondary_api_delete,
)

# Явно экспортируем все функции для использования в urls.py
__all__ = [
    # Auth
    'login_view', 
    'logout_view',
    # Home & General
    'home', 
    'privacy_policy',
    'services',
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
    # Manual matching API
    'get_unmatched_records',
    'save_manual_match',
    'get_unified_records',
    'unified_delete',
    'unified_get',
    'unified_update',
    'toggle_featured',
    'domrf_create',
    'delete_record',
    'get_future_projects',
    'create_future_project',
    'get_domrf_data',
    'delete_photo',
    'get_apartment_stats',
    # Content management API
    'tags_api_list', 'tags_api_create', 'tags_api_get', 'tags_api_update', 'tags_api_toggle', 'tags_api_delete',
    'categories_api_list', 'categories_api_create', 'categories_api_get', 'categories_api_update', 'categories_api_toggle', 'categories_api_delete',
    'authors_api_list', 'authors_api_create', 'authors_api_toggle', 'authors_api_delete',
    'articles_api_list', 'articles_api_create', 'articles_api_get', 'articles_api_update', 'articles_api_toggle', 'articles_api_delete',
    'catalog_landings_api_list', 'catalog_landings_api_create', 'catalog_landings_api_get', 'catalog_landings_api_update', 
    'catalog_landings_api_toggle', 'catalog_landings_api_delete',
    # Company management API
    'employee_reviews_api', 'employee_review_toggle', 'employee_review_update', 'employee_review_delete',
    'company_info_api_list', 'company_info_api_create', 'company_info_api_detail', 'company_info_api_update', 
    'company_info_api_toggle', 'company_info_api_delete',
    'branch_office_api_list', 'branch_office_api_create', 'branch_office_api_detail', 'branch_office_api_update', 
    'branch_office_api_toggle', 'branch_office_api_delete',
    'employee_api_list', 'employee_api_create', 'employee_api_detail', 'employee_api_update', 
    'employee_api_toggle', 'employee_api_delete',
    # Vacancies API
    'vacancies_api_list', 'vacancies_api_create', 'vacancies_api_toggle', 'vacancies_api_delete',
    # Videos API
    'videos_objects_api', 'videos_create', 'videos_list', 'videos_by_complex', 'videos_toggle', 'videos_api_delete',
    # Mortgage API
    'mortgage_programs_list', 'mortgage_programs_create', 'mortgage_programs_update', 'mortgage_programs_delete',
    # Promotions API
    'promotions_create', 'promotions_list', 'promotions_delete', 'promotions_toggle',
    # Secondary API
    'secondary_list', 'secondary_create', 'secondary_api_toggle', 'secondary_api_get', 
    'secondary_api_update', 'secondary_api_delete',
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
    """API для каталога ЖК из MongoDB unified_houses с полной поддержкой фильтрации"""
    try:
        # Получаем параметры фильтрации
        page = int(request.GET.get('page', 1))
        per_page = 9
        
        # Фильтры местоположения
        city = request.GET.get('city', '').strip()
        district = request.GET.get('district', '').strip()
        street = request.GET.get('street', '').strip()
        
        # Фильтры недвижимости
        rooms = request.GET.get('rooms', '').strip()
        area_from = request.GET.get('area_from', '').strip()
        area_to = request.GET.get('area_to', '').strip()
        price_from = request.GET.get('price_from', '').strip()
        price_to = request.GET.get('price_to', '').strip()
        has_offers = request.GET.get('has_offers', '').strip()
        mortgage_program_id = request.GET.get('mortgage_program', '').strip()
        
        # Сортировка
        sort = request.GET.get('sort', 'price_asc')
        
        # Поиск
        search = request.GET.get('search', '').strip()

        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем информацию об ипотечной программе, если выбрана
        mortgage_program_complexes = []
        if mortgage_program_id:
            try:
                mortgage_program = db['mortgage_programs'].find_one({'_id': ObjectId(mortgage_program_id)})
                if mortgage_program and mortgage_program.get('is_individual'):
                    # Если программа индивидуальная, получаем список привязанных ЖК
                    mortgage_program_complexes = mortgage_program.get('complexes', [])
            except:
                pass
        
        # Получаем список ЖК с акциями, если выбрана фильтрация по акциям
        complexes_with_offers = []
        if has_offers == 'true':
            try:
                promotions_col = db['promotions']
                promotions_data = list(promotions_col.find({'is_active': True}))
                complexes_with_offers = [promo.get('complex_id') for promo in promotions_data if promo.get('complex_id')]
            except:
                pass

        # Формируем фильтр - ищем записи с любой структурой (старая или новая)
        filter_query = {}
        
        # Фильтр по местоположению
        if city:
            filter_query['city'] = city
        if district:
            filter_query['district'] = district
        if street:
            filter_query['street'] = street
            
        # Поиск по названию
        if search:
            filter_query['development.name'] = {'$regex': search, '$options': 'i'}

        # Получаем все записи для фильтрации на стороне приложения
        # (так как MongoDB не может эффективно фильтровать по сложным полям)
        all_records = list(unified_col.find(filter_query))
        
        # Фильтруем данные на стороне приложения
        filtered_records = []
        
        for record in all_records:
            # Проверяем фильтры, которые требуют парсинга данных
            
            # Фильтр по ипотечной программе
            if mortgage_program_complexes:
                # Если выбрана индивидуальная программа, показываем только привязанные ЖК
                if record['_id'] not in mortgage_program_complexes:
                    continue
            
            # Фильтр по наличию акций
            if has_offers == 'true' and complexes_with_offers:
                # Если выбрана фильтрация по акциям, показываем только ЖК с активными акциями
                if record['_id'] not in complexes_with_offers:
                    continue
            
            # Фильтр по комнатам
            if rooms:
                apartment_types = {}
                if 'development' in record and 'avito' not in record:
                    # Новая структура
                    apartment_types = record.get('apartment_types', {})
                else:
                    # Старая структура
                    apartment_types = record.get('avito', {}).get('apartment_types', {})
                
                has_matching_rooms = False
                for apt_type, apt_data in apartment_types.items():
                    if apt_type == rooms:
                        has_matching_rooms = True
                        break
                if not has_matching_rooms:
                    continue
            
            # Фильтр по цене
            price_range = ''
            if 'development' in record and 'avito' not in record:
                # Новая структура
                price_range = record.get('development', {}).get('price_range', '')
            else:
                # Старая структура
                price_range = record.get('avito', {}).get('development', {}).get('price_range', '')
            
            if price_range and (price_from or price_to):
                # Парсим цену из строки типа "От 6,29 до 14,97 млн ₽"
                import re
                price_match = re.search(r'от\s+([\d,]+)\s+до\s+([\d,]+)\s+млн', price_range.lower())
                if price_match:
                    min_price = float(price_match.group(1).replace(',', '.'))  # млн руб
                    max_price = float(price_match.group(2).replace(',', '.'))  # млн руб
                    
                    if price_from:
                        try:
                            price_from_val = float(price_from.replace(',', '.'))
                            # Если минимальная цена ЖК меньше фильтра, пропускаем
                            # (это означает, что в ЖК есть квартиры дешевле фильтра)
                            if min_price < price_from_val:
                                continue
                        except ValueError:
                            pass
                    
                    if price_to:
                        try:
                            price_to_val = float(price_to.replace(',', '.'))
                            if min_price > price_to_val:
                                continue
                            # Также проверяем, что максимальная цена не превышает фильтр
                            if max_price > price_to_val:
                                continue
                        except ValueError:
                            pass
                else:
                    # Если не удалось распарсить цену, пропускаем фильтрацию по цене
                    pass
            
            # Фильтр по площади (проверяем в apartment_types)
            if area_from or area_to:
                apartment_types = {}
                if 'development' in record and 'avito' not in record:
                    # Новая структура
                    apartment_types = record.get('apartment_types', {})
                else:
                    # Старая структура
                    apartment_types = record.get('avito', {}).get('apartment_types', {})
                
                has_matching_area = False
                for apt_type, apt_data in apartment_types.items():
                    apartments = apt_data.get('apartments', [])
                    for apt in apartments:
                        # Ищем площадь в разных полях
                        area = apt.get('area') or apt.get('square') or apt.get('totalArea')
                        
                        # Если площадь не найдена в отдельных полях, пытаемся извлечь из title
                        if not area:
                            title = apt.get('title', '')
                            import re
                            # Ищем паттерн типа "58,9 м²" в title
                            area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                            if area_match:
                                area = area_match.group(1).replace(',', '.')
                        
                        if area:
                            try:
                                area_val = float(str(area))
                                if area_from:
                                    try:
                                        area_from_val = float(area_from)
                                        if area_val < area_from_val:
                                            continue
                                    except ValueError:
                                        pass
                                if area_to:
                                    try:
                                        area_to_val = float(area_to)
                                        if area_val > area_to_val:
                                            continue
                                    except ValueError:
                                        pass
                                has_matching_area = True
                                break
                            except (ValueError, TypeError):
                                pass
                    if has_matching_area:
                        break
                if not has_matching_area and (area_from or area_to):
                    continue
            
            filtered_records.append(record)
        
        # Сортировка
        if sort == 'price_asc':
            # Сортировка по возрастанию цены
            def get_min_price(record):
                price_range = ''
                if 'development' in record and 'avito' not in record:
                    price_range = record.get('development', {}).get('price_range', '')
                else:
                    price_range = record.get('avito', {}).get('development', {}).get('price_range', '')
                
                import re
                price_match = re.search(r'от\s+([\d,]+)\s+млн', price_range.lower())
                if price_match:
                    return float(price_match.group(1).replace(',', '.'))
                return float('inf')
            filtered_records.sort(key=get_min_price)
        elif sort == 'price_desc':
            # Сортировка по убыванию цены
            def get_max_price(record):
                price_range = ''
                if 'development' in record and 'avito' not in record:
                    price_range = record.get('development', {}).get('price_range', '')
                else:
                    price_range = record.get('avito', {}).get('development', {}).get('price_range', '')
                
                import re
                price_match = re.search(r'до\s+([\d,]+)\s+млн', price_range.lower())
                if price_match:
                    return float(price_match.group(1).replace(',', '.'))
                return 0
            filtered_records.sort(key=get_max_price, reverse=True)
        elif sort == 'area_desc':
            # Сортировка по убыванию площади
            def get_max_area(record):
                max_area = 0
                apartment_types = {}
                if 'development' in record and 'avito' not in record:
                    apartment_types = record.get('apartment_types', {})
                else:
                    apartment_types = record.get('avito', {}).get('apartment_types', {})
                
                for apt_type, apt_data in apartment_types.items():
                    apartments = apt_data.get('apartments', [])
                    for apt in apartments:
                        area = apt.get('area') or apt.get('square') or apt.get('totalArea')
                        
                        # Если площадь не найдена в отдельных полях, пытаемся извлечь из title
                        if not area:
                            title = apt.get('title', '')
                            import re
                            # Ищем паттерн типа "58,9 м²" в title
                            area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                            if area_match:
                                area = area_match.group(1).replace(',', '.')
                        
                        if area:
                            try:
                                area_val = float(str(area))
                                max_area = max(max_area, area_val)
                            except (ValueError, TypeError):
                                pass
                return max_area
            filtered_records.sort(key=get_max_area, reverse=True)
        elif sort == 'area_asc':
            # Сортировка по возрастанию площади
            def get_min_area(record):
                min_area = float('inf')
                apartment_types = {}
                if 'development' in record and 'avito' not in record:
                    apartment_types = record.get('apartment_types', {})
                else:
                    apartment_types = record.get('avito', {}).get('apartment_types', {})
                
                for apt_type, apt_data in apartment_types.items():
                    apartments = apt_data.get('apartments', [])
                    for apt in apartments:
                        area = apt.get('area') or apt.get('square') or apt.get('totalArea')
                        
                        # Если площадь не найдена в отдельных полях, пытаемся извлечь из title
                        if not area:
                            title = apt.get('title', '')
                            import re
                            # Ищем паттерн типа "58,9 м²" в title
                            area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                            if area_match:
                                area = area_match.group(1).replace(',', '.')
                        
                        if area:
                            try:
                                area_val = float(str(area))
                                min_area = min(min_area, area_val)
                            except (ValueError, TypeError):
                                pass
                return min_area if min_area != float('inf') else 0
            filtered_records.sort(key=get_min_area)
        
        # Пагинация
        total_count = len(filtered_records)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_records = filtered_records[start_idx:end_idx]

        # Форматируем данные для каталога
        complexes_data = []
        
        for record in paginated_records:
            # Определяем структуру записи
            is_new_structure = 'development' in record and 'avito' not in record
            
            if is_new_structure:
                # === НОВАЯ УПРОЩЕННАЯ СТРУКТУРА ===
                development = record.get('development', {})
                apartment_types = record.get('apartment_types', {})
                
                name = development.get('name', 'Без названия')
                address = development.get('address', '')
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
                
                # Типы квартир из avito
                apartment_types = record.get('avito', {}).get('apartment_types', {})
            
            # Подсчитываем общее количество квартир
            total_apartments = 0
            for apt_type, apt_data in apartment_types.items():
                apartments = apt_data.get('apartments', [])
                total_apartments += len(apartments)

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
                'total_apartments': total_apartments,
                'location': address,
                'city': record.get('city', 'Уфа'),
                'district': record.get('district', ''),
                'street': record.get('street', ''),
                'rating': record.get('rating'),
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
