from django.db import models

# Create your models here.

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
