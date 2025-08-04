from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField
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

class ResidentialComplex(models.Model):
    """Модель жилого комплекса"""
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
    image = models.ImageField(upload_to='complexes/', blank=True, null=True, verbose_name="Изображение")
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
    
    # Дополнительные изображения
    image_2 = models.ImageField(upload_to='complexes/', blank=True, null=True, verbose_name="Изображение 2")
    image_3 = models.ImageField(upload_to='complexes/', blank=True, null=True, verbose_name="Изображение 3")
    image_4 = models.ImageField(upload_to='complexes/', blank=True, null=True, verbose_name="Изображение 4")
    
    is_featured = models.BooleanField(default=False, verbose_name="Популярный")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
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

class CompanyInfo(models.Model):
    """Модель информации о компании"""
    founder_name = models.CharField(max_length=100, verbose_name="Имя основателя")
    founder_photo = models.ImageField(upload_to='company/', blank=True, null=True, verbose_name="Фото основателя")
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

class Author(models.Model):
    """Модель автора статьи"""
    name = models.CharField(max_length=100, verbose_name="Имя автора")
    photo = models.ImageField(upload_to='authors/', blank=True, null=True, verbose_name="Фото автора")
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

class Article(models.Model):
    """Модель статьи"""
    CATEGORY_CHOICES = [
        ('mortgage', 'Ипотека'),
        ('laws', 'Законы'),
        ('instructions', 'Инструкции'),
        ('market', 'Рынок недвижимости'),
        ('tips', 'Советы'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = RichTextField(verbose_name="Содержание", config_name='article')
    excerpt = RichTextField(max_length=500, verbose_name="Краткое описание", config_name='default')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='tips', verbose_name="Категория")
    image = models.ImageField(upload_to='articles/', blank=True, null=True, verbose_name="Изображение")
    published_date = models.DateField(auto_now_add=True, verbose_name="Дата публикации")
    updated_date = models.DateField(auto_now=True, verbose_name="Дата обновления")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемая")
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
