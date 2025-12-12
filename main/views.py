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
    'apartments_api',
    'complex_apartments_api',
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
import logging

logger = logging.getLogger(__name__)


# ===== ДОПОЛНИТЕЛЬНЫЕ API ФУНКЦИИ =====

@require_http_methods(["GET"])
def catalog_api(request):
    """API для каталога ЖК из MongoDB unified_houses с полной поддержкой фильтрации"""
    try:
        # Получаем параметры фильтрации
        page = int(request.GET.get('page', 1))
        try:
            per_page = int(request.GET.get('per_page', 15))
        except (TypeError, ValueError):
            per_page = 15
        
        # Фильтры местоположения
        city = request.GET.get('city', '').strip()
        district = request.GET.get('district', '').strip()
        street = request.GET.get('street', '').strip()
        
        # Обрабатываем множественные значения для district и street (через запятую)
        districts_list = [d.strip() for d in district.split(',') if d.strip()] if district else []
        streets_list = [s.strip() for s in street.split(',') if s.strip()] if street else []
        complexes_param = request.GET.get('complexes', '').strip()
        selected_complex_ids = []
        if complexes_param:
            for cid in complexes_param.split(','):
                cid = cid.strip()
                if not cid:
                    continue
                try:
                    selected_complex_ids.append(ObjectId(cid))
                except Exception:
                    continue
        
        # Фильтры недвижимости
        rooms = request.GET.get('rooms', '').strip()
        area_from = request.GET.get('area_from', '').strip()
        area_to = request.GET.get('area_to', '').strip()
        price_from = request.GET.get('price_from', '').strip()
        price_to = request.GET.get('price_to', '').strip()
        has_offers = request.GET.get('has_offers', '').strip()
        delivery_quarter = request.GET.get('delivery_quarter', '').strip()
        
        # Функция конвертации цены: если число >= 100, считаем что это рубли и конвертируем в миллионы
        def convert_price_to_millions(price_str):
            """Конвертирует цену в миллионы рублей.
            Если число >= 100, считаем что это рубли и делим на 1 000 000.
            Иначе считаем что это уже миллионы.
            """
            if not price_str:
                return None
            try:
                # Убираем пробелы и заменяем запятую на точку
                price_clean = price_str.replace(' ', '').replace(',', '.')
                price_val = float(price_clean)
                
                # Если число >= 100, считаем что это рубли, конвертируем в миллионы
                if price_val >= 100:
                    return price_val / 1_000_000
                # Иначе считаем что это уже миллионы
                return price_val
            except (ValueError, TypeError):
                return None
        
        # Конвертируем цены из фильтра в миллионы
        price_from_millions = convert_price_to_millions(price_from) if price_from else None
        price_to_millions = convert_price_to_millions(price_to) if price_to else None
        
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
        if districts_list:
            # Множественный выбор районов - используем $in
            district_filter = {
                '$or': [
                    {'address_district': {'$in': districts_list}},
                    {'district': {'$in': districts_list}}
                ]
            }
            if '$or' in filter_query:
                # Если уже есть $or для города, добавляем район через $and
                filter_query = {
                    '$and': [
                        filter_query,
                        district_filter
                    ]
                }
            else:
                filter_query.update(district_filter)
        if streets_list:
            # Множественный выбор улиц - используем $in
            street_filter = {
                '$or': [
                    {'address_street': {'$in': streets_list}},
                    {'street': {'$in': streets_list}}
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
            
            # Фильтр по цене (используем price_range из карточки ЖК)
            if price_from_millions is not None or price_to_millions is not None:
                # Получаем price_range из development (формат: "От 5 млн ₽" или "От 5 до 10 млн ₽")
                development = {}
                if 'development' in record and 'avito' not in record:
                    development = record.get('development', {})
                else:
                    avito_dev = record.get('avito', {}).get('development', {}) if record.get('avito') else {}
                    development = avito_dev
                
                price_range = development.get('price_range', '')
                record_name = development.get('name', 'Без названия')
                
                # Парсим цену из price_range используя extract_price_from_range
                # Функция извлекает первое число из строки (например "от 5 млн" -> 5.0)
                price_from_card = extract_price_from_range(price_range)  # В миллионах
                
                if not price_range or price_from_card == 0:
                    # Если нет price_range, пропускаем запись при фильтрации
                    continue
                
                
                # Фильтр "от X": ЖК включается, если price_from_card >= price_from_millions
                # (цена на карточке "от X млн" должна быть >= указанной в фильтре)
                if price_from_millions is not None:
                    if price_from_card < price_from_millions:
                        continue
                
                # Фильтр "до Y": для "до" нужно извлечь максимальную цену из диапазона
                # Если price_range содержит "до X" или "от X до Y", извлекаем максимальное значение
                if price_to_millions is not None:
                    # Ищем все числа в price_range (может быть "от 5 до 10 млн")
                    import re
                    numbers = re.findall(r'(\d+\.?\d*)', str(price_range))
                    if numbers:
                        # Берем максимальное число из диапазона (если есть "от 5 до 10", берем 10)
                        price_max_from_card = max([float(n) for n in numbers])
                    else:
                        price_max_from_card = price_from_card
                    
                    if price_max_from_card > price_to_millions:
                        continue
            
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
        
        # Сортировка по цене (используем price_range из карточки ЖК)
        if sort == 'price_asc':
            # Сортировка по возрастанию цены (дешевле) - используем price_range
            def get_price_from(record):
                development = {}
                if 'development' in record and 'avito' not in record:
                    development = record.get('development', {})
                else:
                    avito_dev = record.get('avito', {}).get('development', {}) if record.get('avito') else {}
                    development = avito_dev
                
                price_range = development.get('price_range', '')
                price_from_card = extract_price_from_range(price_range)
                
                if price_from_card > 0:
                    return float(price_from_card)
                # Если цена не найдена - в конец списка
                return float('inf')
            filtered_records.sort(key=get_price_from)
        elif sort == 'price_desc':
            # Сортировка по убыванию цены (дороже) - используем price_range
            def get_price_from(record):
                development = {}
                if 'development' in record and 'avito' not in record:
                    development = record.get('development', {})
                else:
                    avito_dev = record.get('avito', {}).get('development', {}) if record.get('avito') else {}
                    development = avito_dev
                
                price_range = development.get('price_range', '')
                price_from_card = extract_price_from_range(price_range)
                
                if price_from_card > 0:
                    return float(price_from_card)
                # Если цена не найдена - в конец списка
                return float('-inf')
            filtered_records.sort(key=get_price_from, reverse=True)
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
                    'is_future': record.get('is_future', False),  # Флаг будущего проекта
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


@require_http_methods(["GET"])
def apartments_api(request):
    """API для каталога квартир из всех ЖК с фильтрацией"""
    try:
        # Получаем параметры фильтрации
        page = int(request.GET.get('page', 1))
        try:
            per_page = int(request.GET.get('per_page', 15))
        except (TypeError, ValueError):
            per_page = 15
        
        # Фильтры местоположения
        city = request.GET.get('city', '').strip()
        district = request.GET.get('district', '').strip()
        street = request.GET.get('street', '').strip()
        
        # Обрабатываем множественные значения для district и street (через запятую)
        districts_list = [d.strip() for d in district.split(',') if d.strip()] if district else []
        streets_list = [s.strip() for s in street.split(',') if s.strip()] if street else []
        complexes_param = request.GET.get('complexes', '').strip()
        selected_complex_ids = []
        if complexes_param:
            try:
                selected_complex_ids = [ObjectId(cid.strip()) for cid in complexes_param.split(',') if cid.strip()]
            except Exception:
                selected_complex_ids = []
        
        # Фильтры недвижимости
        rooms = request.GET.get('rooms', '').strip()
        area_from = request.GET.get('area_from', '').strip()
        area_to = request.GET.get('area_to', '').strip()
        floor_from = request.GET.get('floor_from', '').strip()
        floor_to = request.GET.get('floor_to', '').strip()
        price_from = request.GET.get('price_from', '').strip()
        price_to = request.GET.get('price_to', '').strip()
        delivery_quarter = request.GET.get('delivery_quarter', '').strip()
        
        # Функция конвертации цены: если число >= 100, считаем что это рубли и конвертируем в миллионы
        def convert_price_to_millions(price_str):
            """Конвертирует цену в миллионы рублей.
            Если число >= 100, считаем что это рубли и делим на 1 000 000.
            Иначе считаем что это уже миллионы.
            """
            if not price_str:
                return None
            try:
                # Убираем пробелы и заменяем запятую на точку
                price_clean = price_str.replace(' ', '').replace(',', '.')
                price_val = float(price_clean)
                
                # Если число >= 100, считаем что это рубли, конвертируем в миллионы
                if price_val >= 100:
                    return price_val / 1_000_000
                # Иначе считаем что это уже миллионы
                return price_val
            except (ValueError, TypeError):
                return None
        
        # Конвертируем цены из фильтра в миллионы
        price_from_millions = convert_price_to_millions(price_from) if price_from else None
        price_to_millions = convert_price_to_millions(price_to) if price_to else None
        
        # Сортировка
        sort = request.GET.get('sort', 'price_asc')
        
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Преобразуем квартал в конечную дату для фильтрации
        delivery_date_limit = None
        if delivery_quarter:
            try:
                parts = delivery_quarter.split('_')
                if len(parts) == 2:
                    quarter = int(parts[0][1:])
                    year = int(parts[1])
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
        
        # Формируем фильтр для ЖК
        filter_query = {}
        if city:
            filter_query['$or'] = [
                {'address_city': city},
                {'city': city}
            ]
        if districts_list:
            district_filter = {
                '$or': [
                    {'address_district': {'$in': districts_list}},
                    {'district': {'$in': districts_list}}
                ]
            }
            if '$or' in filter_query:
                filter_query = {
                    '$and': [filter_query, district_filter]
                }
            else:
                filter_query.update(district_filter)
        if streets_list:
            street_filter = {
                '$or': [
                    {'address_street': {'$in': streets_list}},
                    {'street': {'$in': streets_list}}
                ]
            }
            if '$and' in filter_query:
                filter_query['$and'].append(street_filter)
            elif '$or' in filter_query:
                filter_query = {
                    '$and': [filter_query, street_filter]
                }
            else:
                filter_query.update(street_filter)
        
        if selected_complex_ids:
            filter_query['_id'] = {'$in': selected_complex_ids}
        
        # Получаем все ЖК
        all_complexes = list(unified_col.find(filter_query))
        
        # Собираем все квартиры из всех ЖК
        all_apartments = []
        
        for complex_record in all_complexes:
            # Определяем структуру записи
            is_new_structure = 'development' in complex_record and 'avito' not in complex_record
            
            # Получаем данные ЖК
            if is_new_structure:
                development = complex_record.get('development', {})
                name = development.get('name', 'Без названия')
                address = development.get('address', '')
                photos = development.get('photos', [])
                parameters = development.get('parameters', {})
                apartment_types = complex_record.get('apartment_types', {})
            else:
                avito_dev = complex_record.get('avito', {}).get('development', {}) if complex_record.get('avito') else {}
                name = avito_dev.get('name') or complex_record.get('domclick', {}).get('development', {}).get('complex_name', 'Без названия')
                address_full = avito_dev.get('address', '')
                address = address_full.split('/')[0].strip() if address_full else ''
                photos = complex_record.get('domclick', {}).get('development', {}).get('photos', [])
                parameters = avito_dev.get('parameters', {})
                apartment_types = complex_record.get('avito', {}).get('apartment_types', {})
            
            # Получаем город из записи ЖК
            complex_city = complex_record.get('city') or complex_record.get('address_city') or 'Уфа'
            
            # Получаем срок сдачи
            completion_date_str = parameters.get('Срок сдачи', '')
            
            # Проверяем срок сдачи для фильтрации
            if delivery_date_limit:
                if completion_date_str:
                    import re
                    patterns = re.findall(r'(\d+)\s*кв\.\s*(\d{4})', completion_date_str)
                    if patterns:
                        max_delivery_date = None
                        for quarter_str, year_str in patterns:
                            try:
                                quarter = int(quarter_str)
                                year = int(year_str)
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
                        if max_delivery_date and max_delivery_date > delivery_date_limit:
                            continue  # Пропускаем этот ЖК
            
            # Извлекаем квартиры из apartment_types
            for apt_type, apt_data in apartment_types.items():
                apartments = apt_data.get('apartments', [])
                for apt_index, apt in enumerate(apartments):
                    # Получаем данные квартиры
                    area = apt.get('area') or apt.get('square') or apt.get('totalArea')
                    title = apt.get('title', '')
                    if not area:
                        import re
                        area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                        if area_match:
                            area = area_match.group(1).replace(',', '.')
                    
                    # Фильтр по комнатам
                    if rooms:
                        selected_rooms = [r.strip() for r in rooms.split(',') if r.strip()]
                        if selected_rooms and apt_type not in selected_rooms:
                            continue
                    
                    # Фильтр по площади
                    if area:
                        try:
                            area_val = float(str(area))
                            if area_from:
                                try:
                                    if area_val < float(area_from):
                                        continue
                                except ValueError:
                                    pass
                            if area_to:
                                try:
                                    if area_val > float(area_to):
                                        continue
                                except ValueError:
                                    pass
                        except (ValueError, TypeError):
                            pass
                    
                    # Получаем цену (в базе формат: "3 905 000 ₽")
                    price = apt.get('price') or apt.get('price_value') or ''
                    price_num = None
                    if price:
                        import re
                        if isinstance(price, (int, float)):
                            # Если уже число, конвертируем в миллионы
                            price_num = float(price) / 1000000
                        else:
                            # Извлекаем все цифры из строки (убираем пробелы, символы валюты и т.д.)
                            price_str = str(price)
                            # Убираем все нецифровые символы, оставляем только цифры
                            digits_only = re.sub(r'\D', '', price_str)
                            if digits_only:
                                try:
                                    # Конвертируем в число и делим на 1 000 000 для получения миллионов
                                    price_num = float(digits_only) / 1000000
                                except (ValueError, TypeError):
                                    pass
                    
                    # Фильтр по цене (price_num уже в миллионах)
                    if price_from_millions is not None or price_to_millions is not None:
                        # Если фильтр по цене задан, но у квартиры нет цены - пропускаем её
                        if price_num is None:
                            continue
                        
                        # Фильтр "от X": квартира включается, если price_num >= price_from_millions
                        if price_from_millions is not None:
                            if price_num < price_from_millions:
                                continue
                        
                        # Фильтр "до Y": квартира включается, если price_num <= price_to_millions
                        if price_to_millions is not None:
                            if price_num > price_to_millions:
                                continue
                    
                    # Формируем ID квартиры для ссылки
                    apartment_id = apt.get('id')
                    if not apartment_id:
                        # Если ID нет, формируем из типа и индекса
                        apartment_id = f"{apt_type}_{apt_index}"
                    else:
                        # Если ID есть, проверяем формат
                        apartment_id_str = str(apartment_id)
                        # Если ID содержит complex_id, убираем его
                        if apartment_id_str.startswith(str(complex_record['_id'])):
                            parts = apartment_id_str.split('_')
                            if len(parts) >= 3:
                                apartment_id = f"{parts[1]}_{parts[2]}"
                        else:
                            apartment_id = apartment_id_str
                    
                    # Получаем фото планировки квартиры
                    # Приоритет: layout_photo > фото из массива image > первое фото ЖК
                    apartment_photo = None
                    # 1. Пытаемся взять из массива image (как в detail.html)
                    layout_photos = apt.get('image', [])
                    if isinstance(layout_photos, list) and layout_photos:
                        apartment_photo = layout_photos[0]
                    elif isinstance(layout_photos, str) and layout_photos:
                        apartment_photo = layout_photos
                    # 2. Если нет, пытаемся взять из photo/plan/layout
                    if not apartment_photo:
                        apartment_photo = apt.get('photo') or apt.get('plan') or apt.get('layout') or apt.get('layout_image')
                    # 3. Если всё ещё нет, берем первое фото ЖК
                    if not apartment_photo and photos:
                        apartment_photo = photos[0]
                    # 4. Если и этого нет, используем placeholder
                    if not apartment_photo:
                        apartment_photo = '/media/gallery/placeholders.png'
                    
                    # Формируем название квартиры
                    rooms_display = apt_type
                    if apt_type == 'Студия':
                        apartment_title = 'Студия'
                    elif apt_type == '1':
                        apartment_title = '1-комнатная квартира'
                    elif apt_type == '2':
                        apartment_title = '2-комнатная квартира'
                    elif apt_type == '3':
                        apartment_title = '3-комнатная квартира'
                    elif apt_type == '4':
                        apartment_title = '4-комнатная квартира'
                    elif apt_type == '5+':
                        apartment_title = '5+ комнат'
                    else:
                        apartment_title = f'{apt_type}-комнатная квартира'

                    # Получаем этаж из полей floorMin и floorMax (добавлены скриптом миграции)
                    floor_min = apt.get('floorMin')
                    floor_max = apt.get('floorMax')
                    
                    # Формируем floor_value для отображения
                    floor_value = None
                    if floor_min is not None and floor_max is not None:
                        if floor_min == floor_max:
                            floor_value = str(floor_min)
                        else:
                            floor_value = f"{floor_min}-{floor_max}"
                    elif floor_min is not None:
                        floor_value = str(floor_min)
                    elif floor_max is not None:
                        floor_value = str(floor_max)
                    
                    # Фильтр по этажам
                    # floorMin = этаж квартиры, floorMax = всего этажей в доме
                    # Фильтруем только по floorMin (этаж квартиры)
                    # "ОТ 5" = квартира на 5 этаже или выше
                    # "ДО 10" = квартира на 10 этаже или ниже
                    if floor_from or floor_to:
                        floor_passes_filter = False
                        
                        # Получаем значения фильтра
                        filter_min = None
                        filter_max = None
                        
                        try:
                            if floor_from:
                                filter_min = int(floor_from)
                        except (ValueError, TypeError):
                            pass
                        
                        try:
                            if floor_to:
                                filter_max = int(floor_to)
                        except (ValueError, TypeError):
                            pass
                        
                        # Используем только floor_min (этаж квартиры) для фильтрации
                        if floor_min is not None:
                            passes = True
                            if filter_min is not None and floor_min < filter_min:
                                passes = False
                            if filter_max is not None and floor_min > filter_max:
                                passes = False
                            floor_passes_filter = passes
                        else:
                            # Если этаж не указан у квартиры, пропускаем её при фильтрации по этажам
                            floor_passes_filter = False
                        
                        if not floor_passes_filter:
                            continue  # Пропускаем эту квартиру
                    
                    # Формируем карточку квартиры
                    apartment_card = {
                        'id': f"{str(complex_record['_id'])}_apt_{apartment_id}",
                        'apartment_id': apartment_id,
                        'complex_id': str(complex_record['_id']),
                        'complex_name': name,
                        'complex_address': address,
                        'address': address,  # Адрес ЖК для отображения в карточке
                        'city': complex_city,  # Город для отображения в карточке
                        'complex_photos': photos,
                        'rooms': apt_type,
                        'rooms_display': rooms_display,
                        'apartment_title': apartment_title,
                        'area': area,
                        'price': price,
                        'price_num': price_num,
                        'floor': floor_value or '',
                        'title': apt.get('title', ''),
                        'photo': apartment_photo,
                        'latitude': complex_record.get('latitude'),
                        'longitude': complex_record.get('longitude'),
                        'completion_date': completion_date_str,  # Срок сдачи
                    }
                    all_apartments.append(apartment_card)
        
        # Сортировка
        if sort == 'price_asc':
            # Сортировка по возрастанию: элементы с None идут в конец
            all_apartments.sort(key=lambda x: (
                x.get('price_num') is None,  # Сначала элементы с ценой (False), потом без (True)
                x.get('price_num') if x.get('price_num') is not None else float('inf')
            ))
        elif sort == 'price_desc':
            # Сортировка по убыванию: элементы с None идут в конец
            all_apartments.sort(key=lambda x: (
                x.get('price_num') is None,  # Сначала элементы с ценой (False), потом без (True)
                -(x.get('price_num') if x.get('price_num') is not None else 0)  # Отрицательное для reverse эффекта
            ))
        elif sort == 'area_desc':
            all_apartments.sort(key=lambda x: (x.get('area') is None or x.get('area') == '', -float(str(x.get('area', 0)).replace(',', '.')) if x.get('area') else 0), reverse=False)
        elif sort == 'area_asc':
            all_apartments.sort(key=lambda x: (x.get('area') is None or x.get('area') == '', float(str(x.get('area', float('inf'))).replace(',', '.')) if x.get('area') else float('inf')))
        
        # Для режима квартир возвращаем ВСЕ квартиры без пагинации
        # Пагинация будет происходить на фронтенде по группам
        total_count = len(all_apartments)
        apartments_data = all_apartments  # Возвращаем все квартиры
        
        # Собираем ВСЕ ЖК для карты
        # Это нужно чтобы показать все точки ЖК, как в режиме "ЖК"
        map_points_dict = {}
        # Проходим по ВСЕМ квартирам
        for apt in all_apartments:
            complex_id = apt.get('complex_id')
            if not complex_id or not apt.get('latitude') or not apt.get('longitude'):
                continue
            
            if complex_id not in map_points_dict:
                # Создаем точку для ЖК (точно как в catalog_api)
                map_points_dict[complex_id] = {
                    'id': complex_id,  # ID ЖК
                    'name': apt.get('complex_name', 'ЖК'),
                    'price_range': apt.get('price', 'Цена по запросу'),
                    'price_display': apt.get('price', 'Цена по запросу'),
                    'lat': apt['latitude'],
                    'lng': apt['longitude'],
                    'latitude': apt['latitude'],
                    'longitude': apt['longitude'],
                }
        
        # Преобразуем словарь в список
        map_points = list(map_points_dict.values())
        
        # Для режима квартир пагинация будет на фронтенде по группам
        # Возвращаем все квартиры, фронтенд сам будет группировать и пагинировать
        # total_pages будет пересчитан на фронтенде на основе количества групп
        total_pages = 1  # Временное значение, будет пересчитано на фронтенде
        
        return JsonResponse({
            'apartments': apartments_data,
            'map_points': map_points,
            'has_previous': False,  # Пагинация на фронтенде
            'has_next': False,  # Пагинация на фронтенде
            'current_page': page,  # Сохраняем для совместимости
            'total_pages': total_pages,  # Будет пересчитано на фронтенде
            'total_count': total_count
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'apartments': [],
            'map_points': [],
            'has_previous': False,
            'has_next': False,
            'current_page': 1,
            'total_pages': 0,
            'total_count': 0,
            'error': str(e)
        })


def complex_apartments_api(request, complex_id):
    """API для получения квартир конкретного ЖК с фильтрацией"""
    try:
        # Параметры фильтрации
        # Поддерживаем множественный выбор типов: type=1&type=2&type=Студия
        apt_types_list = request.GET.getlist('type')
        apt_type = request.GET.get('type')  # для обратной совместимости (одиночный)
        if apt_type and not apt_types_list:
            apt_types_list = [apt_type]
        area_from = request.GET.get('area_from')
        area_to = request.GET.get('area_to')
        floor_from = request.GET.get('floor_from')
        floor_to = request.GET.get('floor_to')
        price_from = request.GET.get('price_from')
        price_to = request.GET.get('price_to')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 6))
        
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем ЖК
        from bson import ObjectId
        try:
            complex_record = unified_col.find_one({'_id': ObjectId(complex_id)})
        except:
            complex_record = unified_col.find_one({'_id': complex_id})
        
        if not complex_record:
            return JsonResponse({'error': 'Complex not found', 'apartments': [], 'total_count': 0})
        
        # Получаем квартиры из структуры (логика как в detail view)
        apartment_types = {}
        
        # Проверяем структуру: новая (упрощенная) или старая (с вложенностью)
        is_new_structure = 'development' in complex_record and 'avito' not in complex_record
        
        if is_new_structure:
            # НОВАЯ СТРУКТУРА: apartment_types в корне записи
            apartment_types = complex_record.get('apartment_types', {})
        else:
            # СТАРАЯ СТРУКТУРА: apartment_types внутри avito
            avito_data = complex_record.get('avito', {})
            apartment_types = avito_data.get('apartment_types', {})
        
        filtered_apartments = []
        
        # Преобразуем фильтры в числа
        filter_floor_min = int(floor_from) if floor_from else None
        filter_floor_max = int(floor_to) if floor_to else None
        filter_price_min = float(price_from) if price_from else None
        filter_price_max = float(price_to) if price_to else None
        filter_area_min = float(area_from) if area_from else None
        filter_area_max = float(area_to) if area_to else None
        
        # Собираем квартиры
        for type_key, type_data in apartment_types.items():
            apartments = type_data.get('apartments', [])
            
            for apt_index, apt in enumerate(apartments):
                # Определяем тип квартиры
                apt_type_str = type_key
                if apt_type_str.lower() in ['студия', 'studio']:
                    apt_type_str = 'Студия'
                
                # Фильтр по типу
                if apt_types_list and apt_type_str not in apt_types_list:
                    continue
                
                # Получаем площадь
                area = apt.get('area') or apt.get('totalArea') or ''
                if not area:
                    title = apt.get('title', '')
                    if title:
                        import re
                        area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                        if area_match:
                            area = area_match.group(1).replace(',', '.')
                
                area_num = None
                if area:
                    try:
                        area_num = float(str(area).replace(',', '.'))
                    except ValueError:
                        pass
                
                # Фильтр по площади
                if filter_area_min is not None and area_num is not None:
                    if area_num < filter_area_min:
                        continue
                if filter_area_max is not None and area_num is not None:
                    if area_num > filter_area_max:
                        continue
                
                # Получаем этаж
                floor_min = apt.get('floorMin')
                floor_max = apt.get('floorMax')
                floor_value = apt.get('floor', '')
                
                # Если нет floorMin/floorMax, парсим из floor
                if floor_min is None and floor_max is None and floor_value:
                    import re
                    floor_str = str(floor_value)
                    range_match = re.match(r'(\d+)\s*[-–—]\s*(\d+)', floor_str)
                    if range_match:
                        floor_min = int(range_match.group(1))
                        floor_max = int(range_match.group(2))
                    else:
                        single_match = re.match(r'(\d+)', floor_str)
                        if single_match:
                            floor_min = floor_max = int(single_match.group(1))
                
                # Формируем floor_value для отображения
                if not floor_value and floor_min is not None:
                    if floor_max is not None and floor_min != floor_max:
                        floor_value = f"{floor_min}-{floor_max}"
                    else:
                        floor_value = str(floor_min)
                
                # Фильтр по этажу
                # floorMin = этаж квартиры, floorMax = всего этажей в доме
                # Фильтруем только по floorMin (этаж квартиры)
                # "от 5" → floorMin >= 5 (квартира на 5 этаже или выше)
                # "до 10" → floorMin <= 10 (квартира на 10 этаже или ниже)
                if filter_floor_min is not None or filter_floor_max is not None:
                    if floor_min is None:
                        # Нет данных об этаже - пропускаем
                        continue
                    
                    floor_passes = True
                    
                    # "от X": этаж квартиры >= X
                    if filter_floor_min is not None and floor_min < filter_floor_min:
                        floor_passes = False
                    
                    # "до Y": этаж квартиры <= Y
                    if filter_floor_max is not None and floor_min > filter_floor_max:
                        floor_passes = False
                    
                    if not floor_passes:
                        continue
                
                # Получаем цену
                price = apt.get('price') or ''
                price_num = None
                if price:
                    import re
                    if isinstance(price, (int, float)):
                        price_num = float(price)
                    else:
                        price_str = str(price)
                        digits_only = re.sub(r'\D', '', price_str)
                        if digits_only:
                            try:
                                price_num = float(digits_only)
                            except ValueError:
                                pass
                
                # Фильтр по цене
                if filter_price_min is not None or filter_price_max is not None:
                    if price_num is None:
                        continue
                    if filter_price_min is not None and price_num < filter_price_min:
                        continue
                    if filter_price_max is not None and price_num > filter_price_max:
                        continue
                
                # Получаем фото
                layout_photos = apt.get('image', [])
                if isinstance(layout_photos, dict):
                    layout_photos = [layout_photos.get('128x96', '')]
                elif isinstance(layout_photos, str):
                    layout_photos = [layout_photos] if layout_photos else []
                
                # Формируем данные квартиры
                apt_id = apt.get('_id') or f"{complex_id}_{type_key}_{apt_index}"
                
                filtered_apartments.append({
                    'id': str(apt_id),
                    'type': apt_type_str,
                    'title': apt.get('title', ''),
                    'price': price,
                    'price_num': price_num,
                    'area': area,
                    'area_num': area_num,
                    'floor': floor_value,
                    'floor_min': floor_min,
                    'floor_max': floor_max,
                    'layout_photos': layout_photos[:5] if layout_photos else [],
                    'rooms': apt.get('rooms', ''),
                    'completion_date': apt.get('completionDate', ''),
                })
        
        # Пагинация
        total_count = len(filtered_apartments)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        apartments_page = filtered_apartments[start_idx:end_idx]
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        
        return JsonResponse({
            'apartments': apartments_page,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': page < total_pages,
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'apartments': [],
            'total_count': 0,
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
                'floor': doc.get('floor') or doc.get('floor_number'),
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
    """API для получения районов по городу (поддерживает новостройки и вторичку)."""
    city = request.GET.get('city', '')
    dataset = request.GET.get('dataset', 'newbuild')
    if city:
        try:
            db = get_mongo_connection()
            if dataset == 'secondary':
                collection = db['secondary_properties']
                base_query = {'city': city}
                districts = collection.distinct('district', {**base_query, 'district': {'$ne': None, '$ne': ''}})
                alt_districts = collection.distinct(
                    'address_district',
                    {**base_query, 'address_district': {'$ne': None, '$ne': ''}}
                )
                districts = sorted({d for d in list(districts) + list(alt_districts) if d})
            else:
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
    """API для получения улиц по городу и району(ам) (новостройки и вторичка)."""
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')
    dataset = request.GET.get('dataset', 'newbuild')

    if city:
        try:
            db = get_mongo_connection()
            if dataset == 'secondary':
                collection = db['secondary_properties']
                
                base_query = {'city': city}
                if district:
                    districts_list = [d.strip() for d in district.split(',') if d.strip()]
                    if districts_list:
                        base_query['district'] = {'$in': districts_list}
                
                street_query = {**base_query, 'street': {'$ne': None, '$ne': ''}}
                streets_primary = collection.distinct('street', street_query)
                streets_alt = collection.distinct(
                    'address_street',
                    {**base_query, 'address_street': {'$ne': None, '$ne': ''}}
                )
                # Сортируем по алфавиту (case-insensitive для правильной сортировки)
                streets = sorted({s for s in list(streets_primary) + list(streets_alt) if s}, key=str.lower)
            else:
                collection = db['unified_houses']
                
                # Базовый запрос по городу
                base_query = {
                    '$or': [
                        {'address_city': city},
                        {'city': city}
                    ],
                    'address_street': {'$ne': None, '$ne': ''}
                }
                
                # Если указаны районы (может быть несколько через запятую)
                if district:
                    districts_list = [d.strip() for d in district.split(',') if d.strip()]
                    if districts_list:
                        # Фильтруем по нескольким районам используя $in
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
                                        {'address_district': {'$in': districts_list}},
                                        {'district': {'$in': districts_list}}
                                    ]
                                },
                                {'address_street': {'$ne': None, '$ne': ''}}
                            ]
                        }
                    else:
                        query = base_query
                else:
                    query = base_query
                    
                streets = collection.distinct('address_street', query)
                streets = [street for street in streets if street]
                # Сортируем по алфавиту (case-insensitive для правильной сортировки)
                streets = sorted(streets, key=str.lower)
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
