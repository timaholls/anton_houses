#!/usr/bin/env python3
"""
Скрипт для переноса всех записей из avito_2 в unified_houses
с рандомным агентом и рейтингом 4 или 5
"""

import os
import sys
import random
import time
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import requests

# Подтягиваем корень проекта для импорта модулей
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Настраиваем Django окружение
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')

try:
    import django
    django.setup()
except Exception as e:
    print(f"⚠️  Предупреждение при настройке Django: {e}")

# Импортируем функции из manual_matching_api
try:
    from main.api.manual_matching_api import (
        normalize_coordinate,
        fetch_address_from_coords,
        parse_address_string,
        convert_avito2_apartment_types,
        format_price_number,
        format_price_per_square,
        convert_avito2_apartment_to_unified
    )
except ImportError as e:
    print(f"❌ Не удалось импортировать функции из manual_matching_api: {e}")
    sys.exit(1)


def get_mongo_connection():
    """Получить подключение к MongoDB"""
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:Kfleirb_17@176.98.177.188:27017/admin")
    DB_NAME = os.getenv("DB_NAME", "houses")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db


def format_full_address(city: str, district: str, street: str, house: str) -> str:
    """Форматирует полный адрес"""
    parts = []
    if city:
        parts.append(f"г. {city}")
    if district:
        parts.append(f"р-он {district}")
    if street:
        parts.append(f"ул. {street}")
    if house:
        parts.append(f"д. {house}")
    return ", ".join(parts)


def create_unified_record_from_avito2(avito2_record, agent_id, rating):
    """
    Создает unified_houses запись из avito_2 записи
    Использует логику из save_manual_match
    """
    # Получаем координаты
    avito2_dev = avito2_record.get('development', {})
    latitude = normalize_coordinate(avito2_dev.get('latitude') or avito2_record.get('latitude'))
    longitude = normalize_coordinate(avito2_dev.get('longitude') or avito2_record.get('longitude'))
    
    # Если координат нет - пропускаем
    if latitude is None or longitude is None:
        return None
    
    # Для Avito_2 используем адрес напрямую из development.address (без геокодирования)
    # parse_address_string автоматически обрабатывает слэши в названии улицы
    # (берет только первую часть до слэша, например "ул. Молодежная/Баварская" -> "Молодежная")
    fallback_address = avito2_dev.get('address', '')
    parsed_address = parse_address_string(fallback_address)
    
    # Обрабатываем слэш в полном адресе
    # Если в адресе есть "ул. .../...", берем только "ул. ..." (удаляем все после слэша)
    # Пример: "ул. Молодежная/Баварская, ЖК..." -> "ул. Молодежная"
    import re
    processed_fallback_address = fallback_address
    if processed_fallback_address and '/' in processed_fallback_address:
        # Ищем паттерн "ул. Молодежная/Баварская" или "улица Молодежная/Баварская"
        # Заменяем на "ул. Молодежная" (удаляем все после слэша, включая запятую и все что после)
        pattern = r'(ул\.|улица)\s+([^/]+)/.*'
        processed_fallback_address = re.sub(pattern, r'\1 \2', processed_fallback_address)
    
    # Формируем price_range
    price_range = ''
    price_min = avito2_dev.get('price_range_min')
    price_max = avito2_dev.get('price_range_max')
    if price_min is not None and price_max is not None:
        price_range = f'От {price_min} до {price_max} млн ₽'
    elif price_min is not None:
        price_range = f'От {price_min} млн ₽'
    elif price_max is not None:
        price_range = f'До {price_max} млн ₽'
    
    # Создаем unified запись
    unified_record = {
        'latitude': latitude,
        'longitude': longitude,
        'source': 'migration',
        'created_by': 'migration_script',
        'is_featured': False,
        'rating': rating,
        'rating_description': '',
        'rating_created_at': datetime.now(),
        'rating_updated_at': datetime.now(),
        'agent_id': agent_id if agent_id else None,
    }
    
    # Адрес (используем напрямую из development.address, без геокодирования)
    unified_record['address_full'] = processed_fallback_address
    unified_record['address_city'] = parsed_address.get('city')
    unified_record['address_district'] = parsed_address.get('district')
    unified_record['address_street'] = parsed_address.get('street')
    unified_record['address_house'] = parsed_address.get('house_number')
    unified_record['city'] = unified_record['address_city'] or 'Уфа'
    unified_record['district'] = unified_record['address_district'] or ''
    unified_record['street'] = unified_record['address_street'] or ''
    
    # Development из Avito_2
    unified_record['development'] = {
        'name': avito2_dev.get('name', ''),
        'address': unified_record['address_full'] or avito2_dev.get('address', ''),
        'price_range': price_range,
        'parameters': avito2_dev.get('parameters', {}),
        'korpuses': avito2_dev.get('korpuses', []),
        'photos': avito2_dev.get('photos', [])  # Фото ЖК из development.photos из avito_2
    }
    
    # Ход строительства из Avito_2
    # Ход строительства может быть в development.construction_progress или в корне construction_progress
    # В unified_houses сохраняем в корень construction_progress
    avito2_construction = avito2_dev.get('construction_progress') or avito2_record.get('construction_progress', [])
    if avito2_construction and isinstance(avito2_construction, list):
        unified_record['construction_progress'] = avito2_construction
        # НЕ добавляем фото хода строительства в development.photos
        # Фото хода строительства должны быть только в construction_progress
        # development.photos должны содержать только фото ЖК
    
    # Apartment_types из Avito_2
    avito2_apt_types = avito2_record.get('apartment_types', {})
    unified_record['apartment_types'] = convert_avito2_apartment_types(avito2_apt_types)
    
    # Логируем созданные поля для проверки
    print(f"  📋 Типы квартир в unified_record: {list(unified_record.get('apartment_types', {}).keys())}")
    for apt_type, apt_data in unified_record.get('apartment_types', {}).items():
        apartments = apt_data.get('apartments', [])
        if apartments:
            first_apt = apartments[0]
            print(f"     📋 Тип '{apt_type}', первая квартира:")
            print(f"        - floorMin: {first_apt.get('floorMin')} (тип: {type(first_apt.get('floorMin'))})")
            print(f"        - floorMax: {first_apt.get('floorMax')} (тип: {type(first_apt.get('floorMax'))})")
            print(f"        - totalArea: {first_apt.get('totalArea')} (тип: {type(first_apt.get('totalArea'))})")
            print(f"        - price_value: {first_apt.get('price_value')} (тип: {type(first_apt.get('price_value'))})")
            print(f"        - Все ключи: {list(first_apt.keys())}")
            break  # Показываем только первую квартиру первого типа для краткости
    
    # Сохраняем ссылку на исходную запись
    unified_record['_source_ids'] = {
        'domrf': None,
        'avito': str(avito2_record['_id']),
        'domclick': None
    }
    
    return unified_record


def main():
    """Основная функция"""
    print("🚀 Начинаем миграцию записей из avito_2 в unified_houses...")
    
    db = get_mongo_connection()
    avito2_col = db['avito_2']
    unified_col = db['unified_houses']
    employees_col = db['employees']
    
    # Получаем список активных агентов
    employees = list(employees_col.find({'is_active': True}))
    if not employees:
        print("⚠️  Не найдено активных агентов. Продолжаем без привязки к агенту.")
        agent_ids = [None]
    else:
        agent_ids = [emp['_id'] for emp in employees]
    
    print(f"📋 Найдено агентов: {len(agent_ids)}")
    
    # Получаем все записи из avito_2, которые еще не сопоставлены
    avito2_records = list(avito2_col.find({
        'is_matched': {'$ne': True}
    }))
    
    print(f"📊 Найдено записей в avito_2: {len(avito2_records)}")
    
    if not avito2_records:
        print("✅ Нет записей для миграции")
        return
    
    # Статистика
    success_count = 0
    skipped_count = 0
    error_count = 0
    
    # Обрабатываем каждую запись
    for idx, avito2_record in enumerate(avito2_records, 1):
        try:
            avito_id = str(avito2_record['_id'])
            name = avito2_record.get('development', {}).get('name', 'Без названия')
            
            print(f"\n[{idx}/{len(avito2_records)}] Обрабатываем: {name} (ID: {avito_id})")
            
            # Проверяем, не создана ли уже unified запись для этого avito_2
            existing = unified_col.find_one({
                '_source_ids.avito': avito_id
            })
            
            if existing:
                print(f"  ⏭️  Пропускаем - уже существует unified запись")
                skipped_count += 1
                continue
            
            # Выбираем рандомного агента
            agent_id = random.choice(agent_ids) if agent_ids else None
            
            # Выбираем рандомный рейтинг (4 или 5)
            rating = random.choice([4, 5])
            
            # Создаем unified запись
            unified_record = create_unified_record_from_avito2(avito2_record, agent_id, rating)
            
            if not unified_record:
                print(f"  ⚠️  Пропускаем - нет координат")
                skipped_count += 1
                continue
            
            # Вставляем в unified_houses
            result = unified_col.insert_one(unified_record)
            unified_id = str(result.inserted_id)
            
            # Проверяем что сохранилось в базу
            saved_record = unified_col.find_one({'_id': result.inserted_id})
            if saved_record:
                print(f"  🔍 Проверка сохраненной записи из базы:")
                print(f"     - Типы квартир: {list(saved_record.get('apartment_types', {}).keys())}")
                for apt_type, apt_data in saved_record.get('apartment_types', {}).items():
                    apartments = apt_data.get('apartments', [])
                    if apartments:
                        first_apt = apartments[0]
                        print(f"     📋 Тип '{apt_type}', первая квартира ИЗ БАЗЫ:")
                        print(f"        - floorMin: {first_apt.get('floorMin')} (тип: {type(first_apt.get('floorMin'))})")
                        print(f"        - floorMax: {first_apt.get('floorMax')} (тип: {type(first_apt.get('floorMax'))})")
                        print(f"        - totalArea: {first_apt.get('totalArea')} (тип: {type(first_apt.get('totalArea'))})")
                        print(f"        - price_value: {first_apt.get('price_value')} (тип: {type(first_apt.get('price_value'))})")
                        print(f"        - Все ключи: {list(first_apt.keys())}")
                        break  # Показываем только первую квартиру первого типа для краткости
            
            # Помечаем исходную запись как сопоставленную
            avito2_col.update_one(
                {'_id': avito2_record['_id']},
                {'$set': {
                    'is_matched': True,
                    'matched_unified_id': result.inserted_id,
                    'matched_at': datetime.now()
                }}
            )
            
            agent_name = "нет" if not agent_id else "выбран"
            print(f"  ✅ Создано! Unified ID: {unified_id}, Агент: {agent_name}, Рейтинг: {rating}")
            success_count += 1
            
            # Небольшая задержка для геокодирования
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            error_count += 1
            import traceback
            traceback.print_exc()
    
    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"  ✅ Успешно создано: {success_count}")
    print(f"  ⏭️  Пропущено: {skipped_count}")
    print(f"  ❌ Ошибок: {error_count}")
    print(f"  📝 Всего обработано: {len(avito2_records)}")
    print("="*60)


if __name__ == "__main__":
    main()

