#!/usr/bin/env python3
"""
Скрипт для экспорта исходных данных квартир из Avito и DomClick в CSV файл
"""

import os
import sys
import django
import csv
from bson import ObjectId

# Настройка Django
sys.path.append('/home/art/PycharmProjects/anton_houses')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from main.services.mongo_service import get_mongo_connection


def export_apartments_to_csv(output_file='apartments_comparison.csv'):
    """Экспортирует квартиры из Avito и DomClick в CSV файл с тремя колонками"""
    db = get_mongo_connection()
    unified_col = db['unified_houses']
    
    # Получаем все объединенные записи
    unified_records = list(unified_col.find({}))
    
    print(f"📊 Найдено {len(unified_records)} объединенных записей\n")
    
    # Маппинг названий типов для унификации
    name_mapping = {
        'Студия': 'Студия',
        '1 ком.': '1',
        '1-комн': '1',
        '1-комн.': '1',
        '2 ком.': '2',
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
    
    # Подготавливаем данные для CSV
    csv_data = []
    
    for record_idx, unified_record in enumerate(unified_records, 1):
        source_ids = unified_record.get('_source_ids', {})
        development_name = unified_record.get('development', {}).get('name', 'Без названия')
        
        print(f"[{record_idx}/{len(unified_records)}] Обрабатываем: {development_name}")
        
        # Получаем исходные записи
        avito_record = None
        if source_ids.get('avito'):
            try:
                avito_record = db['avito'].find_one({'_id': ObjectId(source_ids['avito'])})
            except Exception as e:
                print(f"   ❌ Ошибка получения Avito: {e}")
        
        domclick_record = None
        if source_ids.get('domclick'):
            try:
                domclick_record = db['domclick'].find_one({'_id': ObjectId(source_ids['domclick'])})
            except Exception as e:
                print(f"   ❌ Ошибка получения DomClick: {e}")
        
        if not avito_record or not domclick_record:
            print(f"   ⚠️ Пропускаем (нет данных Avito или DomClick)")
            continue
        
        # Получаем типы квартир
        avito_apt_types = avito_record.get('apartment_types', {})
        domclick_apt_types = domclick_record.get('apartment_types', {})
        
        # Собираем все категории
        all_categories = set()
        
        # Добавляем категории из Avito
        for apt_type_name in avito_apt_types.keys():
            simplified = name_mapping.get(apt_type_name, apt_type_name)
            all_categories.add(simplified)
        
        # Добавляем категории из DomClick
        for apt_type_name in domclick_apt_types.keys():
            simplified = name_mapping.get(apt_type_name, apt_type_name)
            all_categories.add(simplified)
        
        # Для каждой категории собираем квартиры
        for category in sorted(all_categories):
            # Находим квартиры из Avito этой категории
            avito_apartments = []
            for apt_type_name, apt_type_data in avito_apt_types.items():
                simplified = name_mapping.get(apt_type_name, apt_type_name)
                if simplified == category:
                    avito_apartments = apt_type_data.get('apartments', [])
                    break
            
            # Находим квартиры из DomClick этой категории
            domclick_apartments = []
            for apt_type_name, apt_type_data in domclick_apt_types.items():
                simplified = name_mapping.get(apt_type_name, apt_type_name)
                if simplified == category:
                    domclick_apartments = apt_type_data.get('apartments', [])
                    break
            
            # Определяем максимальное количество квартир для выравнивания
            max_count = max(len(avito_apartments), len(domclick_apartments))
            
            # Добавляем строки в CSV
            for i in range(max_count):
                avito_title = ""
                domclick_title = ""
                
                if i < len(avito_apartments):
                    avito_title = avito_apartments[i].get('title', '')
                
                if i < len(domclick_apartments):
                    domclick_title = domclick_apartments[i].get('title', '')
                
                csv_data.append({
                    'Категория': category,
                    'Название Avito': avito_title,
                    'Название DomClick': domclick_title
                })
    
    # Записываем в CSV файл
    if csv_data:
        fieldnames = ['Категория', 'Название Avito', 'Название DomClick']
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"\n✅ Данные экспортированы в файл: {output_file}")
        print(f"📊 Всего строк: {len(csv_data)}")
    else:
        print("\n⚠️ Нет данных для экспорта")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Экспорт квартир из Avito и DomClick в CSV')
    parser.add_argument('--output', '-o', type=str, default='apartments_comparison.csv',
                        help='Имя выходного CSV файла (по умолчанию: apartments_comparison.csv)')
    
    args = parser.parse_args()
    export_apartments_to_csv(args.output)

