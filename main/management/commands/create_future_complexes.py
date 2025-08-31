from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random
from main.models import FutureComplex


class Command(BaseCommand):
    help = 'Создает тестовые данные для будущих ЖК'

    def handle(self, *args, **options):
        # Проверяем, есть ли уже данные
        if FutureComplex.objects.exists():
            self.stdout.write(
                self.style.WARNING('Данные FutureComplex уже существуют!')
            )
            return

        # Данные для создания тестовых ЖК
        future_complexes_data = [
            {
                'name': 'ЖК "Солнечный Берег"',
                'description': 'Современный жилой комплекс с видом на реку. Развитая инфраструктура, детские сады, школы, торговые центры в шаговой доступности.',
                'city': 'Уфа',
                'district': 'Калининский район',
                'street': 'ул. Менделеева',
                'delivery_date': date.today() + timedelta(days=365),
                'price_from': 3.2,
                'price_to': 8.5,
                'area_from': 35.0,
                'area_to': 120.0,
                'rooms': '1-4 комнаты',
                'house_class': 'Комфорт',
                'developer': 'ООО "СтройИнвест"',
                'is_featured': True
            },
            {
                'name': 'ЖК "Зеленый Парк"',
                'description': 'Экологичный проект в зеленой зоне города. Собственный парк, спортивные площадки, подземная парковка.',
                'city': 'Уфа',
                'district': 'Октябрьский район',
                'street': 'ул. Парковая',
                'delivery_date': date.today() + timedelta(days=730),
                'price_from': 4.1,
                'price_to': 12.0,
                'area_from': 42.0,
                'area_to': 150.0,
                'rooms': 'Студия, 1-5 комнаты',
                'house_class': 'Премиум',
                'developer': 'АО "УфаСтрой"',
                'is_featured': True
            },
            {
                'name': 'ЖК "Центральный"',
                'description': 'Жилой комплекс в самом центре города. Отличная транспортная доступность, рядом все основные достопримечательности.',
                'city': 'Уфа',
                'district': 'Ленинский район',
                'street': 'ул. Ленина',
                'delivery_date': date.today() + timedelta(days=548),
                'price_from': 5.8,
                'price_to': 15.0,
                'area_from': 28.0,
                'area_to': 110.0,
                'rooms': 'Студия, 1-3 комнаты',
                'house_class': 'Бизнес',
                'developer': 'ООО "ЦентрСтрой"',
                'is_featured': False
            },
            {
                'name': 'ЖК "Речной"',
                'description': 'Жилой комплекс на берегу реки Белой. Панорамные окна, современная архитектура, закрытая территория.',
                'city': 'Уфа',
                'district': 'Советский район',
                'street': 'ул. Набережная',
                'delivery_date': date.today() + timedelta(days=456),
                'price_from': 6.2,
                'price_to': 18.0,
                'area_from': 45.0,
                'area_to': 140.0,
                'rooms': '1-4 комнаты',
                'house_class': 'Премиум',
                'developer': 'ООО "РекаСтрой"',
                'is_featured': True
            },
            {
                'name': 'ЖК "Университетский"',
                'description': 'Жилой комплекс рядом с университетом. Идеально для студентов и преподавателей. Развитая инфраструктура.',
                'city': 'Уфа',
                'district': 'Калининский район',
                'street': 'ул. Зорге',
                'delivery_date': date.today() + timedelta(days=365),
                'price_from': 2.8,
                'price_to': 7.5,
                'area_from': 30.0,
                'area_to': 95.0,
                'rooms': 'Студия, 1-3 комнаты',
                'house_class': 'Эконом',
                'developer': 'ООО "УниверситетСтрой"',
                'is_featured': False
            },
            {
                'name': 'ЖК "Авиационный"',
                'description': 'Жилой комплекс в авиационном районе. Рядом аэропорт, удобная транспортная развязка.',
                'city': 'Уфа',
                'district': 'Октябрьский район',
                'street': 'ул. Авиационная',
                'delivery_date': date.today() + timedelta(days=638),
                'price_from': 3.5,
                'price_to': 9.8,
                'area_from': 38.0,
                'area_to': 125.0,
                'rooms': '1-4 комнаты',
                'house_class': 'Комфорт',
                'developer': 'ООО "АвиаСтрой"',
                'is_featured': False
            },
            {
                'name': 'ЖК "Лесной"',
                'description': 'Экологичный проект в лесной зоне. Чистый воздух, тишина, собственная инфраструктура.',
                'city': 'Уфа',
                'district': 'Советский район',
                'street': 'ул. Лесная',
                'delivery_date': date.today() + timedelta(days=912),
                'price_from': 4.8,
                'price_to': 13.5,
                'area_from': 50.0,
                'area_to': 160.0,
                'rooms': '2-5 комнаты',
                'house_class': 'Премиум',
                'developer': 'ООО "ЛесСтрой"',
                'is_featured': True
            },
            {
                'name': 'ЖК "Спортивный"',
                'description': 'Жилой комплекс рядом со спортивными объектами. Фитнес-центр, бассейн, спортивные площадки.',
                'city': 'Уфа',
                'district': 'Ленинский район',
                'street': 'ул. Спортивная',
                'delivery_date': date.today() + timedelta(days=548),
                'price_from': 3.9,
                'price_to': 11.2,
                'area_from': 40.0,
                'area_to': 130.0,
                'rooms': '1-4 комнаты',
                'house_class': 'Комфорт',
                'developer': 'ООО "СпортСтрой"',
                'is_featured': False
            },
            {
                'name': 'ЖК "Медицинский"',
                'description': 'Жилой комплекс рядом с медицинскими учреждениями. Идеально для медицинских работников.',
                'city': 'Уфа',
                'district': 'Калининский район',
                'street': 'ул. Медицинская',
                'delivery_date': date.today() + timedelta(days=456),
                'price_from': 4.2,
                'price_to': 10.8,
                'area_from': 35.0,
                'area_to': 115.0,
                'rooms': '1-3 комнаты',
                'house_class': 'Комфорт',
                'developer': 'ООО "МедСтрой"',
                'is_featured': False
            },
            {
                'name': 'ЖК "Торговый"',
                'description': 'Жилой комплекс рядом с крупными торговыми центрами. Удобно для покупок и развлечений.',
                'city': 'Уфа',
                'district': 'Октябрьский район',
                'street': 'ул. Торговая',
                'delivery_date': date.today() + timedelta(days=730),
                'price_from': 3.6,
                'price_to': 9.5,
                'area_from': 32.0,
                'area_to': 105.0,
                'rooms': 'Студия, 1-3 комнаты',
                'house_class': 'Комфорт',
                'developer': 'ООО "ТоргСтрой"',
                'is_featured': False
            }
        ]

        # Создаем записи
        created_count = 0
        for data in future_complexes_data:
            future_complex = FutureComplex.objects.create(**data)
            self.stdout.write(f'Создан ЖК: {future_complex.name}')
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано {created_count} будущих ЖК!'
            )
        )
