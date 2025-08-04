from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import ResidentialComplex

def home(request):
    """Главная страница"""
    # Получаем первые 9 ЖК для главной страницы
    complexes = ResidentialComplex.objects.all()[:9]
    
    context = {
        'complexes': complexes
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
    sort = request.GET.get('sort', 'price_asc')
    
    # Базовый queryset
    complexes = ResidentialComplex.objects.all()
    
    # Применяем фильтры только если есть параметры поиска
    filters_applied = False
    if rooms or city or district or street or area_from or area_to or price_from or price_to or delivery_date:
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
            'sort': sort,
        },
        'filters_applied': filters_applied
    }
    return render(request, 'main/catalog.html', context)

def catalog_api(request):
    """API для каталога ЖК с пагинацией"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.all()
    
    # Пагинация по 9 элементов
    paginator = Paginator(complexes, 9)
    page_obj = paginator.get_page(page)
    
    # Подготавливаем данные для JSON
    complexes_data = []
    for complex in page_obj:
        complexes_data.append({
            'id': complex.id,
            'name': complex.name,
            'price_display': complex.price_display,
            'location': complex.location,
            'commute_time': complex.commute_time,
            'image_url': complex.image.url if complex.image else None,
        })
    
    return JsonResponse({
        'complexes': complexes_data,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count
    })

def articles(request):
    """Страница статей"""
    return render(request, 'main/articles.html')

# Быстрые ссылки каталога
def catalog_completed(request):
    """Сданные ЖК"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(status='completed')
    
    paginator = Paginator(complexes, 9)
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
    
    paginator = Paginator(complexes, 9)
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
    
    paginator = Paginator(complexes, 9)
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
    
    paginator = Paginator(complexes, 9)
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
        'page_description': 'Жилье комфорт-класса'
    }
    return render(request, 'main/catalog.html', context)

def catalog_premium(request):
    """Премиум-класс"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(house_class='premium')
    
    paginator = Paginator(complexes, 9)
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
        'page_description': 'Элитное жилье премиум-класса'
    }
    return render(request, 'main/catalog.html', context)

def catalog_finished(request):
    """С отделкой"""
    page = request.GET.get('page', 1)
    complexes = ResidentialComplex.objects.filter(finishing='finished')
    
    paginator = Paginator(complexes, 9)
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
    
    paginator = Paginator(complexes, 9)
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
