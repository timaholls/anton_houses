from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
import re

# Create your models here.

def create_slug(title):
    """Создает slug из заголовка, поддерживая кириллицу"""
    # Транслитерация кириллицы в латиницу
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    # Транслитерация
    result = ''
    for char in title:
        result += translit_map.get(char, char)
    
    # Применяем стандартный slugify
    slug = slugify(result)
    
    # Если slug пустой, создаем fallback
    if not slug:
        slug = 'article-' + str(hash(title) % 10000)
    
    return slug

class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(max_length=100, verbose_name="Название тега")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL", blank=True)
    h1_title = models.CharField(max_length=200, verbose_name="Заголовок H1", blank=True)
    meta_title = models.CharField(max_length=200, verbose_name="Meta Title", blank=True)
    meta_description = models.TextField(max_length=500, verbose_name="Meta Description", blank=True)
    
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_slug(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return f'/articles/tag/{self.slug}/'

class Gallery(models.Model):
    """Универсальная модель для галерей всех типов контента"""
    CONTENT_TYPE_CHOICES = [
        ('image', 'Фото'),
        ('video', 'Видео'),
    ]
    
    CATEGORY_CHOICES = [
        ('residential_complex', 'Жилые комплексы'),
        ('secondary_property', 'Вторичная недвижимость'),
        ('employee', 'Сотрудники'),
        ('company', 'Компания'),
        ('article', 'Статьи'),
        ('special_offer', 'Акции'),
        ('office', 'Офисы'),
        ('employee_video', 'Видео сотрудников'),
        ('residential_video', 'Видео жилых комплексов'),
        ('secondary_video', 'Видео вторичной недвижимости'),
        ('future_complex', 'Будущие ЖК'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название")
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES, default='image', verbose_name="Тип контента")
    image = models.ImageField(upload_to='gallery/', verbose_name="Изображение", blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на видео (YouTube)")
    # video_file = models.FileField(upload_to='gallery/videos/', blank=True, null=True, verbose_name="Файл видео")  # Убрано - только ссылки на видео
    video_thumbnail = models.ImageField(upload_to='gallery/thumbnails/', blank=True, null=True, verbose_name="Превью видео")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name="Категория")
    object_id = models.PositiveIntegerField(verbose_name="ID объекта")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    is_main = models.BooleanField(default=False, verbose_name="Главное фото/видео")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Галерея"
        verbose_name_plural = "Галереи"
        ordering = ['category', 'object_id', 'order', 'created_at']
        indexes = [
            models.Index(fields=['category', 'object_id']),
            models.Index(fields=['is_active', 'is_main']),
        ]
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"
    
    def clean(self):
        """Валидация модели"""
        from django.core.exceptions import ValidationError
        
        # Валидация превью видео
        if self.video_thumbnail:
            # Проверяем размер файла (максимум 5MB)
            if self.video_thumbnail.size > 5 * 1024 * 1024:
                raise ValidationError({
                    'video_thumbnail': 'Размер файла превью не должен превышать 5MB.'
                })
            
            # Проверяем, что это изображение (по расширению файла)
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_extension = self.video_thumbnail.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise ValidationError({
                    'video_thumbnail': f'Неподдерживаемый формат файла. Разрешены: {", ".join(allowed_extensions)}'
                })
    
    def save(self, *args, **kwargs):
        """Переопределяем save для выполнения валидации"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_upload_path(self, filename):
        """Автоматическое определение пути загрузки по категории"""
        if self.category == 'residential_complex':
            return f'gallery/residential_complex/{self.object_id}/{filename}'
        elif self.category == 'secondary_property':
            return f'gallery/secondary_property/{self.object_id}/{filename}'
        elif self.category == 'employee':
            return f'gallery/employees/{self.object_id}/{filename}'
        elif self.category == 'company':
            return f'gallery/company/{filename}'
        elif self.category == 'article':
            return f'gallery/articles/{self.object_id}/{filename}'
        elif self.category == 'special_offer':
            return f'gallery/special_offers/{self.object_id}/{filename}'
        elif self.category == 'office':
            return f'gallery/offices/{self.object_id}/{filename}'
        elif self.category == 'employee_video':
            return f'gallery/employee_videos/{self.object_id}/{filename}'
        elif self.category == 'residential_video':
            return f'gallery/residential_videos/{self.object_id}/{filename}'
        elif self.category == 'future_complex':
            return f'gallery/future_complexes/{self.object_id}/{filename}'
        else:
            return f'gallery/{self.category}/{self.object_id}/{filename}'
    
    def save(self, *args, **kwargs):
        # Если это главное фото, убираем главный статус у других фото этого объекта
        if self.is_main:
            Gallery.objects.filter(
                category=self.category,
                object_id=self.object_id,
                is_main=True
            ).exclude(id=self.id).update(is_main=False)
        super().save(*args, **kwargs)


class ResidentialComplex(models.Model):
    """Модель жилого комплекса """
    HOUSE_TYPE_CHOICES = [
        ('apartment', 'Квартира'),
        ('house', 'Дом'),
        ('townhouse', 'Таунхаус'),
        ('penthouse', 'Пентхаус'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Сдан'),
        ('construction', 'Строится'),
    ]

    HOUSE_CLASS_CHOICES = [
        ('economy', 'Эконом-класс'),
        ('comfort', 'Комфорт-класс'),
        ('premium', 'Премиум-класс'),
    ]
    
    FINISHING_CHOICES = [
        ('finished', 'С отделкой'),
        ('unfinished', 'Без отделки'),
    ]
    
    ROOMS_CHOICES = [
        ('1', '1 комната'),
        ('2', '2 комнаты'),
        ('3', '3 комнаты'),
        ('4', '4+ комнаты'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Название ЖК")
    price_from = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена от (млн)")
    city = models.CharField(max_length=100, verbose_name="Город", default="Уфа")
    district = models.CharField(max_length=100, verbose_name="Район", blank=True)
    street = models.CharField(max_length=200, verbose_name="Улица", blank=True)
    commute_time = models.CharField(max_length=50, verbose_name="Время в пути")
    house_type = models.CharField(max_length=20, choices=HOUSE_TYPE_CHOICES, default='apartment', verbose_name="Тип дома")
    area_from = models.DecimalField(max_digits=6, decimal_places=1, default=60.0, verbose_name="Площадь от (м²)")
    area_to = models.DecimalField(max_digits=6, decimal_places=1, default=120.0, verbose_name="Площадь до (м²)")
    delivery_date = models.DateField(blank=True, null=True, verbose_name="Дата сдачи")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='construction', verbose_name="Статус")
    house_class = models.CharField(max_length=20, choices=HOUSE_CLASS_CHOICES, default='comfort', verbose_name="Класс жилья")
    finishing = models.CharField(max_length=20, choices=FINISHING_CHOICES, default='unfinished', verbose_name="Отделка")
    rooms = models.CharField(max_length=10, choices=ROOMS_CHOICES, default='2', verbose_name="Количество комнат")
    
    # Новые поля для детального отображения
    total_apartments = models.IntegerField(default=100, verbose_name="Общее количество квартир")
    completion_start = models.CharField(max_length=20, default="3 кв. 2024", verbose_name="Начало сдачи")
    completion_end = models.CharField(max_length=20, default="4 кв. 2025", verbose_name="Окончание сдачи")
    has_completed = models.BooleanField(default=False, verbose_name="Есть сданные")
    developer = models.CharField(max_length=100, default="Антон Хаус", verbose_name="Застройщик")
    
    # Цены по типам квартир
    studio_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена студии (млн)")
    one_room_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена 1-комнатной (млн)")
    two_room_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена 2-комнатной (млн)")
    three_room_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена 3-комнатной (млн)")
    four_room_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена 4+ комнатной (млн)")
    
    # Витрина каталога: подсветки
    highlight_sale = models.BooleanField(default=False, verbose_name='Подсветить как акцию')
    highlight_recommended = models.BooleanField(default=False, verbose_name='Подсветить как рекомендуюмую')
    
    is_featured = models.BooleanField(default=False, verbose_name="Популярный")
    agent = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='residential_complexes', verbose_name="Ответственный агент")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    latitude = models.FloatField(null=True, blank=True, verbose_name="Широта")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Долгота")
    
    class Meta:
        verbose_name = "Жилой комплекс"
        verbose_name_plural = "Жилые комплексы"
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.name
    

    
    @property
    def price_display(self):
        """Форматированная цена для отображения"""
        return f"от {self.price_from} млн Р"
    
    def get_images(self):
        """Получить все изображения ЖК"""
        return Gallery.objects.filter(
            category='residential_complex',
            object_id=self.id,
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_image(self):
        """Получить главное изображение ЖК"""
        return Gallery.objects.filter(
            category='residential_complex',
            object_id=self.id,
            is_main=True,
            is_active=True
        ).first()
    
    def get_catalog_images(self):
        """Получить изображения для каталога: главное фото + 3 дополнительных по порядку"""
        # Получаем главное изображение
        main_image = self.get_main_image()
        
        # Получаем все изображения, исключая главное
        other_images = Gallery.objects.filter(
            category='residential_complex',
            object_id=self.id,
            is_active=True
        ).exclude(
            id=main_image.id if main_image else None
        ).order_by('order', 'created_at')[:3]
        
        # Формируем список: главное + дополнительные
        catalog_images = []
        if main_image:
            catalog_images.append(main_image)
        catalog_images.extend(other_images)
        
        return catalog_images
    
    def get_videos(self):
        """Получить все видео ЖК"""
        return Gallery.objects.filter(
            category='residential_video',
            object_id=self.id,
            content_type='video',
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_video(self):
        """Получить главное видео ЖК"""
        return Gallery.objects.filter(
            category='residential_video',
            object_id=self.id,
            content_type='video',
            is_main=True,
            is_active=True
        ).first()
    
    def get_related_complexes(self):
        """Получить похожие ЖК"""
        return ResidentialComplex.objects.filter(
            city=self.city,
            house_class=self.house_class
        ).exclude(id=self.id)[:3]

class CompanyInfo(models.Model):
    """Модель информации о компании"""
    founder_name = models.CharField(max_length=100, verbose_name="Имя основателя")
    founder_position = models.CharField(max_length=200, default="основатель компании", verbose_name="Должность основателя")
    company_name = models.CharField(max_length=100, default="Антон Хаус", verbose_name="Название компании")
    quote = models.TextField(verbose_name="Цитата основателя")
    description = models.TextField(blank=True, verbose_name="Описание компании")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    
    class Meta:
        verbose_name = "Информация о компании"
        verbose_name_plural = "Информация о компании"
    
    def __str__(self):
        return f"Информация о {self.company_name}"
    
    @classmethod
    def get_active(cls):
        """Получить активную информацию о компании"""
        return cls.objects.filter(is_active=True).first()
    
    def get_images(self):
        """Получить все изображения компании"""
        return Gallery.objects.filter(
            category='company',
            object_id=self.id,
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_image(self):
        """Получить главное изображение компании"""
        return Gallery.objects.filter(
            category='company',
            object_id=self.id,
            is_main=True,
            is_active=True
        ).first()




class Author(models.Model):
    """Модель автора статьи"""
    name = models.CharField(max_length=100, verbose_name="Имя автора")
    description = models.TextField(blank=True, verbose_name="Описание автора")
    position = models.CharField(max_length=200, blank=True, verbose_name="Должность")
    articles_count = models.IntegerField(default=0, verbose_name="Количество статей")
    total_views = models.IntegerField(default=0, verbose_name="Общее количество просмотров")
    total_likes = models.IntegerField(default=0, verbose_name="Общее количество лайков")
    
    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Category(models.Model):
    """Модель категории статей"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_slug(self.name)
        super().save(*args, **kwargs)

class Article(models.Model):
    """Модель статьи"""
    TYPE_CHOICES = [
        ('news', 'Новости'),
        ('company', 'Новости компании'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    article_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='news', verbose_name="Тип статьи")
    content = HTMLField(verbose_name="Содержание")
    excerpt = HTMLField(max_length=500, verbose_name="Краткое описание")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    published_date = models.DateField(auto_now_add=True, verbose_name="Дата публикации")
    updated_date = models.DateField(auto_now=True, verbose_name="Дата обновления")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемая")
    show_on_home = models.BooleanField(default=False, verbose_name="Показывать на главной")
    views_count = models.IntegerField(default=0, verbose_name="Количество просмотров")
    likes_count = models.IntegerField(default=0, verbose_name="Количество лайков")
    comments_count = models.IntegerField(default=0, verbose_name="Количество комментариев")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL", blank=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Автор")
    tags = models.ManyToManyField('Tag', related_name='articles', blank=True, verbose_name="Теги")
    related_articles = models.ManyToManyField('self', blank=True, verbose_name="Похожие статьи")
    
    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ['-published_date']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_slug(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return f'/articles/{self.slug}/'
    
    def get_images(self):
        """Получить все изображения статьи"""
        return Gallery.objects.filter(
            category='article',
            object_id=self.id,
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_image(self):
        """Получить главное изображение статьи"""
        return Gallery.objects.filter(
            category='article',
            object_id=self.id,
            is_main=True,
            is_active=True
        ).first()

class CatalogLanding(models.Model):
    """SEO-страница каталога (Новостройки/Вторичка + категории)"""
    KIND_CHOICES = [
        ('newbuild', 'Новостройки'),
        ('secondary', 'Вторичная недвижимость'),
    ]

    CATEGORY_CHOICES = [
        ('apartment', 'Квартиры'),
        ('house', 'Дома'),
        ('cottage', 'Коттеджи'),
        ('townhouse', 'Таунхаусы'),
        ('commercial', 'Коммерческие помещения'),
        ('all', 'Все объекты'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название страницы')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, verbose_name='Тип страницы')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='all', verbose_name='Категория')

    meta_title = models.CharField(max_length=255, blank=True, verbose_name='Meta Title')
    meta_description = models.TextField(blank=True, verbose_name='Meta Description')
    meta_keywords = models.CharField(max_length=255, blank=True, verbose_name='Meta Keywords')

    class Meta:
        verbose_name = 'Страница каталога'
        verbose_name_plural = 'Страницы каталога'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/catalog/l/{self.slug}/"

class SecondaryProperty(models.Model):
    """Объект вторичной недвижимости"""
    HOUSE_TYPE_CHOICES = [
        ('apartment', 'Квартира'),
        ('house', 'Частный дом'),
        ('cottage', 'Коттедж'),
        ('townhouse', 'Таунхаус'),
        ('commercial', 'Коммерческое помещение'),
    ]

    ROOMS_CHOICES = ResidentialComplex.ROOMS_CHOICES

    name = models.CharField(max_length=200, verbose_name='Название')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена (млн)')
    city = models.CharField(max_length=100, verbose_name='Город', default='Уфа')
    district = models.CharField(max_length=100, verbose_name='Район', blank=True)
    street = models.CharField(max_length=200, verbose_name='Улица', blank=True)
    commute_time = models.CharField(max_length=50, verbose_name='Время в пути', default='10 минут')

    house_type = models.CharField(max_length=20, choices=HOUSE_TYPE_CHOICES, default='apartment', verbose_name='Тип объекта')
    area = models.DecimalField(max_digits=7, decimal_places=1, default=45.0, verbose_name='Площадь (м²)')
    rooms = models.CharField(max_length=10, choices=ROOMS_CHOICES, default='2', verbose_name='Комнат')

    description = models.TextField(blank=True, verbose_name='Описание')
    agent = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='secondary_properties', verbose_name="Ответственный агент")
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True, verbose_name='Широта')
    longitude = models.FloatField(null=True, blank=True, verbose_name='Долгота')
    
    # Витрина каталога: подсветки
    highlight_sale = models.BooleanField(default=False, verbose_name='Подсветить как акцию')
    highlight_recommended = models.BooleanField(default=False, verbose_name='Подсветить как рекомендуюмую')

    class Meta:
        verbose_name = 'Вторичная недвижимость'
        verbose_name_plural = 'Вторичная недвижимость'
        ordering = ['-created_at']

    def __str__(self):
        return self.name



    @property
    def price_from(self):
        # Для совместимости с шаблоном каталога
        return self.price
    
    def get_images(self):
        """Получить все изображения объекта вторичной недвижимости"""
        return Gallery.objects.filter(
            category='secondary_property',
            object_id=self.id,
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_image(self):
        """Получить главное изображение объекта вторичной недвижимости"""
        # Сначала ищем главное изображение
        main_image = Gallery.objects.filter(
            category='secondary_property',
            object_id=self.id,
            is_main=True,
            is_active=True
        ).first()
        
        # Если главного нет, берем первое доступное
        if not main_image:
            main_image = Gallery.objects.filter(
                category='secondary_property',
                object_id=self.id,
                is_active=True
            ).first()
        
        return main_image
    
    def get_catalog_images(self):
        """Получить изображения для каталога: главное фото + 3 дополнительных по порядку"""
        # Получаем главное изображение
        main_image = self.get_main_image()
        
        # Получаем все изображения, исключая главное
        other_images = Gallery.objects.filter(
            category='secondary_property',
            object_id=self.id,
            is_active=True
        ).exclude(
            id=main_image.id if main_image else None
        ).order_by('order', 'created_at')[:3]
        
        # Формируем список: главное + дополнительные
        catalog_images = []
        if main_image:
            catalog_images.append(main_image)
        catalog_images.extend(other_images)
        
        return catalog_images
    
    def get_videos(self):
        """Получить все видео вторичной недвижимости"""
        return Gallery.objects.filter(
            category='secondary_video',
            object_id=self.id,
            content_type='video',
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_video(self):
        """Получить главное видео вторичной недвижимости"""
        return Gallery.objects.filter(
            category='secondary_video',
            object_id=self.id,
            content_type='video',
            is_main=True,
            is_active=True
        ).first()


class Vacancy(models.Model):
    """Модель вакансии"""
    EMPLOYMENT_CHOICES = [
        ('fulltime', 'Полная занятость'),
        ('parttime', 'Частичная занятость'),
        ('contract', 'Контракт'),
        ('intern', 'Стажировка'),
        ('remote', 'Удаленная работа'),
    ]

    title = models.CharField(max_length=200, verbose_name='Название вакансии')
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='URL')
    department = models.CharField(max_length=120, blank=True, verbose_name='Отдел')
    city = models.CharField(max_length=100, default='Уфа', verbose_name='Город')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, default='fulltime', verbose_name='Тип занятости')

    salary_from = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Зарплата от')
    salary_to = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Зарплата до')
    currency = models.CharField(max_length=10, default='RUB', verbose_name='Валюта')

    description = HTMLField(verbose_name='Описание')
    responsibilities = HTMLField(verbose_name='Обязанности', blank=True)
    requirements = HTMLField(verbose_name='Требования', blank=True)
    benefits = HTMLField(verbose_name='Условия', blank=True)

    contact_email = models.EmailField(default='hr@antonhaus.ru', verbose_name='Email для отклика')

    is_active = models.BooleanField(default=True, verbose_name='Активна')
    published_date = models.DateField(auto_now_add=True, verbose_name='Дата публикации')
    updated_date = models.DateField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-published_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_slug(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f'/vacancies/{self.slug}/'


class BranchOffice(models.Model):
    """Филиал/офис продаж"""
    name = models.CharField(max_length=200, verbose_name='Название офиса')
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='URL')

    city = models.CharField(max_length=100, default='Уфа', verbose_name='Город')
    address = models.CharField(max_length=255, verbose_name='Адрес')
    phone = models.CharField(max_length=50, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    schedule = models.CharField(max_length=255, blank=True, verbose_name='График работы')

    description = HTMLField(blank=True, verbose_name='Описание')

    latitude = models.FloatField(null=True, blank=True, verbose_name='Широта')
    longitude = models.FloatField(null=True, blank=True, verbose_name='Долгота')

    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_head_office = models.BooleanField(default=False, verbose_name='Головной офис')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')

    class Meta:
        verbose_name = 'Офис продаж'
        verbose_name_plural = 'Офисы продаж'
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} ({self.city})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_slug(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f'/offices/{self.slug}/'
    
    def get_images(self):
        """Получить все изображения офиса"""
        return Gallery.objects.filter(
            category='office',
            object_id=self.id,
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_image(self):
        """Получить главное изображение офиса"""
        return Gallery.objects.filter(
            category='office',
            object_id=self.id,
            is_main=True,
            is_active=True
        ).first()


class Employee(models.Model):
    """Сотрудник филиала"""
    branch = models.ForeignKey(BranchOffice, on_delete=models.CASCADE, related_name='employees', verbose_name='Филиал')

    full_name = models.CharField(max_length=200, verbose_name='ФИО')
    position = models.CharField(max_length=150, verbose_name='Должность')
    video_url = models.URLField(blank=True, null=True, verbose_name='Ссылка на видео (YouTube)')
    video_file = models.FileField(upload_to='company/videos/', blank=True, null=True, verbose_name='Файл видео')
    
    experience_years = models.PositiveIntegerField(default=0, verbose_name='Опыт работы (лет)')
    description = HTMLField(blank=True, verbose_name='Описание агента')
    achievements = HTMLField(blank=True, verbose_name='Достижения')
    specializations = models.TextField(blank=True, verbose_name='Специализации')
    
    phone = models.CharField(max_length=50, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    
    is_featured = models.BooleanField(default=False, verbose_name='Рекомендуемый агент')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['-is_featured', 'full_name']

    def __str__(self):
        return self.full_name
    
    def get_absolute_url(self):
        return f'/team/{self.id}/'
    
    @property
    def reviews_count(self):
        """Количество опубликованных отзывов"""
        return self.reviews.filter(is_approved=True).count()
    
    @property
    def average_rating(self):
        """Средний рейтинг по отзывам"""
        approved_reviews = self.reviews.filter(is_approved=True)
        if approved_reviews.exists():
            return round(approved_reviews.aggregate(avg=models.Avg('rating'))['avg'], 1)
        return 0.0
    
    def get_images(self):
        """Получить все изображения сотрудника"""
        return Gallery.objects.filter(
            category='employee',
            object_id=self.id,
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_image(self):
        """Получить главное изображение сотрудника"""
        # Сначала ищем главное изображение
        main_image = Gallery.objects.filter(
            category='employee',
            object_id=self.id,
            is_main=True,
            is_active=True
        ).first()
        
        # Если главного нет, берем первое доступное
        if not main_image:
            main_image = Gallery.objects.filter(
                category='employee',
                object_id=self.id,
                is_active=True
            ).first()
        
        return main_image
    
    def get_videos(self):
        """Получить все видео сотрудника"""
        return Gallery.objects.filter(
            category='employee_video',
            object_id=self.id,
            content_type='video',
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_video(self):
        """Получить главное видео сотрудника"""
        return Gallery.objects.filter(
            category='employee_video',
            object_id=self.id,
            content_type='video',
            is_main=True,
            is_active=True
        ).first()





class EmployeeReview(models.Model):
    """Отзыв о сотруднике"""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reviews', verbose_name='Сотрудник')
    name = models.CharField(max_length=120, verbose_name='Имя клиента')
    email = models.EmailField(blank=True, verbose_name='Email клиента')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон клиента')
    
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5, verbose_name='Оценка')
    text = models.TextField(verbose_name='Текст отзыва')
    
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен')
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Отзыв о сотруднике'
        verbose_name_plural = 'Отзывы о сотрудниках'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} — {self.employee.full_name} ({self.rating}★)'





class MortgageProgram(models.Model):
    """Ипотечная программа (ставка по году)"""
    name = models.CharField(max_length=120, verbose_name='Название программы')
    rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Ставка, % годовых')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Ипотечная программа'
        verbose_name_plural = 'Ипотечные программы'
        ordering = ['rate', 'name']

    def __str__(self):
        return f"{self.name} — {self.rate}%"


class SpecialOffer(models.Model):
    """Акции по жилым комплексам"""
    residential_complex = models.ForeignKey(ResidentialComplex, on_delete=models.CASCADE, related_name='offers', verbose_name='Жилой комплекс')
    title = models.CharField(max_length=200, verbose_name='Заголовок акции')
    description = models.TextField(verbose_name='Описание акции')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    priority = models.IntegerField(default=0, verbose_name='Приоритет')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    expires_at = models.DateTimeField(verbose_name='Дата окончания акции', null=True, blank=True)

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.title} — {self.residential_complex.name}"
    
    @property
    def is_expired(self):
        """Проверяет, истекла ли акция"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_valid(self):
        """Проверяет, активна ли акция и не истекла ли она"""
        return self.is_active and not self.is_expired
    
    @classmethod
    def get_active_offers(cls, limit=6):
        """Получает активные предложения с учетом времени жизни"""
        from django.utils import timezone
        return cls.objects.filter(
            is_active=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).select_related('residential_complex').order_by('?')[:limit]
    
    def get_images(self):
        """Получить все изображения акции"""
        return Gallery.objects.filter(
            category='special_offer',
            object_id=self.id,
            is_active=True
        ).order_by('order', 'created_at')
    
    def get_main_image(self):
        """Получить главное изображение акции"""
        return Gallery.objects.filter(
            category='special_offer',
            object_id=self.id,
            is_main=True,
            is_active=True
        ).first()


class FutureComplex(models.Model):
    """Модель будущих ЖК"""
    name = models.CharField(max_length=200, verbose_name="Название ЖК")
    description = models.TextField(verbose_name="Описание")
    city = models.CharField(max_length=100, verbose_name="Город")
    district = models.CharField(max_length=100, verbose_name="Район", blank=True)
    street = models.CharField(max_length=200, verbose_name="Улица", blank=True)
    delivery_date = models.DateField(verbose_name="Срок сдачи")
    price_from = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена от (млн ₽)")
    price_to = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена до (млн ₽)", null=True, blank=True)
    area_from = models.DecimalField(max_digits=6, decimal_places=1, verbose_name="Площадь от (м²)", null=True, blank=True)
    area_to = models.DecimalField(max_digits=6, decimal_places=1, verbose_name="Площадь до (м²)", null=True, blank=True)
    rooms = models.CharField(max_length=50, verbose_name="Количество комнат", blank=True)
    house_class = models.CharField(max_length=50, verbose_name="Класс дома", blank=True)
    developer = models.CharField(max_length=200, verbose_name="Застройщик", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемый")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Будущий ЖК"
        verbose_name_plural = "Будущие ЖК"
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.name
    
    def get_main_image(self):
        """Получить главное изображение ЖК"""
        return Gallery.objects.filter(
            category='future_complex',
            object_id=self.id,
            is_main=True,
            is_active=True
        ).first()
    
    def get_images(self):
        """Получить все изображения ЖК"""
        return Gallery.objects.filter(
            category='future_complex',
            object_id=self.id,
            is_active=True
        ).order_by('order', 'created_at')
