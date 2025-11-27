#!/usr/bin/env python
"""Скрипт для восстановления development из avito с сохранением новых фоток из S3"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

import copy
from bson import ObjectId
from main.services.mongo_service import get_mongo_connection

db = get_mongo_connection()
unified_col = db['unified_houses_3']
avito_col = db['avito']

# ID документов для восстановления (из предыдущего запроса)
unified_ids = [
    '691b0e084a809a7cf0f7ee95',
    '691b14d94a809a7cf0f7eeac',
    '691bf7884a809a7cf0f7eec0',
    '691c3e9d65e1daa346547e44'
]

dry_run = False  # Установить True для проверки без изменений

print(f"\n{'='*60}")
print(f"Восстановление development из avito с сохранением фоток из S3")
print(f"Режим: {'DRY-RUN (только проверка)' if dry_run else 'РЕАЛЬНОЕ ОБНОВЛЕНИЕ'}")
print(f"{'='*60}\n")

updated_count = 0
errors_count = 0

for unified_id_str in unified_ids:
    try:
        unified_id = ObjectId(unified_id_str)
        
        # Получаем документ из unified_houses_3
        unified_doc = unified_col.find_one({'_id': unified_id})
        if not unified_doc:
            print(f"❌ [{unified_id_str}] Документ не найден в unified_houses_3")
            errors_count += 1
            continue
        
        # Получаем ID avito
        source_ids = unified_doc.get('_source_ids', {})
        avito_id_str = source_ids.get('avito')
        if not avito_id_str:
            print(f"❌ [{unified_id_str}] Нет _source_ids.avito")
            errors_count += 1
            continue
        
        # Получаем исходный документ из avito
        avito_id = ObjectId(avito_id_str)
        avito_doc = avito_col.find_one({'_id': avito_id})
        if not avito_doc:
            print(f"❌ [{unified_id_str}] Исходный документ avito не найден: {avito_id_str}")
            errors_count += 1
            continue
        
        # Берем development из avito (полностью весь объект)
        avito_dev = avito_doc.get('development', {})
        if not avito_dev:
            print(f"⚠️  [{unified_id_str}] Нет development в avito документе")
            continue
        
        # Сохраняем текущие фотки из unified_houses_3 (уже в S3)
        current_development = unified_doc.get('development', {})
        current_photos = current_development.get('photos', [])
        
        # Копируем полностью весь development из avito (глубокое копирование)
        restored_dev = copy.deepcopy(avito_dev)
        
        # Заменяем только photos на новые фотки из S3
        restored_dev['photos'] = current_photos
        
        # Выводим информацию о полях
        avito_fields = list(avito_dev.keys())
        print(f"[{unified_id_str}]")
        print(f"  📋 Полностью восстановлен development из avito:")
        print(f"     - Всего полей в development: {len(avito_fields)}")
        print(f"     - Поля: {', '.join(avito_fields)}")
        print(f"     - name: {restored_dev.get('name', 'N/A')}")
        print(f"     - address: {restored_dev.get('address', 'N/A')}")
        print(f"     - price_range: {restored_dev.get('price_range', 'N/A')}")
        if 'parameters' in restored_dev:
            print(f"     - parameters: {len(restored_dev.get('parameters', {}))} полей")
        if 'korpuses' in restored_dev:
            print(f"     - korpuses: {len(restored_dev.get('korpuses', []))} шт")
        print(f"  📸 Фоток сохранено из S3: {len(current_photos)}")
        
        if not dry_run:
            # Обновляем документ
            unified_col.update_one(
                {'_id': unified_id},
                {'$set': {'development': restored_dev}}
            )
            print(f"  ✅ Документ обновлен\n")
            updated_count += 1
        else:
            print(f"  [DRY-RUN] Будет обновлен\n")
        
    except Exception as e:
        print(f"❌ [{unified_id_str}] Ошибка: {e}\n")
        errors_count += 1

print(f"{'='*60}")
print(f"Результаты:")
print(f"  Обновлено: {updated_count}")
print(f"  Ошибок: {errors_count}")
print(f"{'='*60}\n")

