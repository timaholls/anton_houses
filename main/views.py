from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import ResidentialComplex, Article, Tag, CompanyInfo

def home(request):
    """Главная страница"""
    # Получаем 9 популярных ЖК для главной страницы
    complexes = ResidentialComplex.objects.filter(is_featured=True).order_by('-created_at')[:9]
    
    # Если популярных ЖК меньше 9, добавляем обычные
    if complexes.count() < 9:
        remaining_count = 9 - complexes.count()
        additional_complexes = ResidentialComplex.objects.filter(is_featured=False).order_by('-created_at')[:remaining_count]
        complexes = list(complexes) + list(additional_complexes)
    
    # Получаем информацию о компании
    company_info = CompanyInfo.get_active()
    
    context = {
        'complexes': complexes,
        'company_info': company_info
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
    """API для каталога ЖК с пагинацией и фильтрацией"""
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
    
    # Применяем фильтры
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
    
    # Подготавливаем данные для JSON
    complexes_data = []
    for complex in page_obj:
        # Создаем локацию из существующих полей
        location_parts = []
        if complex.city:
            location_parts.append(complex.city)
        if complex.district:
            location_parts.append(complex.district)
        if complex.street:
            location_parts.append(complex.street)
        
        location = ' - '.join(location_parts) if location_parts else 'Локация не указана'
        
        complexes_data.append({
            'id': complex.id,
            'name': complex.name,
            'price_display': complex.price_display,
            'price_from': complex.price_from,
            'location': location,
            'commute_time': complex.commute_time,
            'image_url': complex.image.url if complex.image else None,
            'house_type': complex.house_type,
            'house_type_display': complex.get_house_type_display(),
            'area_from': complex.area_from,
            'area_to': complex.area_to,
            'total_apartments': complex.total_apartments,
            'completion_start': complex.completion_start,
            'completion_end': complex.completion_end,
            'studio_price': complex.studio_price,
            'one_room_price': complex.one_room_price,
            'two_room_price': complex.two_room_price,
            'three_room_price': complex.three_room_price,
            'four_room_price': complex.four_room_price,
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
    category = request.GET.get('category', '')
    
    # Получаем статьи
    if category:
        articles_list = Article.objects.filter(category=category)
    else:
        articles_list = Article.objects.all()
    
    # Получаем статьи по категориям для отображения в секциях
    mortgage_articles = Article.objects.filter(category='mortgage', is_featured=True)[:3]
    laws_articles = Article.objects.filter(category='laws')[:3]
    instructions_articles = Article.objects.filter(category='instructions')[:3]
    market_articles = Article.objects.filter(category='market')[:3]
    tips_articles = Article.objects.filter(category='tips')[:3]
    
    # Получаем все категории для фильтрации
    categories = Article.CATEGORY_CHOICES
    
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

def detail(request, complex_id):
    """Детальная страница ЖК"""
    complex = get_object_or_404(ResidentialComplex, id=complex_id)
    
    # Получаем похожие ЖК для рекомендаций
    similar_complexes = ResidentialComplex.objects.filter(
        city=complex.city,
        house_class=complex.house_class
    ).exclude(id=complex.id)[:3]
    
    context = {
        'complex': complex,
        'similar_complexes': similar_complexes,
    }
    return render(request, 'main/detail.html', context)

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
