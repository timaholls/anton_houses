#!/usr/bin/env python3
"""
Диагностический скрипт для проверки записи Greenwich
"""

import os
import sys
import django
from bson import ObjectId

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

def diagnose_greenwich():
    """Диагностика записи Greenwich"""
    print("🔍 ДИАГНОСТИКА ЗАПИСИ GREENWICH")
    print("=" * 50)
    
    db = get_mongo_connection()
    
    # 1. Ищем запись Greenwich в unified_houses
    print("\n1️⃣ ПОИСК В UNIFIED_HOUSES:")
    unified_col = db['unified_houses']
    greenwich_unified = unified_col.find_one({'development.name': 'ЖК «Greenwich»'})
    
    if greenwich_unified:
        print(f"✅ Найдена объединенная запись: {greenwich_unified['_id']}")
        print(f"📊 Источники: {greenwich_unified.get('_source_ids', {})}")
        
        # Проверяем apartment_types
        apt_types = greenwich_unified.get('apartment_types', {})
        print(f"🏠 Типы квартир в объединенной записи:")
        for apt_type, apt_data in apt_types.items():
            apartments = apt_data.get('apartments', [])
            print(f"   - {apt_type}: {len(apartments)} квартир")
            if apartments:
                first_apt = apartments[0]
                print(f"     Первая квартира: {first_apt.get('title', 'N/A')}")
                print(f"     Цена: {first_apt.get('price', 'N/A')}")
                print(f"     Фото: {len(first_apt.get('image', []))} шт.")
    else:
        print("❌ Запись Greenwich не найдена в unified_houses")
        return
    
    # 2. Проверяем исходные записи
    source_ids = greenwich_unified.get('_source_ids', {})
    
    print(f"\n2️⃣ ПРОВЕРКА ИСХОДНЫХ ЗАПИСЕЙ:")
    
    # Avito
    if source_ids.get('avito'):
        print(f"\n📱 AVITO ({source_ids['avito']}):")
        avito_col = db['avito']
        avito_record = avito_col.find_one({'_id': ObjectId(source_ids['avito'])})
        if avito_record:
            print(f"✅ Запись найдена: {avito_record.get('development', {}).get('name', 'N/A')}")
            avito_apt_types = avito_record.get('apartment_types', {})
            print(f"🏠 Типы квартир в Avito:")
            for apt_type, apt_data in avito_apt_types.items():
                apartments = apt_data.get('apartments', [])
                print(f"   - {apt_type}: {len(apartments)} квартир")
                if apartments:
                    first_apt = apartments[0]
                    print(f"     Первая квартира: {first_apt.get('title', 'N/A')}")
                    print(f"     Цена: {first_apt.get('price', 'N/A')}")
        else:
            print("❌ Запись Avito не найдена")
    
    # DomClick
    if source_ids.get('domclick'):
        print(f"\n🏗️ DOMCLICK ({source_ids['domclick']}):")
        domclick_col = db['domclick']
        domclick_record = domclick_col.find_one({'_id': ObjectId(source_ids['domclick'])})
        if domclick_record:
            print(f"✅ Запись найдена: {domclick_record.get('development', {}).get('complex_name', 'N/A')}")
            domclick_apt_types = domclick_record.get('apartment_types', {})
            print(f"🏠 Типы квартир в DomClick:")
            for apt_type, apt_data in domclick_apt_types.items():
                apartments = apt_data.get('apartments', [])
                print(f"   - {apt_type}: {len(apartments)} квартир")
                if apartments:
                    first_apt = apartments[0]
                    print(f"     Первая квартира: {first_apt.get('title', 'N/A')}")
                    photos = first_apt.get('photos', [])
                    print(f"     Фото: {len(photos)} шт.")
                    if photos:
                        print(f"     Первое фото: {photos[0]}")
        else:
            print("❌ Запись DomClick не найдена")
    
    # DomRF
    if source_ids.get('domrf'):
        print(f"\n🏢 DOMRF ({source_ids['domrf']}):")
        domrf_col = db['domrf']
        domrf_record = domrf_col.find_one({'_id': ObjectId(source_ids['domrf'])})
        if domrf_record:
            print(f"✅ Запись найдена: {domrf_record.get('name', 'N/A')}")
        else:
            print("❌ Запись DomRF не найдена")
    
    # 3. Анализ маппинга названий
    print(f"\n3️⃣ АНАЛИЗ МАППИНГА НАЗВАНИЙ:")
    if avito_record and domclick_record:
        avito_apt_types = avito_record.get('apartment_types', {})
        domclick_apt_types = domclick_record.get('apartment_types', {})
        
        print(f"📱 Названия типов в Avito: {list(avito_apt_types.keys())}")
        print(f"🏗️ Названия типов в DomClick: {list(domclick_apt_types.keys())}")
        
        # Маппинг из кода (ИСПРАВЛЕННЫЙ)
        name_mapping = {
            'Студия': 'Студия',
            '1 ком.': '1',
            '1-комн': '1',
            '1-комн.': '1',
            '2 ком.': '2',  # ← ИСПРАВЛЕНО: добавлен маппинг для Avito
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
        
        print(f"\n🔄 ПРИМЕНЕНИЕ МАППИНГА:")
        for dc_type_name in domclick_apt_types.keys():
            simplified_name = name_mapping.get(dc_type_name, dc_type_name)
            print(f"   DomClick '{dc_type_name}' → '{simplified_name}'")
        
        for avito_type_name in avito_apt_types.keys():
            simplified_name = name_mapping.get(avito_type_name, avito_type_name)
            print(f"   Avito '{avito_type_name}' → '{simplified_name}'")
    
    # 4. Проверка логики объединения
    print(f"\n4️⃣ ПРОВЕРКА ЛОГИКИ ОБЪЕДИНЕНИЯ:")
    if avito_record and domclick_record:
        avito_apt_types = avito_record.get('apartment_types', {})
        domclick_apt_types = domclick_record.get('apartment_types', {})
        
        processed_types = set()
        
        for dc_type_name, dc_type_data in domclick_apt_types.items():
            simplified_name = name_mapping.get(dc_type_name, dc_type_name)
            
            if simplified_name in processed_types:
                print(f"⚠️ Тип '{simplified_name}' уже обработан, пропускаем '{dc_type_name}'")
                continue
            processed_types.add(simplified_name)
            
            dc_apartments = dc_type_data.get('apartments', [])
            print(f"\n🔄 Обрабатываем тип '{simplified_name}' (из DomClick '{dc_type_name}'):")
            print(f"   Квартир в DomClick: {len(dc_apartments)}")
            
            # Ищем в Avito
            avito_apartments = []
            for avito_type_name, avito_data in avito_apt_types.items():
                avito_simplified = name_mapping.get(avito_type_name, avito_type_name)
                if avito_simplified == simplified_name:
                    avito_apartments = avito_data.get('apartments', [])
                    print(f"   Найден в Avito как '{avito_type_name}' → '{avito_simplified}'")
                    break
            
            print(f"   Квартир в Avito: {len(avito_apartments)}")
            
            # Проверяем квартиры с фото
            apartments_with_photos = 0
            for dc_apt in dc_apartments:
                apartment_photos = dc_apt.get('photos', [])
                if apartment_photos:
                    apartments_with_photos += 1
            
            print(f"   Квартир с фото в DomClick: {apartments_with_photos}")
            
            if apartments_with_photos == 0:
                print(f"❌ Нет квартир с фото для типа '{simplified_name}' - тип не будет добавлен!")
    
    print(f"\n" + "=" * 50)
    print("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    diagnose_greenwich()
