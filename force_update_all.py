#!/usr/bin/env python3
"""
Скрипт для принудительного обновления всех объединенных записей с исправленным маппингом
"""

import os
import sys
import django
from bson import ObjectId
from datetime import datetime, timezone

# Настройка Django
sys.path.append('/home/art/PycharmProjects/anton_houses')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from pymongo import MongoClient
from django.conf import settings


def get_mongo_connection():
    """Получить подключение к MongoDB из настроек проекта."""
    uri = getattr(settings, 'MONGO_URI', 'mongodb://root:Kfleirb_17@176.98.177.188:27017/admin')
    db_name = getattr(settings, 'DB_NAME', 'houses')
    client = MongoClient(uri)
    return client[db_name]


def rebuild_unified_record(unified_record):
    """Пересоздает объединенную запись с исправленным маппингом"""
    db = get_mongo_connection()

    # Получаем исходные записи
    source_ids = unified_record.get('_source_ids', {})

    domrf_record = None
    if source_ids.get('domrf'):
        try:
            domrf_record = db['domrf'].find_one({'_id': ObjectId(source_ids['domrf'])})
        except Exception as e:
            print(f"❌ Error getting DomRF: {e}")

    avito_record = None
    if source_ids.get('avito'):
        try:
            avito_record = db['avito'].find_one({'_id': ObjectId(source_ids['avito'])})
        except Exception as e:
            print(f"❌ Error getting Avito: {e}")

    domclick_record = None
    if source_ids.get('domclick'):
        try:
            domclick_record = db['domclick'].find_one({'_id': ObjectId(source_ids['domclick'])})
        except Exception as e:
            print(f"❌ Error getting DomClick: {e}")

    # Проверяем, что у нас есть хотя бы одна запись
    if not avito_record and not domclick_record:
        print(f"❌ Нет исходных записей для unified_record {unified_record['_id']}")
        return None

    # Определяем координаты (приоритет: DomRF > Avito > DomClick > существующие в unified_record)
    latitude = None
    longitude = None

    if domrf_record:
        latitude = domrf_record.get('latitude')
        longitude = domrf_record.get('longitude')
    elif avito_record:
        avito_dev = avito_record.get('development', {})
        latitude = avito_dev.get('latitude')
        longitude = avito_dev.get('longitude')
    elif domclick_record:
        domclick_dev = domclick_record.get('development', {})
        latitude = domclick_dev.get('latitude')
        longitude = domclick_dev.get('longitude')
    else:
        latitude = unified_record.get('latitude')
        longitude = unified_record.get('longitude')

    # Создаем новую запись
    new_record = {
        'latitude': latitude,
        'longitude': longitude,
        'source': 'unified',
        'created_by': 'script',
        'is_featured': unified_record.get('is_featured', False),
        'agent_id': unified_record.get('agent_id'),
        'updated_at': datetime.now(timezone.utc)
    }

    # 1. Development из Avito + photos и construction_progress из DomClick
    if avito_record:
        avito_dev = avito_record.get('development', {})
        if isinstance(avito_dev, dict):
            new_record['development'] = {
                'name': avito_dev.get('name', ''),
                'address': avito_dev.get('address', ''),
                'price_range': avito_dev.get('price_range', ''),
                'parameters': avito_dev.get('parameters', {}),
                'korpuses': avito_dev.get('korpuses', []),
                'photos': []  # Будет заполнено из DomClick
            }

            # Добавляем фото ЖК из DomClick
            if domclick_record:
                domclick_dev = domclick_record.get('development', {})
                if domclick_dev.get('photos'):
                    new_record['development']['photos'] = domclick_dev['photos']
                # Ход строительства: development.construction_progress или корень
                dc_construction = domclick_dev.get('construction_progress') or domclick_record.get('construction_progress')
                if dc_construction:
                    new_record['construction_progress'] = dc_construction

    # 2. Объединяем apartment_types с ИСПРАВЛЕННЫМ маппингом
    new_record['apartment_types'] = {}

    if avito_record and domclick_record:
        avito_apt_types = avito_record.get('apartment_types', {})
        domclick_apt_types = domclick_record.get('apartment_types', {})

        # ИСПРАВЛЕННЫЙ маппинг
        name_mapping = {
            'Студия': 'Студия',
            '1 ком.': '1',
            '1-комн': '1',
            '1-комн.': '1',
            '2 ком.': '2',  # ← ИСПРАВЛЕНО
            '2': '2',
            '2-комн': '2',
            '2-комн.': '2',
            '3': '3',
            '3-комн': '3',
            '3-комн.': '3',
            '4': '4',
            '4-комн': '4',
            '4-комн.': '4',
            '4-комн.+': '4',
            '4-комн+': '4'
        }

        # Сначала обрабатываем все типы из DomClick (чтобы не пропустить 1-комнатные)
        processed_types = set()

        for dc_type_name, dc_type_data in domclick_apt_types.items():
            # Упрощаем название типа
            simplified_name = name_mapping.get(dc_type_name, dc_type_name)

            # Пропускаем если уже обработали этот упрощенный тип
            if simplified_name in processed_types:
                continue
            processed_types.add(simplified_name)

            # Получаем квартиры из DomClick
            dc_apartments = dc_type_data.get('apartments', [])
            if not dc_apartments:
                continue

            # Ищем соответствующий тип в Avito
            avito_apartments = []
            for avito_type_name, avito_data in avito_apt_types.items():
                avito_simplified = name_mapping.get(avito_type_name, avito_type_name)
                if avito_simplified == simplified_name:
                    avito_apartments = avito_data.get('apartments', [])
                    break

            # ИЗМЕНЕНО: Добавляем тип только если есть данные в Avito
            if not avito_apartments:
                continue  # Пропускаем тип, если нет данных в Avito

            # Объединяем: количество квартир = количество квартир в DomClick
            combined_apartments = []

            for i, dc_apt in enumerate(dc_apartments):
                # Получаем ВСЕ фото этой квартиры из DomClick как МАССИВ
                apartment_photos = dc_apt.get('photos', [])

                # Если фото нет - пропускаем эту квартиру
                if not apartment_photos:
                    continue

                # Берем соответствующую квартиру из Avito (циклически)
                avito_apt = avito_apartments[i % len(avito_apartments)]

                combined_apartments.append({
                    'title': avito_apt.get('title', ''),
                    'price': avito_apt.get('price', ''),
                    'pricePerSquare': avito_apt.get('pricePerSquare', ''),
                    'completionDate': avito_apt.get('completionDate', ''),
                    'url': avito_apt.get('urlPath', ''),
                    'image': apartment_photos  # МАССИВ всех фото этой планировки!
                })

            # Добавляем в результат только если есть квартиры с фото И данными из Avito
            if combined_apartments:
                new_record['apartment_types'][simplified_name] = {
                    'apartments': combined_apartments
                }

    # 3. Сохраняем ссылки на исходные записи
    new_record['_source_ids'] = source_ids

    return new_record


def main():
    """Принудительное обновление всех объединенных записей"""
    print("🔄 ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ ВСЕХ ОБЪЕДИНЕННЫХ ЗАПИСЕЙ")
    print("=" * 60)

    db = get_mongo_connection()
    unified_col = db['unified_houses']

    # Получаем все объединенные записи
    unified_records = list(unified_col.find({}))
    total_records = len(unified_records)

    print(f"📊 Найдено {total_records} объединенных записей")

    updated_count = 0
    error_count = 0

    for i, record in enumerate(unified_records, 1):
        try:
            record_name = record.get('development', {}).get('name', 'Без названия')
            print(f"\n[{i}/{total_records}] Обрабатываем: {record_name}")

            # Пересоздаем запись с исправленным маппингом
            new_record = rebuild_unified_record(record)

            if new_record:
                # Заменяем старую запись новой
                result = unified_col.replace_one(
                    {'_id': record['_id']},
                    new_record
                )

                if result.modified_count == 1:
                    print(f"✅ Запись обновлена")
                    updated_count += 1
                else:
                    print(f"⚠️ Запись не изменилась")
            else:
                print(f"❌ Не удалось пересоздать запись")
                error_count += 1

        except Exception as e:
            print(f"❌ Ошибка при обработке записи {i}: {e}")
            error_count += 1

    print(f"\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ПРИНУДИТЕЛЬНОГО ОБНОВЛЕНИЯ:")
    print(f"✅ Обновлено: {updated_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"📈 Всего обработано: {total_records}")
    print("🏁 ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ ЗАВЕРШЕНО")


if __name__ == "__main__":
    main()
