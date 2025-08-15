from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import ResidentialComplex, Article, Tag, CompanyInfo, CatalogLanding, SecondaryProperty
from .models import Vacancy
from .models import BranchOffice, Employee
from .models import ResidentialVideo, VideoComment, MortgageProgram, SpecialOffer
from django.db import models

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
    # Статьи для главной
    home_articles = Article.objects.filter(show_on_home=True).order_by('-published_date')[:3]
    # Акции для главной
    offers = SpecialOffer.objects.filter(is_active=True).select_related('residential_complex')[:5]
    
    context = {
        'complexes': complexes,
        'company_info': company_info,
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
    
    # Пагинация по 10 элементов
    paginator = Paginator(complexes, 10)
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
    
    # Пагинация по 10 элементов
    paginator = Paginator(complexes, 10)
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
            'image_2_url': complex.image_2.url if complex.image_2 else None,
            'image_3_url': complex.image_3.url if complex.image_3 else None,
            'image_4_url': complex.image_4.url if complex.image_4 else None,
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
            'lat': complex.latitude,
            'lng': complex.longitude,
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


def vacancies(request):
    """Список вакансий"""
    department = request.GET.get('department', '')
    city = request.GET.get('city', '')
    employment_type = request.GET.get('employment_type', '')

    vacancies_qs = Vacancy.objects.filter(is_active=True)
    if department:
        vacancies_qs = vacancies_qs.filter(department__iexact=department)
    if city:
        vacancies_qs = vacancies_qs.filter(city__iexact=city)
    if employment_type:
        vacancies_qs = vacancies_qs.filter(employment_type=employment_type)

    paginator = Paginator(vacancies_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    departments = Vacancy.objects.exclude(department='').values_list('department', flat=True).distinct()
    cities = Vacancy.objects.values_list('city', flat=True).distinct()
    employment_choices = Vacancy.EMPLOYMENT_CHOICES

    context = {
        'vacancies': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'departments': departments,
        'cities': cities,
        'employment_choices': employment_choices,
        'filters': {
            'department': department,
            'city': city,
            'employment_type': employment_type,
        }
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
    """Список видеообзоров ЖК"""
    city = request.GET.get('city', '')
    complex_id = request.GET.get('complex', '')
    videos_qs = ResidentialVideo.objects.filter(is_active=True).select_related('residential_complex')
    if city:
        videos_qs = videos_qs.filter(residential_complex__city__iexact=city)
    if complex_id:
        try:
            videos_qs = videos_qs.filter(residential_complex__id=int(complex_id))
        except ValueError:
            pass

    paginator = Paginator(videos_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    cities = ResidentialVideo.objects.select_related('residential_complex').values_list('residential_complex__city', flat=True).distinct()

    context = {
        'videos': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': cities,
        'filters': {
            'city': city,
            'complex': complex_id,
        }
    }
    return render(request, 'main/videos.html', context)


def video_detail(request, slug):
    """Детальная страница видеообзора с комментариями"""
    video = get_object_or_404(ResidentialVideo, slug=slug, is_active=True)

    # Увеличиваем просмотры только для GET
    if request.method == 'GET':
        ResidentialVideo.objects.filter(pk=video.pk).update(views_count=models.F('views_count') + 1)
        video.refresh_from_db(fields=['views_count'])

    # Обработка отправки комментария
    comment_success = False
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        rating = int(request.POST.get('rating', '5') or 5)
        text = request.POST.get('text', '').strip()
        if name and text:
            VideoComment.objects.create(video=video, name=name, rating=max(1, min(5, rating)), text=text)
            comment_success = True

    # Похожие видео (из связей, либо по городу)
    related = video.related_videos.filter(is_active=True)[:3]
    if related.count() < 3:
        fallback = ResidentialVideo.objects.filter(
            is_active=True,
            residential_complex__city=video.residential_complex.city
        ).exclude(id=video.id)[: 3 - related.count()]
        related = list(related) + list(fallback)

    context = {
        'video': video,
        'related_videos': related,
        'comment_success': comment_success,
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
    """Детальная страница ЖК"""
    complex = get_object_or_404(ResidentialComplex, id=complex_id)
    
    # Получаем похожие ЖК для рекомендаций
    similar_complexes = ResidentialComplex.objects.filter(
        city=complex.city,
        house_class=complex.house_class
    ).exclude(id=complex.id)[:3]
    
    # Первое активное видеообзор этого ЖК
    video = ResidentialVideo.objects.filter(residential_complex=complex, is_active=True).order_by('-is_featured', '-published_date').first()
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
     
    mortgage_programs = list(MortgageProgram.objects.filter(is_active=True))
    if not mortgage_programs:
        # Защита: если нет записей, используем дефолтный набор в памяти
        class P:
            def __init__(self, name, rate):
                self.name, self.rate = name, rate
        mortgage_programs = [
            P('Базовая', 18.0),
            P('IT-ипотека', 6.0),
            P('Семейная', 6.0),
        ]
     
    context = {
        'complex': complex,
        'similar_complexes': similar_complexes,
        'video': video,
        'video_embed_url': video_embed_url,
        'mortgage_programs': mortgage_programs,
    }
    return render(request, 'main/detail.html', context)

def secondary_detail(request, pk: int):
    obj = get_object_or_404(SecondaryProperty, pk=pk)
    # Используем существующий шаблон detail.html с минимальным контекстом-адаптером
    class Adapter:
        pass
    complex = Adapter()
    complex.name = obj.name
    complex.image = obj.image
    complex.image_2 = obj.image_2
    complex.image_3 = obj.image_3
    complex.image_4 = obj.image_4
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
    complex.get_house_type_display = obj.get_house_type_display if hasattr(obj, 'get_house_type_display') else lambda: ''
    complex.get_finishing_display = lambda: ''

    return render(request, 'main/detail.html', {'complex': complex, 'similar_complexes': []})

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

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page)

    items = []
    for obj in page_obj:
        items.append({
            'id': obj.id,
            'name': obj.name,
            'price_from': float(obj.price),
            'city': obj.city,
            'district': obj.district,
            'street': obj.street,
            'image_url': obj.image.url if obj.image else None,
            'image_2_url': obj.image_2.url if obj.image_2 else None,
            'image_3_url': obj.image_3.url if obj.image_3 else None,
            'image_4_url': obj.image_4.url if obj.image_4 else None,
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
        'commercial': None,        # коммерция отсутствует — оставляем как есть
        'all': None,
    }
    house_type = category_map.get(landing.category)
    if house_type:
        if landing.kind == 'secondary':
            queryset = queryset.filter(house_type=house_type)
        else:
            queryset = queryset.filter(house_type=house_type)

    paginator = Paginator(queryset, 10)
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

    paginator = Paginator(queryset, 10)
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

def company(request):
    """Страница "Наша компания" со всеми сотрудниками"""
    company_info = CompanyInfo.get_active()
    employees_qs = Employee.objects.filter(is_active=True).select_related('branch').order_by('full_name')

    paginator = Paginator(employees_qs, 24)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'company_info': company_info,
        'employees': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
    }
    return render(request, 'main/company.html', context)
