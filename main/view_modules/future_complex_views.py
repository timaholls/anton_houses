"""Views для будущих жилых комплексов"""
import re
from django.shortcuts import render
from django.http import Http404
from django.core.paginator import Paginator
from bson import ObjectId
from ..services.mongo_service import get_mongo_connection, get_future_complexes_from_mongo


def future_complexes(request):
    """Страница будущих ЖК"""
    # Получаем параметры фильтрации
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')
    price_from = request.GET.get('price_from', '')
    price_to = request.GET.get('price_to', '')
    delivery_date = request.GET.get('delivery_date', '')
    sort = request.GET.get('sort', 'delivery_date_asc')

    # Получаем данные из MongoDB
    filters = {}
    if city:
        filters['city'] = city
    if district:
        filters['district'] = district
    if price_from:
        filters['price_from'] = price_from
    if price_to:
        filters['price_to'] = price_to
    if delivery_date:
        filters['delivery_date'] = delivery_date
    
    complexes = get_future_complexes_from_mongo(filters=filters, sort_by=sort)

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
    """Детальная страница будущего ЖК - данные из unified_houses"""
    try:
        db = get_mongo_connection()
        collection = db['unified_houses']
        complex = collection.find_one({'_id': ObjectId(complex_id), 'is_future': True})
        if not complex:
            raise Http404("ЖК не найден")
    except Exception:
        raise Http404("ЖК не найден")

    # Получаем данные из development
    dev = complex.get('development', {})
    parameters = dev.get('parameters', {})
    
    # Получаем изображения ЖК из development.photos
    images = dev.get('photos', [])

    # Преобразуем _id в строку для использования в шаблонах
    if '_id' in complex:
        complex['id'] = str(complex['_id'])
    
    # Адаптируем формат для шаблона
    complex['name'] = dev.get('name', 'Без названия')
    complex['city'] = complex.get('city', complex.get('address_city', ''))
    complex['district'] = complex.get('district', complex.get('address_district', ''))
    complex['street'] = complex.get('street', complex.get('address_street', ''))
    complex['gallery_photos'] = images
    complex['images'] = images
    
    # Описание
    complex['description'] = dev.get('description', '') or parameters.get('Описание', '')
    
    # Цены из price_range или parameters
    price_range = dev.get('price_range', '')
    if price_range:
        # Пытаемся извлечь цены из строки "от X до Y млн ₽"
        price_match = re.search(r'от\s+([\d.]+)', price_range)
        if price_match:
            complex['price_from'] = price_match.group(1)
        price_match_to = re.search(r'до\s+([\d.]+)', price_range)
        if price_match_to:
            complex['price_to'] = price_match_to.group(1)
    else:
        complex['price_from'] = parameters.get('Цена от', None)
        complex['price_to'] = parameters.get('Цена до', None)
    
    # Площади из apartment_types
    all_areas = []
    apartment_types = complex.get('apartment_types', {})
    for apt_type, apt_data in apartment_types.items():
        apartments = apt_data.get('apartments', [])
        for apt in apartments:
            area = apt.get('totalArea') or apt.get('total_area') or apt.get('area')
            if area:
                try:
                    all_areas.append(float(area))
                except (ValueError, TypeError):
                    pass
    if all_areas:
        complex['area_from'] = round(min(all_areas), 1)
        complex['area_to'] = round(max(all_areas), 1)
    else:
        complex['area_from'] = parameters.get('Площадь от', None)
        complex['area_to'] = parameters.get('Площадь до', None)
    
    # Комнаты (из apartment_types)
    rooms_set = set()
    for apt_type, apt_data in apartment_types.items():
        apartments = apt_data.get('apartments', [])
        for apt in apartments:
            rooms = apt.get('rooms')
            if rooms:
                rooms_set.add(str(rooms))
    if rooms_set:
        complex['rooms'] = ', '.join(sorted(rooms_set))
    else:
        complex['rooms'] = None
    
    # Дата сдачи
    complex['delivery_date'] = parameters.get('Срок сдачи', None) or parameters.get('Дата сдачи', None)
    
    # Старт продаж
    complex['sales_start'] = parameters.get('Старт продаж', None) or parameters.get('Начало продаж', None)
    
    # Застройщик
    complex['developer'] = parameters.get('Застройщик', '')
    
    # Класс дома
    complex['house_class'] = parameters.get('Класс недвижимости', '') or parameters.get('Класс дома', '')
    
    # Подрядчики
    complex['contractors'] = parameters.get('Подрядчики', '')
    
    # Энергоэффективность
    complex['energy_efficiency'] = parameters.get('Класс энергоэффективности', '')
    
    # Этажность
    complex['floors'] = parameters.get('Этажность', None) or parameters.get('Количество этажей', None)
    
    # Количество квартир
    total_apartments = 0
    for apt_type, apt_data in apartment_types.items():
        apartments = apt_data.get('apartments', [])
        total_apartments += len(apartments)
    complex['apartments_count'] = total_apartments if total_apartments > 0 else parameters.get('Количество квартир', None)
    
    # Высота потолков
    complex['ceiling_height'] = parameters.get('Высота потолков', None)

    # Подтягиваем закрепленного агента, если есть
    agent = None
    try:
        agent_id = complex.get('agent_id')
        if agent_id:
            # agent_id может прийти как ObjectId или строка
            _agent_oid = ObjectId(agent_id) if not isinstance(agent_id, ObjectId) else agent_id
            agent_doc = db['employees'].find_one({'_id': _agent_oid, 'is_active': True})
            if agent_doc:
                agent = {
                    'id': str(agent_doc.get('_id')),
                    'full_name': agent_doc.get('full_name') or '',
                    'position': agent_doc.get('position') or '',
                    'photo': (agent_doc.get('photo') or ''),
                }
    except Exception:
        agent = None

    # Преобразуем apartment_types в flats_data для шаблона
    apartment_types = complex.get('apartment_types', {})
    flats_data = {}
    for apt_type, apt_data in apartment_types.items():
        apartments = apt_data.get('apartments', [])
        if apartments:
            flats_data[apt_type] = {
                'total_count': len(apartments),
                'flats': apartments
            }

    # Обрабатываем flats_data для статистики квартир
    if flats_data:
        for apt_type, apt_data in flats_data.items():
            if isinstance(apt_data, dict):
                flats = apt_data.get('flats', [])
                total_count = apt_data.get('total_count', len(flats) if flats else 0)
                
                # Вычисляем min/max площадь из всех квартир
                areas = []
                if flats:
                    for flat in flats:
                        if isinstance(flat, dict):
                            total_area = flat.get('totalArea') or flat.get('total_area') or flat.get('area')
                            if total_area:
                                try:
                                    areas.append(float(total_area))
                                except (ValueError, TypeError):
                                    pass
                
                if areas:
                    min_area = round(min(areas), 1)
                    max_area = round(max(areas), 1)
                    apt_data['min_area'] = min_area
                    apt_data['max_area'] = max_area
                else:
                    apt_data['min_area'] = None
                    apt_data['max_area'] = None
                
                # Убеждаемся что total_count есть
                apt_data['total_count'] = total_count
    
    complex['flats_data'] = flats_data

    # Формируем object_details для детальных характеристик
    object_details = {
        'main_characteristics': {},
        'yard_improvement': {},
        'accessible_environment': {},
        'elevators': {},
        'parking_space': {},
    }
    
    # Основные характеристики
    if complex.get('floors'):
        object_details['main_characteristics']['Этажность'] = str(complex['floors'])
    if complex.get('apartments_count'):
        object_details['main_characteristics']['Количество квартир'] = str(complex['apartments_count'])
    if complex.get('ceiling_height'):
        object_details['main_characteristics']['Высота потолков'] = str(complex['ceiling_height']) + ' м'
    if complex.get('energy_efficiency'):
        object_details['main_characteristics']['Класс энергоэффективности'] = complex['energy_efficiency']
    
    # Добавляем другие параметры из parameters
    for key, value in parameters.items():
        if value and value != '':
            # Классифицируем параметры по категориям
            key_lower = key.lower()
            if any(word in key_lower for word in ['двор', 'благоустройство', 'озеленение', 'детская', 'спортивная']):
                object_details['yard_improvement'][key] = str(value)
            elif any(word in key_lower for word in ['доступная', 'пандус', 'лифт']):
                object_details['accessible_environment'][key] = str(value)
            elif any(word in key_lower for word in ['лифт', 'подъемник']):
                object_details['elevators'][key] = str(value)
            elif any(word in key_lower for word in ['парковка', 'парковочное', 'гараж']):
                object_details['parking_space'][key] = str(value)
            elif key not in ['Застройщик', 'Класс недвижимости', 'Срок сдачи', 'Дата сдачи', 'Старт продаж', 'Начало продаж', 'Цена от', 'Цена до', 'Площадь от', 'Площадь до', 'Этажность', 'Количество этажей', 'Количество квартир', 'Высота потолков', 'Класс энергоэффективности', 'Описание']:
                object_details['main_characteristics'][key] = str(value)
    
    complex['object_details'] = object_details
    
    # Нормализуем формат хода строительства (как в обычной детальной странице)
    construction_progress_raw = complex.get('construction_progress', {})
    if isinstance(construction_progress_raw, list):
        # Если это массив этапов, оборачиваем в объект с construction_stages
        normalized_stages = []
        for idx, stage in enumerate(construction_progress_raw):
            if isinstance(stage, dict):
                normalized_stage = stage.copy()
                if 'stage_number' not in normalized_stage:
                    normalized_stage['stage_number'] = idx + 1
                if 'date' not in normalized_stage:
                    normalized_stage['date'] = normalized_stage.get('stage', '')
                normalized_stages.append(normalized_stage)
            else:
                normalized_stages.append({
                    'stage_number': idx + 1,
                    'date': '',
                    'photos': []
                })
        complex['construction_progress_data'] = {'construction_stages': normalized_stages}
    elif isinstance(construction_progress_raw, dict) and 'construction_stages' in construction_progress_raw:
        # Если это уже объект с construction_stages, добавляем stage_number если его нет
        stages = construction_progress_raw.get('construction_stages', [])
        normalized_stages = []
        for idx, stage in enumerate(stages):
            if isinstance(stage, dict):
                normalized_stage = stage.copy()
                if 'stage_number' not in normalized_stage:
                    normalized_stage['stage_number'] = idx + 1
                if 'date' not in normalized_stage:
                    normalized_stage['date'] = normalized_stage.get('stage', '')
                normalized_stages.append(normalized_stage)
            else:
                normalized_stages.append({
                    'stage_number': idx + 1,
                    'date': '',
                    'photos': []
                })
        complex['construction_progress_data'] = {'construction_stages': normalized_stages}
    elif isinstance(construction_progress_raw, dict) and construction_progress_raw:
        # Если это объект без construction_stages, пытаемся создать этап из photos
        direct_photos = construction_progress_raw.get('photos', [])
        if direct_photos:
            complex['construction_progress_data'] = {
                'construction_stages': [{
                    'stage_number': 1,
                    'stage': 'Строительство',
                    'date': construction_progress_raw.get('date', ''),
                    'photos': direct_photos
                }]
            }
        else:
            complex['construction_progress_data'] = {}
    else:
        complex['construction_progress_data'] = {}

    # Получаем другие будущие ЖК для блока "Другие проекты"
    other_complexes = get_future_complexes_from_mongo(limit=6)
    
    # Адаптируем other_complexes для шаблона
    for other in other_complexes:
        if '_id' in other:
            other['id'] = str(other['_id'])
        other_dev = other.get('development', {})
        other['name'] = other_dev.get('name', 'Без названия')
        other['city'] = other.get('city', other.get('address_city', ''))
        other['district'] = other.get('district', other.get('address_district', ''))
        other['gallery_photos'] = other_dev.get('photos', [])
        other_params = other_dev.get('parameters', {})
        other['delivery_date'] = other_params.get('Срок сдачи', None) or other_params.get('Дата сдачи', None)
        other['price_from'] = other_params.get('Цена от', None)

    context = {
        'complex': complex,
        'images': images,
        'other_complexes': other_complexes,
        'agent': agent,
    }
    return render(request, 'main/future_complex_detail.html', context)

