import random
from django.core.management.base import BaseCommand
from django.db import models
from main.models import ResidentialComplex, SecondaryProperty, BranchOffice


class Command(BaseCommand):
    help = 'Добавляет случайные координаты районов Уфы для ЖК, вторички и офисов продаж'

    def handle(self, *args, **options):
        # Примерные координаты разных районов Уфы
        ufa_districts = [
            # Центральный район
            (54.7388, 55.9721),  # Центр
            (54.7350, 55.9580),  # Ленинский район
            (54.7420, 55.9850),  # Советский район
            
            # Калининский район
            (54.7180, 55.9420),
            (54.7250, 55.9380),
            (54.7320, 55.9460),
            
            # Кировский район
            (54.7580, 55.9180),
            (54.7620, 55.9240),
            (54.7480, 55.9120),
            
            # Орджоникидзевский район
            (54.7680, 55.9680),
            (54.7720, 55.9750),
            (54.7640, 55.9580),
            
            # Октябрьский район
            (54.7080, 55.9980),
            (54.7120, 56.0020),
            (54.7040, 55.9920),
            
            # Демский район
            (54.6980, 55.9380),
            (54.6920, 55.9420),
            (54.7020, 55.9340),
        ]
        
        def randomize_coords():
            lat, lng = random.choice(ufa_districts)
            lat += random.uniform(-0.01, 0.01)
            lng += random.uniform(-0.01, 0.01)
            return round(lat, 6), round(lng, 6)
        
        # Обновляем координаты для жилых комплексов
        complexes = ResidentialComplex.objects.filter(
            models.Q(latitude__isnull=True) | models.Q(longitude__isnull=True)
        )
        updated_complexes = 0
        for complex in complexes:
            lat, lng = randomize_coords()
            complex.latitude = lat
            complex.longitude = lng
            complex.save(update_fields=['latitude', 'longitude'])
            updated_complexes += 1
            self.stdout.write(f'ЖК "{complex.name}": {complex.latitude}, {complex.longitude}')
        
        # Обновляем координаты для вторичной недвижимости
        properties = SecondaryProperty.objects.filter(
            models.Q(latitude__isnull=True) | models.Q(longitude__isnull=True)
        )
        updated_properties = 0
        for property in properties:
            lat, lng = randomize_coords()
            property.latitude = lat
            property.longitude = lng
            property.save(update_fields=['latitude', 'longitude'])
            updated_properties += 1
            self.stdout.write(f'Вторичка "{property.name}": {property.latitude}, {property.longitude}')
        
        # Обновляем координаты для офисов продаж
        offices = BranchOffice.objects.filter(
            models.Q(latitude__isnull=True) | models.Q(longitude__isnull=True)
        )
        updated_offices = 0
        for office in offices:
            lat, lng = randomize_coords()
            office.latitude = lat
            office.longitude = lng
            office.save(update_fields=['latitude', 'longitude'])
            updated_offices += 1
            self.stdout.write(f'Офис "{office.name}": {office.latitude}, {office.longitude}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Обновлено координат: {updated_complexes} ЖК, {updated_properties} вторичных объектов, {updated_offices} офисов'
            )
        )
