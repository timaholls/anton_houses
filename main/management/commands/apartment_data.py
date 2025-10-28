from django.core.management.base import BaseCommand
from bson import ObjectId
from main.services.mongo_service import get_mongo_connection
import json


class Command(BaseCommand):
    help = 'Получить данные квартиры из MongoDB для анализа структуры'

    def add_arguments(self, parser):
        parser.add_argument('--complex-id', type=str, help='ID ЖК')
        parser.add_argument('--apartment-id', type=str, help='ID квартиры')
        parser.add_argument('--limit', type=int, default=5, help='Количество квартир для показа')

    def handle(self, *args, **options):
        db = get_mongo_connection()
        
        # Если не указан ID ЖК, показываем первые несколько ЖК
        if not options['complex_id']:
            self.stdout.write("=== ПОИСК ЖК С КВАРТИРАМИ ===")
            complexes = list(db['unified_houses'].find({}).limit(10))
            
            for complex_doc in complexes:
                complex_id = str(complex_doc.get('_id'))
                complex_name = complex_doc.get('name', 'Без названия')
                
                # Проверяем есть ли квартиры
                apartment_types = complex_doc.get('apartment_types', {})
                total_apartments = 0
                for apt_type, apt_data in apartment_types.items():
                    apartments = apt_data.get('apartments', [])
                    total_apartments += len(apartments)
                
                if total_apartments > 0:
                    self.stdout.write(f"ID: {complex_id}")
                    self.stdout.write(f"Название: {complex_name}")
                    self.stdout.write(f"Квартир: {total_apartments}")
                    self.stdout.write("-" * 50)
            
            return
        
        # Получаем конкретный ЖК
        complex_id = options['complex_id']
        try:
            complex_doc = db['unified_houses'].find_one({'_id': ObjectId(complex_id)})
        except:
            self.stdout.write(f"Ошибка: Неверный ID ЖК {complex_id}")
            return
        
        if not complex_doc:
            self.stdout.write(f"ЖК с ID {complex_id} не найден")
            return
        
        self.stdout.write("=== ДАННЫЕ ЖК ===")
        self.stdout.write(f"ID: {complex_id}")
        self.stdout.write(f"Название: {complex_doc.get('name', 'Без названия')}")
        self.stdout.write(f"Город: {complex_doc.get('city', 'Не указан')}")
        self.stdout.write(f"Район: {complex_doc.get('district', 'Не указан')}")
        self.stdout.write(f"Улица: {complex_doc.get('street', 'Не указана')}")
        
        # Проверяем структуру данных
        self.stdout.write("\n=== СТРУКТУРА ДАННЫХ ===")
        self.stdout.write(f"Ключи в документе: {list(complex_doc.keys())}")
        
        # Анализируем apartment_types
        apartment_types = complex_doc.get('apartment_types', {})
        self.stdout.write(f"\n=== APARTMENT_TYPES ===")
        self.stdout.write(f"Типов квартир: {len(apartment_types)}")
        
        apartment_count = 0
        for apt_type, apt_data in apartment_types.items():
            apartments = apt_data.get('apartments', [])
            apartment_count += len(apartments)
            self.stdout.write(f"Тип {apt_type}: {len(apartments)} квартир")
        
        self.stdout.write(f"Всего квартир: {apartment_count}")
        
        # Показываем детали первых квартир
        self.stdout.write(f"\n=== ДЕТАЛИ КВАРТИР (первые {options['limit']}) ===")
        
        shown_count = 0
        for apt_type, apt_data in apartment_types.items():
            apartments = apt_data.get('apartments', [])
            
            for i, apt in enumerate(apartments):
                if shown_count >= options['limit']:
                    break
                
                self.stdout.write(f"\n--- Квартира {shown_count + 1} ---")
                self.stdout.write(f"Тип: {apt_type}")
                self.stdout.write(f"Индекс в типе: {i}")
                self.stdout.write(f"ID: {apt.get('_id', 'Нет')}")
                self.stdout.write(f"Ключи квартиры: {list(apt.keys())}")
                
                # Показываем основные поля
                for field in ['title', 'rooms', 'totalArea', 'floor', 'price', 'pricePerSqm', 
                             'layout', 'balcony', 'loggia', 'view', 'condition', 'furniture',
                             'ceilingHeight', 'windows', 'bathroom', 'kitchenArea', 
                             'livingArea', 'bedroomArea', 'description']:
                    value = apt.get(field, '')
                    if value:
                        self.stdout.write(f"  {field}: {value}")
                
                # Показываем фото
                photos = apt.get('photos', [])
                image = apt.get('image', [])
                if photos:
                    self.stdout.write(f"  photos: {len(photos)} фото")
                    if len(photos) > 0:
                        self.stdout.write(f"    Первое фото: {photos[0]}")
                if image:
                    self.stdout.write(f"  image: {len(image) if isinstance(image, list) else 'строка'}")
                    if isinstance(image, list) and len(image) > 0:
                        self.stdout.write(f"    Первое изображение: {image[0]}")
                
                shown_count += 1
        
        # Если указан конкретный ID квартиры
        if options['apartment_id']:
            self.stdout.write(f"\n=== ПОИСК КОНКРЕТНОЙ КВАРТИРЫ {options['apartment_id']} ===")
            
            apartment_found = False
            for apt_type, apt_data in apartment_types.items():
                apartments = apt_data.get('apartments', [])
                
                for i, apt in enumerate(apartments):
                    apt_id = apt.get('_id')
                    generated_id = f"{apt_type}_{i}"
                    
                    if str(apt_id) == options['apartment_id'] or generated_id == options['apartment_id']:
                        self.stdout.write(f"НАЙДЕНА КВАРТИРА!")
                        self.stdout.write(f"Тип: {apt_type}")
                        self.stdout.write(f"Индекс: {i}")
                        self.stdout.write(f"Оригинальный ID: {apt_id}")
                        self.stdout.write(f"Сгенерированный ID: {generated_id}")
                        self.stdout.write(f"Полные данные:")
                        self.stdout.write(json.dumps(apt, indent=2, ensure_ascii=False, default=str))
                        apartment_found = True
                        break
                
                if apartment_found:
                    break
            
            if not apartment_found:
                self.stdout.write(f"Квартира с ID {options['apartment_id']} не найдена")
        
        self.stdout.write("\n=== КОМАНДЫ ДЛЯ ТЕСТИРОВАНИЯ ===")
        self.stdout.write(f"python manage.py apartment_data --complex-id {complex_id}")
        self.stdout.write(f"python manage.py apartment_data --complex-id {complex_id} --apartment-id 2_0")
        self.stdout.write(f"python manage.py apartment_data --complex-id {complex_id} --limit 10")
