"""Views для будущих жилых комплексов"""
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
    """Детальная страница будущего ЖК - данные из MongoDB"""
    try:
        db = get_mongo_connection()
        collection = db['future_complexes']
        complex = collection.find_one({'_id': ObjectId(complex_id), 'is_active': True})
        if not complex:
            raise Http404("ЖК не найден")
    except Exception:
        raise Http404("ЖК не найден")

    # Получаем изображения ЖК (если есть в MongoDB)
    images = complex.get('images', [])

    # Преобразуем _id в строку для использования в шаблонах
    if '_id' in complex:
        complex['id'] = str(complex['_id'])

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

    # Обрабатываем flats_data для статистики квартир
    flats_data = complex.get('flats_data', {})
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

    # Получаем другие будущие ЖК для блока "Другие проекты"
    other_complexes = get_future_complexes_from_mongo(limit=6)

    context = {
        'complex': complex,
        'images': images,
        'other_complexes': other_complexes,
        'agent': agent,
    }
    return render(request, 'main/future_complex_detail.html', context)

