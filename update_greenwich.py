#!/usr/bin/env python3
"""
Скрипт для обновления конкретной записи Greenwich с исправленным маппингом
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

def update_greenwich_record():
    """Обновить запись Greenwich с исправленным маппингом"""
    print("🔄 ОБНОВЛЕНИЕ ЗАПИСИ GREENWICH")
    print("=" * 50)
    
    db = get_mongo_connection()
    unified_col = db['unified_houses']
    
    # Находим запись Greenwich
    greenwich_unified = unified_col.find_one({'development.name': 'ЖК «Greenwich»'})
    
    if not greenwich_unified:
        print("❌ Запись Greenwich не найдена")
        return
    
    print(f"✅ Найдена запись: {greenwich_unified['_id']}")
    
    # Получаем исходные записи
    source_ids = greenwich_unified.get('_source_ids', {})
    
    avito_record = None
    if source_ids.get('avito'):
        avito_col = db['avito']
        avito_record = avito_col.find_one({'_id': ObjectId(source_ids['avito'])})
        print(f"📱 Avito запись: {bool(avito_record)}")
    
    domclick_record = None
    if source_ids.get('domclick'):
        domclick_col = db['domclick']
        domclick_record = domclick_col.find_one({'_id': ObjectId(source_ids['domclick'])})
        print(f"🏗️ DomClick запись: {bool(domclick_record)}")
    
    if not avito_record or not domclick_record:
        print("❌ Не найдены исходные записи")
        return
    
    # Создаем новую объединенную запись с исправленным маппингом
    print(f"\n🔄 Пересоздаем объединенную запись...")
    
    # 1. Основная информация
    new_record = {
        'latitude': greenwich_unified.get('latitude'),
        'longitude': greenwich_unified.get('longitude'),
        'source': 'unified',
        'created_by': 'script',
        'is_featured': greenwich_unified.get('is_featured', False),
        'agent_id': greenwich_unified.get('agent_id'),
        'updated_at': datetime.now(timezone.utc),
        '_source_ids': source_ids
    }
    
    # 2. Development из Avito
    avito_dev = avito_record.get('development', {})
    new_record['development'] = {
        'name': avito_dev.get('name', ''),
        'address': avito_dev.get('address', ''),
        'price_range': avito_dev.get('price_range', ''),
        'parameters': avito_dev.get('parameters', {}),
        'korpuses': avito_dev.get('korpuses', []),
        'photos': []  # Будет заполнено из DomClick
    }
    
    # Добавляем фото ЖК из DomClick
    domclick_dev = domclick_record.get('development', {})
    if domclick_dev.get('photos'):
        new_record['development']['photos'] = domclick_dev['photos']
    
    # 3. Объединяем apartment_types с ИСПРАВЛЕННЫМ маппингом
    new_record['apartment_types'] = {}
    
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
    
    processed_types = set()
    changes = []
    
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
                print(f"✅ Найден тип '{simplified_name}': DomClick '{dc_type_name}' + Avito '{avito_type_name}' ({len(avito_apartments)} квартир)")
                break
        
        # Объединяем: количество квартир = количество квартир в DomClick
        combined_apartments = []
        
        for i, dc_apt in enumerate(dc_apartments):
            # Получаем ВСЕ фото этой квартиры из DomClick как МАССИВ
            apartment_photos = dc_apt.get('photos', [])
            
            # Если фото нет - пропускаем эту квартиру
            if not apartment_photos:
                continue
            
            # Берем соответствующую квартиру из Avito (циклически)
            avito_apt = avito_apartments[i % len(avito_apartments)] if avito_apartments else {}
            
            combined_apartments.append({
                'title': avito_apt.get('title', ''),
                'price': avito_apt.get('price', ''),
                'pricePerSquare': avito_apt.get('pricePerSquare', ''),
                'completionDate': avito_apt.get('completionDate', ''),
                'url': avito_apt.get('urlPath', ''),
                'image': apartment_photos  # МАССИВ всех фото этой планировки!
            })
        
        # Добавляем в результат только если есть квартиры с фото
        if combined_apartments:
            new_record['apartment_types'][simplified_name] = {
                'apartments': combined_apartments
            }
            changes.append(f"✅ {simplified_name}-комн: {len(combined_apartments)} квартир (было {len(greenwich_unified.get('apartment_types', {}).get(simplified_name, {}).get('apartments', []))})")
        else:
            changes.append(f"❌ {simplified_name}-комн: нет квартир с фото")
    
    # 4. Сохраняем обновленную запись
    print(f"\n💾 Сохраняем обновленную запись...")
    
    result = unified_col.replace_one(
        {'_id': greenwich_unified['_id']},
        new_record
    )
    
    if result.modified_count == 1:
        print(f"✅ Запись успешно обновлена!")
        print(f"\n📊 ИЗМЕНЕНИЯ:")
        for change in changes:
            print(f"   {change}")
    else:
        print(f"❌ Ошибка при обновлении записи")
    
    print(f"\n" + "=" * 50)
    print("🏁 ОБНОВЛЕНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    update_greenwich_record()
