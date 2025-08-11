# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from main.models import SecondaryProperty
from decimal import Decimal
import random

NAMES = {
    'apartment': ['2-к квартира на Ленина', '1-к квартира в центре', '3-к квартира у парка'],
    'house': ['Частный дом в Затоне', 'Дом в Спортивном районе'],
    'cottage': ['Коттедж в Уфимском районе', 'Коттедж в сосновом бору'],
    'townhouse': ['Таунхаус у набережной', 'Таунхаус в quiet-районе'],
    'commercial': ['Торговое помещение на первом этаже', 'Офис в бизнес-центре'],
}

class Command(BaseCommand):
    help = 'Создает демонстрационные объекты вторичной недвижимости'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20, help='Количество объектов')

    def handle(self, *args, **options):
        count = options['count']
        created = 0
        for _ in range(count):
            category = random.choice(list(NAMES.keys()))
            name = random.choice(NAMES[category])
            price = Decimal(random.randrange(150, 1500)) / Decimal('10')  # 15.0–150.0 млн
            rooms = random.choice(['1', '2', '3', '4'])
            area = Decimal(random.randrange(30, 250))
            city = 'Уфа'
            district = random.choice(['Октябрьский', 'Кировский', 'Дёмский', 'Советский'])
            street = random.choice(['ул. Ленина', 'ул. Комсомольская', 'пр. Салавата', 'ул. Республики'])

            SecondaryProperty.objects.create(
                name=name,
                price=price,
                city=city,
                district=district,
                street=street,
                house_type=category,
                rooms=rooms,
                area=area,
                commute_time=f"{random.randrange(5,30)} минут",
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Создано объектов: {created}')) 