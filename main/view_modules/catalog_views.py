"""Views для каталога жилых комплексов и недвижимости"""
import json
import re
import sys
from datetime import datetime, date
from django.shortcuts import render
from django.http import Http404, JsonResponse
from django.core.paginator import Paginator
from bson import ObjectId
from ..services.mongo_service import get_mongo_connection, get_residential_complexes_from_mongo, get_unified_houses_from_mongo
from ..utils import get_video_thumbnail
from ..s3_service import PLACEHOLDER_IMAGE_URL


def parse_completion_date(completion_date_str):
    """Парсит строку срока сдачи вида '4 кв. 2017 — 2 кв. 2027' или '3 кв. 2024 – 3 кв. 2027'
    Возвращает максимальную дату (последний квартал)"""
    if not completion_date_str:
        return None
    
    import re
    # Ищем паттерны типа "4 кв. 2017" или "2 кв. 2027"
    patterns = re.findall(r'(\d+)\s*кв\.\s*(\d{4})', completion_date_str)
    
    if not patterns:
        return None
    
    # Берем максимальную дату (последний квартал в диапазоне)
    max_date = None
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
            
            if not max_date or end_date > max_date:
                max_date = end_date
        except (ValueError, TypeError):
            continue
    
    return max_date


def get_all_delivery_dates_from_db():
    """Получает все уникальные сроки сдачи из базы данных"""
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        all_records = list(unified_col.find({}))
        
        delivery_dates = set()
        
        for record in all_records:
            # Получаем срок сдачи из parameters
            completion_date_str = None
            
            if 'development' in record and 'avito' not in record:
                # Новая структура
                dev = record.get('development', {})
                parameters = dev.get('parameters', {})
                completion_date_str = parameters.get('Срок сдачи', '')
            else:
                # Старая структура
                avito_dev = record.get('avito', {}).get('development', {})
                if avito_dev:
                    parameters = avito_dev.get('parameters', {})
                    completion_date_str = parameters.get('Срок сдачи', '')
                
                if not completion_date_str:
                    domrf_dev = record.get('domrf', {}).get('development', {})
                    if domrf_dev:
                        parameters = domrf_dev.get('parameters', {})
                        completion_date_str = parameters.get('Срок сдачи', '')
            
            if completion_date_str:
                # Парсим срок сдачи и добавляем максимальную дату из диапазона
                parsed_date = parse_completion_date(completion_date_str)
                if parsed_date:
                    delivery_dates.add(parsed_date)
        
        return sorted(list(delivery_dates))
    except Exception as e:
        return []


def get_delivery_quarters():
    """Генерирует список кварталов на основе реальных данных из базы"""
    sys.stdout.flush()
    
    current_date = datetime.now().date()
    current_year = current_date.year
    current_month = current_date.month
    current_quarter = (current_month - 1) // 3 + 1
    
    sys.stdout.flush()
    
    sys.stdout.flush()
    
    # Получаем все уникальные сроки сдачи из базы
    all_delivery_dates = get_all_delivery_dates_from_db()
    
    sys.stdout.flush()
    
    # Создаем множество кварталов из всех дат
    quarters_set = set()
    
    for delivery_date in all_delivery_dates:
        # Пропускаем прошедшие даты
        if delivery_date < current_date:
            continue
        
        year = delivery_date.year
        month = delivery_date.month
        
        # Определяем квартал по месяцу
        if month <= 3:
            quarter = 1
        elif month <= 6:
            quarter = 2
        elif month <= 9:
            quarter = 3
        else:
            quarter = 4
        
        # Вычисляем последний день квартала
        if quarter == 1:
            end_date = date(year, 3, 31)
        elif quarter == 2:
            end_date = date(year, 6, 30)
        elif quarter == 3:
            end_date = date(year, 9, 30)
        else:  # quarter == 4
            end_date = date(year, 12, 31)
        
        quarters_set.add((year, quarter, end_date))
    
    # Преобразуем в список и сортируем
    quarters_list = []
    for year, quarter, end_date in sorted(quarters_set):
        value = f"Q{quarter}_{year}"
        label = f"До {quarter} квартала {year} года"
        
        quarters_list.append({
            'value': value,
            'label': label,
            'end_date': end_date,
            'year': year,
            'quarter': quarter
        })
    
    sys.stdout.flush()
    
    return quarters_list


def client_catalog(request):
    """Каталог квартир для клиентов - страница с выбранными квартирами"""
    # Проверяем, есть ли параметр selection_id (короткая ссылка)
    selection_id = request.GET.get('selection_id', '').strip()
    if selection_id:
        # Если есть selection_id, получаем подборку и формируем параметры
        from ..services.mongo_service import get_mongo_connection
        from bson import ObjectId
        
        try:
            db = get_mongo_connection()
            selections_col = db['apartment_selections']
            selection = selections_col.find_one({'_id': ObjectId(selection_id)})
            
            if selection:
                complexes = selection.get('complexes', [])
                complex_ids = []
                apartment_ids = []
                
                for comp in complexes:
                    complex_id = comp.get('complex_id', '')
                    if complex_id:
                        complex_ids.append(str(complex_id))
                        apt_ids = comp.get('apartment_ids', [])
                        for apt_id in apt_ids:
                            apartment_ids.append(f"{complex_id}_{apt_id}")
                
                # Формируем URL с параметрами
                from django.shortcuts import redirect
                complexes_param = ','.join(complex_ids)
                apartments_param = ','.join(apartment_ids)
                redirect_url = f"/client-catalog/?complexes={complexes_param}"
                if apartments_param:
                    redirect_url += f"&apartments={apartments_param}"
                return redirect(redirect_url)
        except Exception as e:
            # Если ошибка, просто показываем страницу без параметров
            pass
    
    return render(request, 'main/client_catalog.html')


def favorites(request):
    """Страница избранного"""
    return render(request, 'main/favorites.html')


def selection_view(request, selection_id):
    """Редирект на client-catalog с параметрами из подборки"""
    from django.shortcuts import redirect
    from ..services.mongo_service import get_mongo_connection
    from bson import ObjectId
    
    try:
        db = get_mongo_connection()
        selections_col = db['apartment_selections']
        selection = selections_col.find_one({'_id': ObjectId(selection_id)})
        
        if not selection:
            # Если подборка не найдена, редиректим на каталог
            return redirect('main:catalog')
        
        complexes = selection.get('complexes', [])
        complex_ids = []
        apartment_ids = []
        
        for comp in complexes:
            complex_id = comp.get('complex_id', '')
            if complex_id:
                # Убеждаемся, что complex_id - это строка
                complex_id_str = str(complex_id)
                complex_ids.append(complex_id_str)
                apt_ids = comp.get('apartment_ids', [])
                for apt_id in apt_ids:
                    # Формируем полный ID квартиры: complexId_apartmentId
                    # Если apt_id уже содержит complex_id, не дублируем
                    if apt_id.startswith(complex_id_str + '_'):
                        apartment_ids.append(apt_id)
                    else:
                        apartment_ids.append(f"{complex_id_str}_{apt_id}")
        
        # Формируем URL с параметрами
        from urllib.parse import urlencode
        params = {'complexes': ','.join(complex_ids), 'is_selection': 'true'}
        if apartment_ids:
            params['apartments'] = ','.join(apartment_ids)
        
        redirect_url = f"/client-catalog/?{urlencode(params)}"
        return redirect(redirect_url)
        
    except Exception as e:
        # Если ошибка, редиректим на каталог
        return redirect('main:catalog')


def format_currency(value):
    """Форматирует цену с пробелами и знаком ₽"""
    if value is None:
        return ''

    try:
        # Если число или строка с числом
        if isinstance(value, (int, float)):
            value_num = float(value)
        else:
            value_str = str(value).strip()
            if not value_str:
                return ''
            # Удаляем все символы валют и текста
            cleaned = re.sub(r'[^\d.,-]', '', value_str)
            cleaned = cleaned.replace(',', '.')
            value_num = float(cleaned)

        if value_num <= 0:
            return ''

        formatted = f"{value_num:,.0f}".replace(',', ' ')
        return f"{formatted} ₽"
    except Exception:
        # Если не получилось преобразовать, возвращаем исходное значение
        value_str = str(value).strip()
        if not value_str:
            return ''
        if '₽' in value_str:
            base = value_str.split('₽')[0].strip()
            return f"{base} ₽"
        return f"{value_str} ₽"


def format_currency_per_sqm(value):
    """Форматирует цену за м²"""
    formatted = format_currency(value)
    if not formatted:
        return ''
    # Удаляем конечный символ ₽ перед добавлением /м²
    if formatted.endswith(' ₽'):
        formatted = formatted[:-2].strip()
    elif formatted.endswith('₽'):
        formatted = formatted[:-1].strip()
    return f"{formatted} ₽/м²"


def get_complexes_list_for_filter():
    """Общая функция для получения списка ЖК для фильтра"""
    complexes_list = []
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        all_complexes = list(unified_col.find({}))
        
        for comp in all_complexes:
            comp_id = str(comp.get('_id'))
            name = None
            
            is_new_structure = 'development' in comp and 'avito' not in comp
            
            if is_new_structure:
                name = (comp.get('development', {}) or {}).get('name', '')
            else:
                avito_dev = (comp.get('avito', {}) or {}).get('development', {}) or {}
                domclick_dev = (comp.get('domclick', {}) or {}).get('development', {}) or {}
                name = avito_dev.get('name') or domclick_dev.get('complex_name') or ''
            
            if name and name.strip() and name != 'Без названия':
                complexes_list.append({'id': comp_id, 'name': name.strip()})
        
        # Удаляем дубликаты по названию
        seen_names = set()
        unique_complexes = []
        for comp in complexes_list:
            if comp['name'] not in seen_names:
                seen_names.add(comp['name'])
                unique_complexes.append(comp)
        
        complexes_list = sorted(unique_complexes, key=lambda x: x['name'])
    except Exception as e:
        import traceback
        traceback.print_exc()
        complexes_list = []
    
    return complexes_list


def catalog(request):
    """Каталог ЖК - теперь только рендерит шаблон, данные загружаются через API"""
    sys.stdout.flush()
    
    page = request.GET.get('page', 1)

    # Получаем параметры фильтрации для начального состояния формы
    rooms = request.GET.get('rooms', '')
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')
    street = request.GET.get('street', '')
    area_from = request.GET.get('area_from', '')
    area_to = request.GET.get('area_to', '')
    price_from = request.GET.get('price_from', '')
    price_to = request.GET.get('price_to', '')
    delivery_quarter = request.GET.get('delivery_quarter', '')
    has_offers = request.GET.get('has_offers', '')
    sort = request.GET.get('sort', 'price_asc')
    # Получаем выбранные ЖК (может быть несколько через запятую)
    selected_complexes = request.GET.get('complexes', '').strip()
    selected_complexes_list = [c.strip() for c in selected_complexes.split(',') if c.strip()] if selected_complexes else []
    selected_cities_list = [c.strip() for c in city.split(',') if c.strip()] if city else []
    selected_districts_list = [d.strip() for d in district.split(',') if d.strip()] if district else []
    selected_streets_list = [s.strip() for s in street.split(',') if s.strip()] if street else []
    selected_delivery_quarters_list = [q.strip() for q in delivery_quarter.split(',') if q.strip()] if delivery_quarter else []

    # Получаем уникальные города, районы и улицы для фильтра из MongoDB
    cities = []
    districts = []
    streets = []
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем уникальные города
        cities = unified_col.distinct('city', {'city': {'$ne': None, '$ne': ''}})
        cities = [city for city in cities if city]  # Убираем пустые значения
        
        
        # Фильтруем города: исключаем названия ЖК и комплексов
        def is_valid_city(city_name):
            if not city_name:
                return False
            city_str = str(city_name).strip()
            city_lower = city_str.lower()
            
            
            # Исключаем значения, начинающиеся с "ЖК" или содержащие паттерны названий комплексов
            # Проверяем начало строки на "жк" (с разными вариантами пробелов и кавычек)
            if city_lower.startswith('жк'):
                return False
            
            invalid_patterns = [
                'жк ',  # Содержит "ЖК " (с пробелом)
                'жк«',  # Содержит "ЖК«"
                'жк"',  # Содержит 'ЖК"'
                'жк «', # Содержит "ЖК «"
                'жк "', # Содержит 'ЖК "'
                'город природы',  # Специфичное название
                'жилой комплекс',
                'комплекс',
            ]
            
            for pattern in invalid_patterns:
                if pattern in city_lower:
                    return False
            
            return True
        
        cities_before = cities.copy()
        cities = [city for city in cities if is_valid_city(city)]
        cities_filtered_out = [city for city in cities_before if city not in cities]
        
        
        # Получаем уникальные районы
        districts = unified_col.distinct('district', {'district': {'$ne': None, '$ne': ''}})
        districts = [district for district in districts if district]
        
        # Получаем уникальные улицы
        streets = unified_col.distinct('street', {'street': {'$ne': None, '$ne': ''}})
        streets = [street for street in streets if street]
        
        # Сортируем списки
        cities = sorted(cities)
        districts = sorted(districts)
        streets = sorted(streets)
        
    except Exception as e:
        cities = []
        districts = []
        streets = []

    # Генерируем список кварталов для фильтра по сроку сдачи
    sys.stdout.flush()
    delivery_quarters = get_delivery_quarters()
    sys.stdout.flush()

    # Получаем список ЖК для фильтра по названиям
    complexes_list = get_complexes_list_for_filter()

    # Создаем пустые объекты для обратной совместимости с шаблоном
    class EmptyPaginator:
        num_pages = 0
    class EmptyPage:
        number = 1
        paginator = EmptyPaginator()
        has_previous = False
        has_next = False
        previous_page_number = 1
        next_page_number = 1

    page_obj = EmptyPage()

    context = {
        'complexes': [],  # Пустой список - карточки загружаются через API
        'page_obj': page_obj,
        'paginator': EmptyPaginator(),
        'cities': cities,
        'districts': districts,
        'streets': streets,
        'complexes_list': complexes_list,
        'rooms_choices': [('Студия', 'Студия'), ('1', '1-комнатная'), ('2', '2-комнатная'), ('3', '3-комнатная'), ('4', '4-комнатная'), ('5+', '5+ комнат')],
        'delivery_quarters': delivery_quarters,
        'filters': {
            'rooms': rooms,
            'city': city,
            'city_list': selected_cities_list,
            'district': district,
            'district_list': selected_districts_list,
            'street': street,
            'street_list': selected_streets_list,
            'area_from': area_from,
            'area_to': area_to,
            'price_from': price_from,
            'price_to': price_to,
            'delivery_quarter': delivery_quarter,
            'delivery_quarter_list': selected_delivery_quarters_list,
            'has_offers': has_offers,
            'sort': sort,
            'complexes': selected_complexes,
            'complexes_list': selected_complexes_list,
        },
        'filters_applied': False,
        'dataset_type': 'newbuild'
    }
    return render(request, 'main/catalog.html', context)


def detail(request, complex_id):
    """Детальная страница ЖК (MongoDB или SQL)"""
    
    # Получаем ипотечные программы из MongoDB (унифицировано)
    def get_mortgage_programs_from_mongo(complex_id=None):
        try:
            db = get_mongo_connection()
            # Получаем ВСЕ активные программы (и основные, и индивидуальные)
            all_docs = list(db['mortgage_programs'].find({'is_active': True}).sort('rate', 1))
            
            # Фильтруем программы для данного ЖК
            filtered_docs = []
            for doc in all_docs:
                is_individual = doc.get('is_individual', False)
                complexes = doc.get('complexes', [])
                
                # Если программа основная (не индивидуальная) - показываем всегда
                if not is_individual:
                    filtered_docs.append(doc)
                # Если программа индивидуальная - показываем только если она привязана к данному ЖК
                elif complex_id and ObjectId(complex_id) in complexes:
                    filtered_docs.append(doc)
            
            class P:
                def __init__(self, name, rate, is_individual=False):
                    self.name, self.rate, self.is_individual = name, rate, is_individual
            return [P(d.get('name',''), float(d.get('rate', 0)), d.get('is_individual', False)) for d in filtered_docs]
        except Exception:
            return []
    mortgage_programs = get_mortgage_programs_from_mongo(complex_id)
    
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
                address_raw = development.get('address', '')
                if address_raw:
                    address = address_raw.split('/')[0].strip()
                else:
                    # Формируем адрес из города и улицы, если есть
                    city = record.get('city', '') or development.get('city', '')
                    street = record.get('street', '') or development.get('street', '')
                    if city and street:
                        address = f"{street}, {city}"
                    elif street:
                        address = street
                    elif city:
                        address = city
                    else:
                        address = ''
                price_range = development.get('price_range', '')
                
                # Фото ЖК (исключаем фото из хода строительства)
                all_photos = development.get('photos', [])
                construction_progress = record.get('construction_progress', {})
                construction_photos = []
                
                # Собираем все фото из хода строительства
                if construction_progress:
                    if isinstance(construction_progress, list):
                        # Если это массив этапов
                        for stage in construction_progress:
                            if isinstance(stage, dict):
                                stage_photos = stage.get('photos', [])
                                if stage_photos:
                                    construction_photos.extend(stage_photos)
                    elif isinstance(construction_progress, dict):
                        # Если это объект с construction_stages
                        stages = construction_progress.get('construction_stages', [])
                        for stage in stages:
                            if isinstance(stage, dict):
                                stage_photos = stage.get('photos', [])
                                if stage_photos:
                                    construction_photos.extend(stage_photos)
                        # Или если это объект с photos напрямую
                        if not stages:
                            direct_photos = construction_progress.get('photos', [])
                            if direct_photos:
                                construction_photos.extend(direct_photos)
                
                # Исключаем фото хода строительства из фото ЖК
                photos = [p for p in all_photos if p not in construction_photos]
                
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
                address_raw = avito_dev.get('address', '') or domclick_dev.get('address', '')
                if address_raw:
                    address = address_raw.split('/')[0].strip()
                else:
                    # Формируем адрес из города и улицы, если есть
                    city = record.get('city', '') or avito_dev.get('city', '') or domclick_dev.get('city', '')
                    street = record.get('street', '') or avito_dev.get('street', '') or domclick_dev.get('street', '')
                    if city and street:
                        address = f"{street}, {city}"
                    elif street:
                        address = street
                    elif city:
                        address = city
                    else:
                        address = ''
                price_range = avito_dev.get('price_range', '')
                
                # Фото ЖК из domclick
                photos = domclick_dev.get('photos', [])
                
                # Координаты
                latitude = record.get('latitude') or domrf_data.get('latitude')
                longitude = record.get('longitude') or domrf_data.get('longitude')
                
                # Параметры ЖК
                parameters = avito_dev.get('parameters', {})
                korpuses = avito_dev.get('korpuses', [])
            
            # Обработка типов квартир в зависимости от структуры
            apartment_variants = []
            apartment_types_list = []
            
            if is_new_structure:
                # === НОВАЯ СТРУКТУРА: данные уже объединены ===
                
                for apt_type, apt_data in apartment_types_data.items():
                    apt_type_str = str(apt_type)
                    apartments = apt_data.get('apartments', [])
                    
                    if apartments:
                        if apt_type_str not in apartment_types_list:
                            apartment_types_list.append(apt_type_str)
                        
                        for apt_index, apt in enumerate(apartments):
                            # Получаем все фото планировки - это уже массив!
                            layout_photos = apt.get('image', [])
                            
                            # Если это не массив, а строка - преобразуем в массив
                            if isinstance(layout_photos, str):
                                layout_photos = [layout_photos] if layout_photos else []
                            
                            # Извлекаем площадь - сначала из отдельного поля, потом из title
                            area = apt.get('area') or apt.get('totalArea') or ''
                            if not area:
                                # Парсим из title если нет в отдельном поле
                                title = apt.get('title', '')
                                if title:
                                    import re
                                    area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                                    if area_match:
                                        area = area_match.group(1).replace(',', '.')
                            
                            # Генерируем уникальный ID если его нет
                            apt_id = apt.get('_id')
                            if not apt_id:
                                # Создаем уникальный ID на основе complex_id + тип + индекс
                                apt_id = f"{complex_id}_{apt_type_str}_{apt_index}"
                            
                            formatted_price = format_currency(apt.get('price', ''))
                            
                            # Получаем цену за м²
                            price_per_sqm_raw = apt.get('pricePerSquare', '') or apt.get('pricePerSqm', '')
                            
                            # Если цена за м² не указана, но есть цена и площадь, вычисляем
                            if not price_per_sqm_raw:
                                price_raw = apt.get('price', '')
                                area_raw = area
                                if price_raw and area_raw:
                                    try:
                                        price_str = str(price_raw).replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').strip()
                                        area_str = str(area_raw).replace(',', '.').strip()
                                        if price_str and area_str:
                                            price_num = float(price_str)
                                            area_num = float(area_str)
                                            if area_num > 0:
                                                price_per_sqm_raw = price_num / area_num
                                    except (ValueError, TypeError, ZeroDivisionError):
                                        pass
                            
                            formatted_price_per_sqm = format_currency_per_sqm(price_per_sqm_raw)
                            
                            # Получаем этаж из floorMin/floorMax (как в каталоге)
                            floor_min = apt.get('floorMin')
                            floor_max = apt.get('floorMax')
                            floor_value = apt.get('floor', '')
                            if not floor_value and (floor_min is not None or floor_max is not None):
                                if floor_min is not None and floor_max is not None:
                                    if floor_min == floor_max:
                                        floor_value = str(floor_min)
                                    else:
                                        floor_value = f"{floor_min}-{floor_max}"
                                elif floor_min is not None:
                                    floor_value = str(floor_min)
                                elif floor_max is not None:
                                    floor_value = str(floor_max)

                            apartment_variants.append({
                                'id': str(apt_id),  # Добавляем ID квартиры
                                'type': apt_type_str,
                                'title': apt.get('title', ''),
                                'price': apt.get('price', ''),
                                'price_per_square': apt.get('pricePerSquare', ''),
                                'formatted_price': formatted_price,
                                'formatted_price_per_sqm': formatted_price_per_sqm,
                                'completion_date': apt.get('completionDate', ''),
                                'image': layout_photos[0] if layout_photos else '',  # Первое фото для превью
                                'url': apt.get('url', ''),
                                'layout_photos': layout_photos,  # Все фото для галереи
                                '_id': apt.get('_id'),  # Сохраняем оригинальный _id
                                'rooms': apt.get('rooms', ''),
                                'area': area,  # Площадь из DomClick (приоритет над totalArea)
                                'totalArea': apt.get('totalArea', '') or area,  # Для совместимости
                                'floor': floor_value,
                                'pricePerSqm': apt.get('pricePerSqm', ''),
                                'layout': apt.get('layout', ''),
                                'balcony': apt.get('balcony', ''),
                                'loggia': apt.get('loggia', ''),
                                'view': apt.get('view', ''),
                                'condition': apt.get('condition', ''),
                                'furniture': apt.get('furniture', ''),
                                'ceilingHeight': apt.get('ceilingHeight', ''),
                                'windows': apt.get('windows', ''),
                                'bathroom': apt.get('bathroom', ''),
                                'kitchenArea': apt.get('kitchenArea', ''),
                                'livingArea': apt.get('livingArea', ''),
                                'bedroomArea': apt.get('bedroomArea', ''),
                                'photos': apt.get('photos', []),
                                'description': apt.get('description', ''),
                                'features': apt.get('features', [])
                            })
            
            else:
                # === СТАРАЯ СТРУКТУРА: нужно объединять данные ===
                avito_apartment_types = avito_data.get('apartment_types', {})
                domclick_apartment_types = domclick_data.get('apartment_types', {})
                
                for apt_type, apt_data in avito_apartment_types.items():
                    apt_type_str = str(apt_type)
                    apartments = apt_data.get('apartments', [])
                    
                    # Добавляем тип в список если есть квартиры
                    if apartments and apt_type_str not in apartment_types_list:
                        apartment_types_list.append(apt_type_str)
                    
                    # Получаем квартиры из DomClick для этого типа
                    dc_apartments = []
                    if apt_type in domclick_apartment_types:
                        dc_apartments = domclick_apartment_types[apt_type].get('apartments', [])
                    
                    for apt_index, apt in enumerate(apartments):
                        # Генерируем уникальный ID если его нет
                        apt_id = apt.get('_id')
                        if not apt_id:
                            # Создаем уникальный ID на основе complex_id + тип + индекс
                            apt_id = f"{complex_id}_{apt_type_str}_{apt_index}"
                        
                        # Извлекаем площадь - сначала из отдельного поля, потом из title
                        area = apt.get('area') or apt.get('totalArea') or ''
                        if not area:
                            # Парсим из title если нет в отдельном поле
                            title = apt.get('title', '')
                            if title:
                                import re
                                area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                                if area_match:
                                    area = area_match.group(1).replace(',', '.')
                        
                        # Ищем соответствующую квартиру из DomClick по площади
                        # Берем фото только из соответствующей квартиры, а не из всех
                        layout_photos = []
                        if dc_apartments and area:
                            try:
                                area_float = float(area)
                                # Ищем квартиру с наиболее близкой площадью
                                best_match = None
                                min_diff = float('inf')
                                for dc_apt in dc_apartments:
                                    dc_title = dc_apt.get('title', '')
                                    if dc_title:
                                        import re
                                        dc_area_match = re.search(r'(\d+[,.]?\d*)\s*м²', dc_title)
                                        if dc_area_match:
                                            dc_area = float(dc_area_match.group(1).replace(',', '.'))
                                            diff = abs(area_float - dc_area)
                                            if diff < min_diff and diff < 1.0:  # Разница меньше 1 м²
                                                min_diff = diff
                                                best_match = dc_apt
                                
                                if best_match:
                                    layout_photos = best_match.get('photos', [])
                            except (ValueError, AttributeError):
                                pass
                        
                        # Если не нашли совпадение - берем первые фото из всех (fallback)
                        if not layout_photos and dc_apartments:
                            for dc_apt in dc_apartments[:1]:  # Берем только первую квартиру
                                layout_photos = dc_apt.get('photos', [])[:5]
                                break
                        
                        formatted_price = format_currency(apt.get('price', ''))
                        
                        # Получаем цену за м²
                        price_per_sqm_raw = apt.get('pricePerSquare', '') or apt.get('pricePerSqm', '')
                        
                        # Если цена за м² не указана, но есть цена и площадь, вычисляем
                        if not price_per_sqm_raw:
                            price_raw = apt.get('price', '')
                            area_raw = area
                            if price_raw and area_raw:
                                try:
                                    price_str = str(price_raw).replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').strip()
                                    area_str = str(area_raw).replace(',', '.').strip()
                                    if price_str and area_str:
                                        price_num = float(price_str)
                                        area_num = float(area_str)
                                        if area_num > 0:
                                            price_per_sqm_raw = price_num / area_num
                                except (ValueError, TypeError, ZeroDivisionError):
                                    pass
                        
                        formatted_price_per_sqm = format_currency_per_sqm(price_per_sqm_raw)
                        
                        # Получаем этаж из floorMin/floorMax (как в каталоге)
                        floor_min = apt.get('floorMin')
                        floor_max = apt.get('floorMax')
                        floor_value = apt.get('floor', '')
                        if not floor_value and (floor_min is not None or floor_max is not None):
                            if floor_min is not None and floor_max is not None:
                                if floor_min == floor_max:
                                    floor_value = str(floor_min)
                                else:
                                    floor_value = f"{floor_min}-{floor_max}"
                            elif floor_min is not None:
                                floor_value = str(floor_min)
                            elif floor_max is not None:
                                floor_value = str(floor_max)

                        apartment_variants.append({
                            'id': str(apt_id),  # Добавляем ID квартиры
                            'type': apt_type_str,
                            'title': apt.get('title', ''),
                            'price': apt.get('price', ''),
                            'price_per_square': apt.get('pricePerSquare', ''),
                            'formatted_price': formatted_price,
                            'formatted_price_per_sqm': formatted_price_per_sqm,
                            'completion_date': apt.get('completionDate', ''),
                            'image': apt.get('image', {}).get('128x96', ''),
                            'url': apt.get('urlPath', ''),
                            'layout_photos': layout_photos[:5],  # Фото из соответствующей квартиры DomClick
                            '_id': apt.get('_id'),  # Сохраняем оригинальный _id
                            'rooms': apt.get('rooms', ''),
                            'area': area,  # Площадь из DomClick (приоритет над totalArea)
                            'totalArea': apt.get('totalArea', '') or area,  # Для совместимости
                            'floor': floor_value,
                            'pricePerSqm': apt.get('pricePerSqm', ''),
                            'layout': apt.get('layout', ''),
                            'balcony': apt.get('balcony', ''),
                            'loggia': apt.get('loggia', ''),
                            'view': apt.get('view', ''),
                            'condition': apt.get('condition', ''),
                            'furniture': apt.get('furniture', ''),
                            'ceilingHeight': apt.get('ceilingHeight', ''),
                            'windows': apt.get('windows', ''),
                            'bathroom': apt.get('bathroom', ''),
                            'kitchenArea': apt.get('kitchenArea', ''),
                            'livingArea': apt.get('livingArea', ''),
                            'bedroomArea': apt.get('bedroomArea', ''),
                            'photos': apt.get('photos', []),
                            'description': apt.get('description', ''),
                            'features': apt.get('features', [])
                        })
            # Группируем квартиры по типам для удобного отображения
            apartment_variants_grouped = {}
            for apt in apartment_variants:
                apt_type_key = str(apt.get('type', ''))
                if apt_type_key not in apartment_variants_grouped:
                    apartment_variants_grouped[apt_type_key] = []
                apartment_variants_grouped[apt_type_key].append(apt)
            
            # Удаляем дубли из списка типов
            unique_types = []
            for apt_type in apartment_types_list:
                apt_type_str = str(apt_type).strip()
                if apt_type_str and apt_type_str not in unique_types:
                    unique_types.append(apt_type_str)

            def sort_key(value: str):
                val = value.strip().lower()
                studio_aliases = {'студия', 'studio', 'студии'}
                if val in studio_aliases:
                    return (0, 0)

                # Значения вида "5+" считаем большим числом с бонусом
                if val.endswith('+') and val[:-1].isdigit():
                    return (2, int(val[:-1]), 1)

                # Чисто числовые значения
                if val.isdigit():
                    return (1, int(val), 0)

                # Пытаемся извлечь число из форматов "2-комн." и т.п.
                import re
                match = re.match(r'(\d+)', val)
                if match:
                    return (1, int(match.group(1)), 0)

                # Всё остальное оставляем в конце по алфавиту
                return (3, value)

            # Фильтруем список типов: оставляем только те, для которых есть квартиры
            apartment_types_list = []
            for apt_type in unique_types:
                apt_type_str = str(apt_type).strip()
                # Проверяем, есть ли квартиры для этого типа
                if apt_type_str in apartment_variants_grouped and apartment_variants_grouped[apt_type_str]:
                    apartment_types_list.append(apt_type_str)
            
            # Сортируем только те типы, для которых есть квартиры
            apartment_types_list = sorted(apartment_types_list, key=sort_key)
            
            # Формируем контекст для MongoDB версии
            # Получаем акции для этого ЖК
            complex_offers = []
            try:
                promotions_col = db['promotions']
                offers_data = list(promotions_col.find({
                    'complex_id': ObjectId(complex_id),
                    'is_active': True
                }).sort('created_at', -1))
                
                # Создаем адаптеры для совместимости с шаблонами
                for offer_data in offers_data:
                    class _Img: pass
                    class _MainImg: pass
                    class _RC: pass
                    class _Offer: pass
                    
                    offer = _Offer()
                    offer.id = str(offer_data.get('_id'))
                    offer.title = offer_data.get('title', 'Акция')
                    # Убираем описание
                    offer.description = ''
                    offer.expires_at = offer_data.get('expires_at')
                    
                    # residential_complex.name
                    rc = _RC()
                    rc.name = name  # Используем название ЖК из записи
                    offer.residential_complex = rc
                    
                    # get_main_image.image.url - правильная обработка S3 и локальных URL
                    main = _MainImg()
                    img = _Img()
                    # Берем первое фото из ЖК для акции
                    if photos:
                        photo_url = photos[0]
                        # Проверяем, является ли URL уже полным (S3)
                        if photo_url.startswith('http://') or photo_url.startswith('https://'):
                            img.url = photo_url
                        else:
                            img.url = '/media/' + photo_url if not photo_url.startswith('/media/') else photo_url
                    else:
                        img.url = PLACEHOLDER_IMAGE_URL
                    main.image = img
                    offer.get_main_image = main
                    
                    complex_offers.append(offer)
            except Exception as e:
                complex_offers = []
            
            # Получаем видеообзоры для этого ЖК
            videos = []
            try:
                videos_col = db['residential_videos']
                videos_data = list(videos_col.find({
                    'complex_id': ObjectId(complex_id)
                }).sort('created_at', -1))
                
                # Создаем адаптеры для совместимости с шаблонами
                for video_data in videos_data:
                    class _Video: pass
                    video = _Video()
                    video.id = str(video_data.get('_id'))
                    video.title = video_data.get('title', '')
                    video.video_url = video_data.get('url', '')
                    video.created_at = video_data.get('created_at')
                    # Добавляем превью для видео
                    video.thumbnail_url = get_video_thumbnail(video_data.get('url', ''))
                    videos.append(video)
            except Exception as e:
                videos = []

            # Нормализуем формат хода строительства перед передачей в шаблон
            # Шаблон ожидает объект с construction_stages, а не массив
            # Также добавляем stage_number для каждого этапа
            construction_progress_raw = record.get('construction_progress', {})
            if isinstance(construction_progress_raw, list):
                # Если это массив этапов, оборачиваем в объект с construction_stages
                # И добавляем stage_number для каждого этапа
                normalized_stages = []
                for idx, stage in enumerate(construction_progress_raw):
                    if isinstance(stage, dict):
                        normalized_stage = stage.copy()
                        # Добавляем stage_number если его нет
                        if 'stage_number' not in normalized_stage:
                            normalized_stage['stage_number'] = idx + 1
                        # Убеждаемся, что есть date
                        if 'date' not in normalized_stage:
                            normalized_stage['date'] = normalized_stage.get('stage', '')
                        normalized_stages.append(normalized_stage)
                    else:
                        # Если этап не словарь, создаем словарь
                        normalized_stages.append({
                            'stage_number': idx + 1,
                            'date': '',
                            'photos': []
                        })
                construction_progress = {'construction_stages': normalized_stages}
            elif isinstance(construction_progress_raw, dict) and 'construction_stages' in construction_progress_raw:
                # Если это уже объект с construction_stages, добавляем stage_number если его нет
                stages = construction_progress_raw.get('construction_stages', [])
                normalized_stages = []
                for idx, stage in enumerate(stages):
                    if isinstance(stage, dict):
                        normalized_stage = stage.copy()
                        # Добавляем stage_number если его нет
                        if 'stage_number' not in normalized_stage:
                            normalized_stage['stage_number'] = idx + 1
                        # Убеждаемся, что есть date
                        if 'date' not in normalized_stage:
                            normalized_stage['date'] = normalized_stage.get('stage', '')
                        normalized_stages.append(normalized_stage)
                    else:
                        normalized_stages.append({
                            'stage_number': idx + 1,
                            'date': '',
                            'photos': []
                        })
                construction_progress = {'construction_stages': normalized_stages}
            elif isinstance(construction_progress_raw, dict) and construction_progress_raw:
                # Если это объект без construction_stages, пытаемся создать этап из photos
                direct_photos = construction_progress_raw.get('photos', [])
                if direct_photos:
                    construction_progress = {
                        'construction_stages': [{
                            'stage_number': 1,
                            'stage': 'Строительство',
                            'date': construction_progress_raw.get('date', ''),
                            'photos': direct_photos
                        }]
                    }
                else:
                    construction_progress = {}
            else:
                construction_progress = {}

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
                    'apartment_variants_grouped': apartment_variants_grouped,
                    'apartment_variants_json': json.dumps(apartment_variants),
                    'apartment_types': apartment_types_list,
                    'total_apartments': avito_data.get('total_apartments', 0),
                    'avito_url': avito_data.get('url', ''),
                    'domclick_url': domclick_data.get('url', ''),
                    # Ход строительства из объединенной записи (нормализованный формат)
                    'construction_progress': construction_progress,
                },
                'complex_offers': complex_offers,
                'videos': videos,
                'mortgage_programs': mortgage_programs,
                'is_mongodb': True,
                'is_secondary': False,
            }
            
            # Подтягиваем данные агента, если закреплен
            agent = None
            if record.get('agent_id'):
                try:
                    agent = db['employees'].find_one({'_id': record['agent_id'], 'is_active': True})
                    if agent:
                        agent['id'] = str(agent.get('_id'))
                except Exception:
                    agent = None
            context['agent'] = agent
            
            # Логируем данные, передаваемые в шаблон
            import logging
            logger = logging.getLogger(__name__)
            
            
            # Логируем development.photos
            development = context['complex'].get('development', {})
            dev_photos = development.get('photos', [])
            
            
            return render(request, 'main/detail.html', context)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Http404(f"Ошибка загрузки ЖК: {str(e)}")
    
    else:
        # Для числовых ID возвращаем 404, так как все данные теперь в MongoDB
        raise Http404("ЖК не найден. Используйте MongoDB ID.")


def secondary_detail_mongo(request, complex_id: str):
    """Детальная страница объекта вторичной недвижимости из MongoDB"""
    try:
        from bson import ObjectId
        
        # Подключение к MongoDB
        db = get_mongo_connection()
        collection = db['secondary_properties']
        
        # Получаем объект по ID
        obj_id = ObjectId(complex_id)
        doc = collection.find_one({'_id': obj_id})
        
        if not doc:
            raise Http404("Объект не найден")
        
        # Подтягиваем агента, если закреплен
        agent = None
        if doc.get('agent_id'):
            try:
                agent = db['employees'].find_one({'_id': doc['agent_id'], 'is_active': True})
            except Exception:
                agent = None

        # Создаем адаптер для совместимости с шаблоном
        class SecondaryAdapter:
            def __init__(self, data):
                self._data = data
                self.id = str(data.get('_id')) if data.get('_id') else ''
                self.name = data.get('name', '')
                self.price_from = data.get('price', 0)
                self.city = data.get('city', '')
                self.district = data.get('district', '')
                self.street = data.get('street', '')
                # Формируем адрес из улицы и города, или используем поле address если есть
                address_raw = data.get('address', '')
                if address_raw:
                    self.address = address_raw.split('/')[0].strip() if '/' in address_raw else address_raw.strip()
                elif data.get('street') or data.get('city'):
                    street = data.get('street', '')
                    city = data.get('city', '')
                    if street and city:
                        self.address = f"{street}, {city}"
                    elif street:
                        self.address = street
                    elif city:
                        self.address = city
                    else:
                        self.address = ''
                else:
                    self.address = ''
                self.commute_time = data.get('commute_time', '')
                self.area_from = data.get('area', 0)
                self.area_to = data.get('area', 0)
                self.developer = 'Собственник'
                self.total_apartments = 1  # Для совместимости с шаблоном
                self.completion_start = ''
                self.completion_end = ''
                self.has_completed = True
                self.get_house_class_display = lambda: ''
                self.get_house_type_display = lambda: self._get_house_type_display()
                self.get_finishing_display = lambda: self._get_finishing_display()
                self.description = data.get('description', '')
                self.photos = data.get('photos', [])
                self.rooms = data.get('rooms', '')
                self.total_floors = data.get('total_floors', '')
                self.finishing = data.get('finishing', '')
                
            def _get_house_type_display(self):
                house_type = self._data.get('house_type', '')
                house_types = {
                    'apartment': 'Квартира',
                    'house': 'Дом',
                    'cottage': 'Коттедж',
                    'townhouse': 'Таунхаус',
                    'commercial': 'Коммерческое помещение',
                    'room': 'Комната',
                    'studio': 'Студия'
                }
                return house_types.get(house_type, house_type)
            
            def _get_finishing_display(self):
                finishing = self._data.get('finishing', '')
                finishing_types = {
                    'without': 'Без отделки',
                    'rough': 'Черновая отделка',
                    'white_box': 'Белая коробка',
                    'full': 'Полная отделка',
                    'designer': 'Дизайнерская отделка'
                }
                return finishing_types.get(finishing, finishing)
            
            def get_main_image(self):
                if self.photos:
                    class ImageAdapter:
                        def __init__(self, photo_path):
                            self.image = type('obj', (object,), {'url': photo_path})()
                    return ImageAdapter(self.photos[0])
                return None
            
            def get_all_images(self):
                return self.photos
            
            def get_catalog_images(self):
                # Возвращаем адаптеры для всех фото для совместимости с шаблоном
                if not self.photos:
                    return []
                
                class CatalogImageAdapter:
                    def __init__(self, photo_path):
                        self.image = type('obj', (object,), {'url': photo_path})()
                
                return [CatalogImageAdapter(photo) for photo in self.photos]
            
            def get_videos(self):
                return []  # Вторичка не имеет видео
        
        complex_obj = SecondaryAdapter(doc)
        
        # Получаем похожие объекты (первые 3 из той же категории)
        similar_filter = {}
        if doc.get('rooms'):
            similar_filter['rooms'] = doc['rooms']
        if doc.get('city'):
            similar_filter['city'] = doc['city']
        
        similar_cursor = collection.find(similar_filter).limit(3)
        similar_objects = []
        for similar_doc in similar_cursor:
            if str(similar_doc['_id']) != complex_id:  # Исключаем текущий объект
                similar_objects.append(SecondaryAdapter(similar_doc))

        return render(request, 'main/detail.html', {
            'complex': complex_obj,
            'similar_complexes': similar_objects,
        'is_secondary': True,
        'mortgage_programs': [],
            'videos': [],
            'agent': agent,
        })
    except Exception as e:
        raise Http404(f"Ошибка загрузки объекта: {str(e)}")


def secondary_detail(request, pk: int):
    """Legacy функция - перенаправляет на MongoDB версию"""
    raise Http404("Используйте MongoDB ID для просмотра объектов вторичной недвижимости")


# Быстрые ссылки каталога
def catalog_completed(request):
    """Сданные ЖК - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'status': 'completed'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'complexes_list': complexes_list,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Сданные ЖК',
        'page_description': 'Готовые к заселению жилые комплексы'
    }
    return render(request, 'main/catalog.html', context)


def catalog_construction(request):
    """Строящиеся ЖК - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'status': 'construction'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'complexes_list': complexes_list,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Строящиеся ЖК',
        'page_description': 'Жилые комплексы в стадии строительства'
    }
    return render(request, 'main/catalog.html', context)


def catalog_economy(request):
    """Эконом-класс - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'house_class': 'economy'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'complexes_list': complexes_list,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Эконом-класс',
        'page_description': 'Доступное жилье эконом-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_comfort(request):
    """Комфорт-класс - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'house_class': 'comfort'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'complexes_list': complexes_list,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Комфорт-класс',
        'page_description': 'Жилые комплексы комфорт-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_premium(request):
    """Премиум-класс - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'house_class': 'premium'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'complexes_list': complexes_list,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Премиум-класс',
        'page_description': 'Жилые комплексы премиум-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_finished(request):
    """С отделкой - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'finishing': 'finished'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'complexes_list': complexes_list,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'С отделкой',
        'page_description': 'Квартиры с готовой отделкой'
    }
    return render(request, 'main/catalog.html', context)


def catalog_unfinished(request):
    """Без отделки - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'finishing': 'unfinished'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'complexes_list': complexes_list,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Без отделки',
        'page_description': 'Квартиры без отделки'
    }
    return render(request, 'main/catalog.html', context)


def catalog_landing(request, slug):
    db = get_mongo_connection()
    landing = db['catalog_landings'].find_one({'slug': slug, 'is_active': True})
    
    if not landing:
        raise Http404("Страница не найдена")

    # Базовый queryset в зависимости от типа
    if landing['kind'] == 'secondary':
        queryset = []
    else:
        # Для новостроек получаем данные из MongoDB
        filters = {'status': 'construction'}
        queryset = get_residential_complexes_from_mongo(filters=filters)

    # Категории
    category_map = {
        'apartment': 'apartment',
        'house': 'house',
        'cottage': 'cottage',
        'townhouse': 'townhouse',
        'commercial': None,
        'all': None,
    }
    house_type = category_map.get(landing['category'])
    if house_type:
        if landing['kind'] == 'secondary':
            pass
        else:
            queryset = queryset.filter(house_type=house_type)

    paginator = Paginator(queryset, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    categories = list(db['catalog_landings'].find({'kind': landing['kind'], 'is_active': True}).sort('name', 1))

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()
    
    landing_kind = 'secondary' if landing.get('kind') == 'secondary' else 'newbuild'
    cities, districts, streets = _get_location_lists(landing_kind)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': cities,
        'districts': districts,
        'streets': streets,
        'complexes_list': complexes_list,
        'rooms_choices': [('Студия', 'Студия'), ('1', '1-комнатная'), ('2', '2-комнатная'), ('3', '3-комнатная'), ('4', '4-комнатная'), ('5+', '5+ комнат')],
        'filters': {},
        'filters_applied': True,
        'page_title': landing.get('name', ''),
        'page_description': landing.get('meta_description') or landing.get('name', ''),
        'landing': landing,
        'landing_categories': categories,
        'dataset_type': landing_kind,
    }

    return render(request, 'main/catalog.html', context)


def _get_location_lists(kind: str):
    """Возвращает списки городов, районов и улиц для конкретного вида каталога."""
    cities = []
    districts = []
    streets = []
    try:
        db = get_mongo_connection()
        if kind == 'newbuild':
            collection = db['unified_houses']
        elif kind == 'secondary':
            collection = db['secondary_properties']
        else:
            return cities, districts, streets
        
        # Получаем уникальные города
        cities = collection.distinct('city', {'city': {'$ne': None, '$ne': ''}})
        cities = [city for city in cities if city]  # Убираем пустые значения
        
        
        # Фильтруем города: исключаем названия ЖК и комплексов
        def is_valid_city(city_name):
            if not city_name:
                return False
            city_str = str(city_name).strip()
            city_lower = city_str.lower()
            
            
            # Исключаем значения, начинающиеся с "ЖК" или содержащие паттерны названий комплексов
            # Проверяем начало строки на "жк" (с разными вариантами пробелов и кавычек)
            if city_lower.startswith('жк'):
                return False
            
            invalid_patterns = [
                'жк ',  # Содержит "ЖК " (с пробелом)
                'жк«',  # Содержит "ЖК«"
                'жк"',  # Содержит 'ЖК"'
                'жк «', # Содержит "ЖК «"
                'жк "', # Содержит 'ЖК "'
                'город природы',  # Специфичное название
                'жилой комплекс',
                'комплекс',
            ]
            
            for pattern in invalid_patterns:
                if pattern in city_lower:
                    return False
            
            return True
        
        cities_before = cities.copy()
        cities = [city for city in cities if is_valid_city(city)]
        cities_filtered_out = [city for city in cities_before if city not in cities]
        
        
        districts = collection.distinct('district', {'district': {'$ne': None, '$ne': ''}})
        districts = sorted([district for district in districts if district])
        streets = collection.distinct('street', {'street': {'$ne': None, '$ne': ''}})
        streets = sorted([street for street in streets if street])
    except Exception as exc:
        cities, districts, streets = [], [], []
    return cities, districts, streets


def _catalog_fallback(request, kind: str, title: str):
    """Рендер каталога без необходимости иметь запись CatalogLanding.
    kind: 'newbuild'|'secondary'
    """
    sys.stdout.flush()
    
    if kind == 'secondary':
        queryset = []
    else:
        # Для новостроек получаем данные из MongoDB
        filters = {'status': 'construction'}
        queryset = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(queryset, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Получаем города, районы и улицы в зависимости от типа каталога
    cities, districts, streets = _get_location_lists(kind)

    # Получаем список ЖК для фильтра
    complexes_list = get_complexes_list_for_filter()
    
    # Генерируем список кварталов для фильтра по сроку сдачи (только для новостроек)
    delivery_quarters = []
    if kind == 'newbuild':
        sys.stdout.flush()
        delivery_quarters = get_delivery_quarters()
        sys.stdout.flush()

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': cities,
        'districts': districts,
        'streets': streets,
        'complexes_list': complexes_list,
        'rooms_choices': [('Студия', 'Студия'), ('1', '1-комнатная'), ('2', '2-комнатная'), ('3', '3-комнатная'), ('4', '4-комнатная'), ('5+', '5+ комнат')],
        'delivery_quarters': delivery_quarters,
        'filters': ({'stype': request.GET.get('stype', '')} if kind == 'secondary' else {}),
        'filters_applied': True,
        'page_title': title,
        'page_description': title,
        'landing': None,
        'landing_categories': [],
        'dataset_type': kind,
    }
    return render(request, 'main/catalog.html', context)


def newbuild_index(request):
    # Стартовая страница новостроек - читает из MongoDB
    sys.stdout.flush()
    
    db = get_mongo_connection()
    landing = db['catalog_landings'].find_one({'kind': 'newbuild', 'category': 'all', 'is_active': True})
    if landing:
        sys.stdout.flush()
        return catalog_landing(request, slug=landing['slug'])
    
    sys.stdout.flush()
    return _catalog_fallback(request, kind='newbuild', title='Новостройки')


def secondary_index(request):
    # Стартовая страница вторички - читает из MongoDB
    db = get_mongo_connection()
    landing = db['catalog_landings'].find_one({'kind': 'secondary', 'category': 'all', 'is_active': True})
    if landing:
        return catalog_landing(request, slug=landing['slug'])
    return _catalog_fallback(request, kind='secondary', title='Вторичная недвижимость')

