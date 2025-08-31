from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.contrib import messages
from .models import ResidentialComplex, Article, Tag, CompanyInfo, CatalogLanding, SecondaryProperty, Category, Employee, EmployeeReview, FutureComplex
from .models import Vacancy
from .models import BranchOffice
from .models import Gallery, MortgageProgram, SpecialOffer
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
    # Галерея компании
    company_gallery = []
    if company_info:
        company_gallery = company_info.get_images()[:6]
    # Статьи для главной
    home_articles = Article.objects.filter(show_on_home=True).order_by('-published_date')[:3]
    # Акции для главной - случайные 6 активных предложений
    offers = SpecialOffer.get_active_offers(limit=4)
    
    # Будущие ЖК для главной - 4 случайных активных ЖК
    future_complexes = FutureComplex.objects.filter(is_active=True).order_by('?')[:4]
    
    context = {
        'complexes': complexes,
        'company_info': company_info,
        'company_gallery': company_gallery,
        'home_articles': home_articles,
        'offers': offers,
        'future_complexes': future_complexes,
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
        'filters_applied': filters_applied,
        'dataset_type': 'newbuild'  # По умолчанию показываем новостройки
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
        
        # Получаем изображения для каталога
        catalog_images = complex.get_catalog_images()
        
        # Подготавливаем отдельные URL для каждого изображения
        image_url = None
        image_2_url = None
        image_3_url = None
        image_4_url = None
        
        if catalog_images:
            # Главное изображение
            if len(catalog_images) > 0 and catalog_images[0].image:
                image_url = catalog_images[0].image.url
            
            # Дополнительные изображения
            if len(catalog_images) > 1 and catalog_images[1].image:
                image_2_url = catalog_images[1].image.url
            if len(catalog_images) > 2 and catalog_images[2].image:
                image_3_url = catalog_images[2].image.url
            if len(catalog_images) > 3 and catalog_images[3].image:
                image_4_url = catalog_images[3].image.url
        
        complexes_data.append({
            'id': complex.id if complex.id else 0,
            'name': complex.name,
            'price_display': complex.price_display,
            'price_from': complex.price_from,
            'location': location,
            'commute_time': complex.commute_time,
            'image_url': image_url,
            'image_2_url': image_2_url,
            'image_3_url': image_3_url,
            'image_4_url': image_4_url,
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
    article_type = request.GET.get('type', 'news')  # По умолчанию показываем новости
    
    # Получаем статьи по типу
    articles_list = Article.objects.filter(article_type=article_type)
    
    # Дополнительная фильтрация по категории
    if category:
        try:
            category_obj = Category.objects.get(slug=category)
            articles_list = articles_list.filter(category=category_obj)
        except Category.DoesNotExist:
            articles_list = Article.objects.none()
    
    # Получаем статьи по категориям для отображения в секциях (только для текущего типа)
    try:
        mortgage_category = Category.objects.get(slug='mortgage')
        mortgage_articles = Article.objects.filter(article_type=article_type, category=mortgage_category, is_featured=True)[:3]
    except Category.DoesNotExist:
        mortgage_articles = Article.objects.none()
    
    try:
        laws_category = Category.objects.get(slug='laws')
        laws_articles = Article.objects.filter(article_type=article_type, category=laws_category)[:3]
    except Category.DoesNotExist:
        laws_articles = Article.objects.none()
    
    try:
        instructions_category = Category.objects.get(slug='instructions')
        instructions_articles = Article.objects.filter(article_type=article_type, category=instructions_category)[:3]
    except Category.DoesNotExist:
        instructions_articles = Article.objects.none()
    
    try:
        market_category = Category.objects.get(slug='market')
        market_articles = Article.objects.filter(article_type=article_type, category=market_category)[:3]
    except Category.DoesNotExist:
        market_articles = Article.objects.none()
    
    try:
        tips_category = Category.objects.get(slug='tips')
        tips_articles = Article.objects.filter(article_type=article_type, category=tips_category)[:3]
    except Category.DoesNotExist:
        tips_articles = Article.objects.none()
    
    # Получаем все категории для фильтрации
    categories = Category.objects.filter(is_active=True)
    
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
        'current_type': article_type,
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
    vacancies_qs = Vacancy.objects.filter(is_active=True)

    paginator = Paginator(vacancies_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'vacancies': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
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
    category = request.GET.get('category', '')  # 'newbuild' или 'secondary'
    complex_id = request.GET.get('complex', '')
    
    # Получаем видео из галереи
    videos_qs = Gallery.objects.filter(
        content_type='video',
        is_active=True
    )
    
    # Фильтруем по категории
    if category == 'newbuild':
        videos_qs = videos_qs.filter(category='residential_video')
    elif category == 'secondary':
        videos_qs = videos_qs.filter(category='secondary_video')
    
    if complex_id:
        try:
            videos_qs = videos_qs.filter(object_id=int(complex_id))
        except ValueError:
            pass

    # Добавляем название объекта к каждому видео
    for video in videos_qs:
        try:
            if video.category == 'residential_video':
                complex_obj = ResidentialComplex.objects.get(id=video.object_id)
                video.residential_complex_name = complex_obj.name
            elif video.category == 'secondary_video':
                property_obj = SecondaryProperty.objects.get(id=video.object_id)
                video.residential_complex_name = property_obj.name
        except (ResidentialComplex.DoesNotExist, SecondaryProperty.DoesNotExist):
            video.residential_complex_name = "Неизвестный объект"
    
    # Если фильтруем по конкретному объекту и нет видео, показываем сообщение
    if complex_id and not videos_qs.exists():
        # Получаем категории для фильтра
        categories = [
            {'value': 'newbuild', 'name': 'Новостройки'},
            {'value': 'secondary', 'name': 'Вторичная недвижимость'},
        ]
        
        context = {
            'videos': [],
            'page_obj': None,
            'paginator': None,
            'categories': categories,
            'filters': {
                'category': category,
                'complex': complex_id,
            },
            'no_videos_for_complex': True
        }
        return render(request, 'main/videos.html', context)
    
    # Проверяем, есть ли результаты поиска
    if not videos_qs.exists():
        # Получаем категории для фильтра
        categories = [
            {'value': 'newbuild', 'name': 'Новостройки'},
            {'value': 'secondary', 'name': 'Вторичная недвижимость'},
        ]
        
        context = {
            'videos': [],
            'page_obj': None,
            'paginator': None,
            'categories': categories,
            'filters': {
                'category': category,
                'complex': complex_id,
            },
            'no_videos_for_complex': False
        }
        return render(request, 'main/videos.html', context)
    
    paginator = Paginator(videos_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Получаем категории для фильтра
    categories = [
        {'value': 'newbuild', 'name': 'Новостройки'},
        {'value': 'secondary', 'name': 'Вторичная недвижимость'},
    ]

    context = {
        'videos': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
        'filters': {
            'category': category,
            'complex': complex_id,
        }
    }
    return render(request, 'main/videos.html', context)


def video_detail(request, video_id):
    """Детальная страница видеообзора"""
    video = get_object_or_404(Gallery, id=video_id, content_type='video', is_active=True)
    
    # Получаем связанный объект в зависимости от категории
    if video.category == 'residential_video':
        residential_complex = ResidentialComplex.objects.get(id=video.object_id)
        object_type = 'ЖК'
    elif video.category == 'secondary_video':
        residential_complex = SecondaryProperty.objects.get(id=video.object_id)
        object_type = 'Объект'
    else:
        raise Http404("Неизвестная категория видео")
    
    # Формируем embed URL для видео
    video_embed_url = None
    if video.video_url:
        url = video.video_url.strip()
        
        # Проверяем, является ли это iframe кодом
        if url.startswith('<iframe'):
            # Извлекаем src из iframe
            import re
            src_match = re.search(r'src=["\']([^"\']+)["\']', url)
            if src_match:
                video_embed_url = src_match.group(1)
            else:
                video_embed_url = url
        # YouTube обработка
        elif 'youtu.be/' in url:
            vid = url.split('youtu.be/')[-1].split('?')[0]
            video_embed_url = f'https://www.youtube.com/embed/{vid}'
        elif 'watch?v=' in url:
            vid = url.split('watch?v=')[-1].split('&')[0]
            video_embed_url = f'https://www.youtube.com/embed/{vid}'
        # Rutube обработка
        elif 'rutube.ru' in url:
            # Если это уже embed URL
            if '/play/embed/' in url:
                video_embed_url = url
            else:
                # Если это обычная ссылка, пытаемся извлечь ID
                import re
                rutube_match = re.search(r'rutube\.ru/video/([a-f0-9]+)', url)
                if rutube_match:
                    video_id = rutube_match.group(1)
                    video_embed_url = f'https://rutube.ru/play/embed/{video_id}/'
                else:
                    video_embed_url = url
        else:
            video_embed_url = url
    
    # Видео из того же объекта
    same_complex_videos = Gallery.objects.filter(
        category=video.category,
        content_type='video',
        is_active=True,
        object_id=video.object_id
    ).exclude(id=video.id)[:5]
    
    # Похожие видео (из других объектов того же города)
    if video.category == 'residential_video':
        complex_ids = ResidentialComplex.objects.filter(city=residential_complex.city).exclude(id=video.object_id).values_list('id', flat=True)
    else:
        complex_ids = SecondaryProperty.objects.filter(city=residential_complex.city).exclude(id=video.object_id).values_list('id', flat=True)
    
    similar_videos = Gallery.objects.filter(
        category=video.category,
        content_type='video',
        is_active=True,
        object_id__in=complex_ids
    ).exclude(id=video.id)[:3]

    context = {
        'video': video,
        'video_embed_url': video_embed_url,
        'residential_complex': residential_complex,
        'same_complex_videos': same_complex_videos,
        'similar_videos': similar_videos,
        'object_type': object_type,
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
    
    # Получаем акции для данного ЖК
    from django.utils import timezone
    complex_offers = SpecialOffer.objects.filter(
        residential_complex=complex,
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).order_by('-priority', '-created_at')
    
    # Первое активное видеообзор этого ЖК
    video = complex.get_main_video()
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
        'complex_offers': complex_offers,
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
        # Получаем изображения для каталога
        catalog_images = obj.get_catalog_images()
        
        # Подготавливаем отдельные URL для каждого изображения
        image_url = None
        image_2_url = None
        image_3_url = None
        image_4_url = None
        
        if catalog_images:
            # Главное изображение
            if len(catalog_images) > 0 and catalog_images[0].image:
                image_url = catalog_images[0].image.url
            
            # Дополнительные изображения
            if len(catalog_images) > 1 and catalog_images[1].image:
                image_2_url = catalog_images[1].image.url
            if len(catalog_images) > 2 and catalog_images[2].image:
                image_3_url = catalog_images[2].image.url
            if len(catalog_images) > 3 and catalog_images[3].image:
                image_4_url = catalog_images[3].image.url
        
        items.append({
            'id': obj.id if obj.id else 0,
            'name': obj.name,
            'price_from': float(obj.price),
            'city': obj.city,
            'district': obj.district,
            'street': obj.street,
            'image_url': image_url,
            'image_2_url': image_2_url,
            'image_3_url': image_3_url,
            'image_4_url': image_4_url,
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


def team(request):
    """Страница команды"""
    employees = Employee.objects.filter(is_active=True).order_by('-is_featured', 'full_name')
    
    context = {
        'employees': employees,
    }
    return render(request, 'main/team.html', context)


def future_complexes(request):
    """Страница будущих ЖК"""
    # Получаем параметры фильтрации
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')
    price_from = request.GET.get('price_from', '')
    price_to = request.GET.get('price_to', '')
    delivery_date = request.GET.get('delivery_date', '')
    sort = request.GET.get('sort', 'delivery_date_asc')
    
    # Базовый queryset
    complexes = FutureComplex.objects.filter(is_active=True)
    
    # Применяем фильтры
    if city:
        complexes = complexes.filter(city__icontains=city)
    if district:
        complexes = complexes.filter(district__icontains=district)
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
    if sort == 'delivery_date_asc':
        complexes = complexes.order_by('delivery_date')
    elif sort == 'delivery_date_desc':
        complexes = complexes.order_by('-delivery_date')
    elif sort == 'price_asc':
        complexes = complexes.order_by('price_from')
    elif sort == 'price_desc':
        complexes = complexes.order_by('-price_from')
    elif sort == 'name_asc':
        complexes = complexes.order_by('name')
    else:
        complexes = complexes.order_by('-is_featured', 'delivery_date')
    
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
    """Детальная страница будущего ЖК"""
    try:
        complex = FutureComplex.objects.get(id=complex_id, is_active=True)
    except FutureComplex.DoesNotExist:
        raise Http404("ЖК не найден")
    
    # Получаем изображения ЖК
    images = complex.get_images()
    
    # Получаем другие будущие ЖК для блока "Другие проекты"
    other_complexes = FutureComplex.objects.filter(
        is_active=True
    ).exclude(id=complex_id).order_by('?')[:6]
    
    context = {
        'complex': complex,
        'images': images,
        'other_complexes': other_complexes,
    }
    return render(request, 'main/future_complex_detail.html', context)


def employee_detail(request, employee_id):
    """Детальная страница сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id, is_active=True)
    
    # Получаем объекты недвижимости агента
    residential_complexes = employee.residential_complexes.filter(is_featured=True)[:6]
    secondary_properties = employee.secondary_properties.all()[:6]
    
    # Получаем опубликованные отзывы
    reviews = employee.reviews.filter(is_approved=True, is_published=True).order_by('-created_at')[:10]
    
    # Обработка формы отзыва
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        rating = request.POST.get('rating', 5)
        text = request.POST.get('text', '').strip()
        
        if name and text and rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    EmployeeReview.objects.create(
                        employee=employee,
                        name=name,
                        email=email,
                        phone=phone,
                        rating=rating,
                        text=text
                    )
                    messages.success(request, 'Спасибо! Ваш отзыв отправлен на модерацию.')
                    return redirect('main:employee_detail', employee_id=employee.id)
            except ValueError:
                pass
        
        messages.error(request, 'Пожалуйста, заполните все обязательные поля корректно.')
    
    context = {
        'employee': employee,
        'residential_complexes': residential_complexes,
        'secondary_properties': secondary_properties,
        'reviews': reviews,
    }
    return render(request, 'main/employee_detail.html', context)


def mortgage(request):
    """Страница ипотеки с калькулятором"""
    # Получаем ипотечные программы для калькулятора
    mortgage_programs = MortgageProgram.objects.filter(is_active=True).order_by('rate')
    
    # Если нет программ, создаем базовую
    if not mortgage_programs.exists():
        mortgage_programs = [
            type('MortgageProgram', (), {
                'name': 'Базовая',
                'rate': 11.4
            })()
        ]
    
    context = {
        'mortgage_programs': mortgage_programs,
    }
    return render(request, 'main/mortgage.html', context)


def all_offers(request):
    """Страница всех акций"""
    from django.utils import timezone
    
    # Получаем все активные акции
    offers = SpecialOffer.objects.filter(
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).select_related('residential_complex').order_by('?')
    
    context = {
        'offers': offers,
    }
    return render(request, 'main/all_offers.html', context)


def offer_detail(request, offer_id):
    """Детальная страница акции"""
    from django.utils import timezone
    
    # Получаем акцию
    offer = get_object_or_404(SpecialOffer, id=offer_id, is_active=True)
    
    # Проверяем, не истекла ли акция
    if offer.expires_at and offer.expires_at < timezone.now():
        raise Http404("Акция истекла")
    
    # Получаем другие активные акции (без лимита)
    other_offers = SpecialOffer.objects.filter(
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).exclude(id=offer_id).select_related('residential_complex').order_by('?')[:8]
    
    context = {
        'offer': offer,
        'other_offers': other_offers,
    }
    return render(request, 'main/offer_detail.html', context)

def videos_objects_api(request):
    """API для получения списка объектов по категории недвижимости"""
    from django.http import JsonResponse
    
    category = request.GET.get('category', '')
    
    if category == 'newbuild':
        objects = ResidentialComplex.objects.values('id', 'name')
    elif category == 'secondary':
        objects = SecondaryProperty.objects.values('id', 'name')
    else:
        objects = []
    
    return JsonResponse({
        'success': True,
        'objects': list(objects)
    })
