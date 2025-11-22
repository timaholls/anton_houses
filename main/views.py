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
    client_catalog,
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
    preview_future_project,
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
    get_client_catalog_apartments,
    create_apartment_selection,
    get_apartment_selections,
    get_apartment_selection,
    update_apartment_selection,
    delete_apartment_selection,
    get_complexes_with_apartments,
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
    branch_office_api_toggle, branch_office_api_delete, branch_office_delete_image,
    # Employee API
    employee_api_list, employee_api_create, employee_api_detail, employee_api_update,
    employee_api_toggle, employee_api_delete, employee_delete_image,
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
    secondary_api_update, secondary_api_delete, secondary_api_delete_photo,
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
    'secondary_api_update', 'secondary_api_delete', 'secondary_api_delete_photo',
]

# Дополнительные импорты для API
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime, date
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
        delivery_quarter = request.GET.get('delivery_quarter', '').strip()
        
        # Сортировка
        sort = request.GET.get('sort', 'price_asc')
        
        # Поиск
        search = request.GET.get('search', '').strip()
        
        # Фильтр по выбранным ЖК (может быть несколько через запятую)
        complexes_param = request.GET.get('complexes', '').strip()
        selected_complex_ids = []
        if complexes_param:
            try:
                selected_complex_ids = [ObjectId(cid.strip()) for cid in complexes_param.split(',') if cid.strip()]
            except:
                selected_complex_ids = []

        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Преобразуем квартал в конечную дату для фильтрации
        delivery_date_limit = None
        if delivery_quarter:
            try:
                # Формат: Q4_2025
                parts = delivery_quarter.split('_')
                if len(parts) == 2:
                    quarter = int(parts[0][1:])  # Убираем 'Q' и преобразуем в число
                    year = int(parts[1])
                    
                    # Вычисляем последний день квартала
                    if quarter == 1:
                        delivery_date_limit = date(year, 3, 31)
                    elif quarter == 2:
                        delivery_date_limit = date(year, 6, 30)
                    elif quarter == 3:
                        delivery_date_limit = date(year, 9, 30)
                    elif quarter == 4:
                        delivery_date_limit = date(year, 12, 31)
            except (ValueError, IndexError):
                delivery_date_limit = None
        
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
        
        # Фильтр по местоположению - используем address_* поля с fallback на старые поля
        if city:
            filter_query['$or'] = [
                {'address_city': city},
                {'city': city}
            ]
        if district:
            if '$or' in filter_query:
                # Если уже есть $or для города, добавляем район через $and
                filter_query = {
                    '$and': [
                        filter_query,
                        {
                            '$or': [
                                {'address_district': district},
                                {'district': district}
                            ]
                        }
                    ]
                }
            else:
                filter_query['$or'] = [
                    {'address_district': district},
                    {'district': district}
                ]
        if street:
            street_filter = {
                '$or': [
                    {'address_street': street},
                    {'street': street}
                ]
            }
            if '$and' in filter_query:
                filter_query['$and'].append(street_filter)
            elif '$or' in filter_query:
                filter_query = {
                    '$and': [
                        filter_query,
                        street_filter
                    ]
                }
            else:
                filter_query.update(street_filter)
            
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
            
            # Фильтр по выбранным ЖК
            if selected_complex_ids:
                if record['_id'] not in selected_complex_ids:
                    continue
            
            # Фильтр по сроку сдачи (до выбранного квартала)
            if delivery_date_limit:
                # Получаем срок сдачи из parameters (как в catalog_api)
                completion_date_str = None
                if 'development' in record and 'avito' not in record:
                    # Новая структура
                    dev = record.get('development', {})
                    parameters = dev.get('parameters', {})
                    completion_date_str = parameters.get('Срок сдачи', '')
                else:
                    # Старая структура - проверяем разные источники
                    avito_dev = record.get('avito', {}).get('development', {})
                    if avito_dev:
                        parameters = avito_dev.get('parameters', {})
                        completion_date_str = parameters.get('Срок сдачи', '')
                    
                    if not completion_date_str:
                        domrf_dev = record.get('domrf', {}).get('development', {})
                        if domrf_dev:
                            parameters = domrf_dev.get('parameters', {})
                            completion_date_str = parameters.get('Срок сдачи', '')
                
                if not completion_date_str:
                    # Если у ЖК нет срока сдачи, пропускаем его при фильтрации
                    continue
                
                # Парсим срок сдачи (формат: "4 кв. 2017 — 2 кв. 2027" или "3 кв. 2024")
                import re
                patterns = re.findall(r'(\d+)\s*кв\.\s*(\d{4})', completion_date_str)
                
                if not patterns:
                    # Если не удалось распарсить, пропускаем
                    continue
                
                # Берем максимальную дату (последний квартал в диапазоне)
                max_delivery_date = None
                for quarter_str, year_str in patterns:
                    try:
                        quarter = int(quarter_str)
                        year = int(year_str)
                        
                        # Вычисляем последний день квартала
                        if quarter == 1:
                            end_date = date(year, 3, 31)
                        elif quarter == 2:
                            end_date = date(year, 6, 30)
                        elif quarter == 3:
                            end_date = date(year, 9, 30)
                        elif quarter == 4:
                            end_date = date(year, 12, 31)
                        else:
                            continue
                        
                        if not max_delivery_date or end_date > max_delivery_date:
                            max_delivery_date = end_date
                    except (ValueError, TypeError):
                        continue
                
                # Фильтруем: показываем только ЖК со сроком сдачи до выбранного квартала
                if max_delivery_date and max_delivery_date > delivery_date_limit:
                    continue
            
            # Фильтр по наличию акций
            if has_offers == 'true' and complexes_with_offers:
                # Если выбрана фильтрация по акциям, показываем только ЖК с активными акциями
                if record['_id'] not in complexes_with_offers:
                    continue
            
            # Фильтр по комнатам (поддержка множественного выбора через запятую)
            if rooms:
                # Разбиваем строку на список значений (поддержка множественного выбора)
                selected_rooms = [r.strip() for r in rooms.split(',') if r.strip()]
                if selected_rooms:
                    apartment_types = {}
                    if 'development' in record and 'avito' not in record:
                        # Новая структура
                        apartment_types = record.get('apartment_types', {})
                    else:
                        # Старая структура
                        apartment_types = record.get('avito', {}).get('apartment_types', {})
                    
                    has_matching_rooms = False
                    for apt_type, apt_data in apartment_types.items():
                        if apt_type in selected_rooms:
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
        # Форматируем данные для каталога и собираем данные для карты
        formatted_records = []
        map_points = []
        
        for record in filtered_records:
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
                
                # Координаты: всегда берем из объединенной записи, DomRF используем только как резерв
                latitude = record.get('latitude') or domrf_data.get('latitude')
                longitude = record.get('longitude') or domrf_data.get('longitude')
                
                # Параметры из avito
                parameters = avito_dev.get('parameters', {})
                
                # Типы квартир из avito
                apartment_types = record.get('avito', {}).get('apartment_types', {})
            
            # Подсчитываем общее количество квартир
            total_apartments = 0
            for apt_type, apt_data in apartment_types.items():
                apartments = apt_data.get('apartments', [])
                total_apartments += len(apartments)

            formatted_record = {
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
            }

            formatted_records.append(formatted_record)

            if latitude and longitude:
                map_points.append({
                    'id': formatted_record['id'],
                    'name': formatted_record['name'],
                    'price_range': formatted_record['price_range'],
                    'price_display': formatted_record['price_display'],
                    'lat': latitude,
                    'lng': longitude,
                    'latitude': latitude,
                    'longitude': longitude,
                })

        complexes_data = formatted_records[start_idx:end_idx]

        total_pages = (total_count + per_page - 1) // per_page

        return JsonResponse({
            'complexes': complexes_data,
            'map_points': map_points,
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
    """API для получения районов по городу - данные из unified_houses"""
    city = request.GET.get('city', '')
    if city:
        try:
            db = get_mongo_connection()
            collection = db['unified_houses']
            # Фильтруем по address_city или city
            query = {
                '$or': [
                    {'address_city': city},
                    {'city': city}
                ],
                'address_district': {'$ne': None, '$ne': ''}
            }
            districts = collection.distinct('address_district', query)
            districts = [district for district in districts if district]
            districts = sorted(districts)
        except Exception:
            districts = []
    else:
        districts = []

    return JsonResponse({'districts': list(districts)})


def streets_api(request):
    """API для получения улиц по городу и району - данные из unified_houses"""
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')

    if city:
        try:
            db = get_mongo_connection()
            collection = db['unified_houses']
            # Фильтруем по address_city или city
            query = {
                '$or': [
                    {'address_city': city},
                    {'city': city}
                ],
                'address_street': {'$ne': None, '$ne': ''}
            }
            # Если указан район, добавляем фильтр по району
            if district:
                query = {
                    '$and': [
                        {
                            '$or': [
                                {'address_city': city},
                                {'city': city}
                            ]
                        },
                        {
                            '$or': [
                                {'address_district': district},
                                {'district': district}
                            ]
                        },
                        {'address_street': {'$ne': None, '$ne': ''}}
                    ]
                }
            streets = collection.distinct('address_street', query)
            streets = [street for street in streets if street]
            streets = sorted(streets)
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
