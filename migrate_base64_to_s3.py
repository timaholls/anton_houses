#!/usr/bin/env python3
"""
Скрипт миграции: находит все base64 изображения в базе данных,
загружает их в S3 через resize_img.py и заменяет ссылки в базе.

Использование:
    python migrate_base64_to_s3.py
    python migrate_base64_to_s3.py --collection unified_houses
    python migrate_base64_to_s3.py --collection secondary_properties
    python migrate_base64_to_s3.py --dry-run  # только проверка, без изменений
"""

import os
import sys
import base64
import argparse
import logging
from datetime import datetime
from io import BytesIO
from bson import ObjectId

# Настройка Django
import django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from main.services.mongo_service import get_mongo_connection
from main.s3_service import s3_client
from main.resize_img import ImageProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def is_base64_image(value):
    """Проверяет, является ли значение base64 изображением"""
    if not isinstance(value, str):
        return False
    return value.startswith('data:image/') and ',' in value


def upload_base64_to_s3(base64_data, s3_key):
    """Загружает base64 изображение в S3 через resize_img.py"""
    try:
        # Извлекаем base64 данные
        if ',' in base64_data:
            header, base64_data = base64_data.split(',', 1)
        
        # Декодируем base64
        image_bytes = base64.b64decode(base64_data)
        
        # Обрабатываем через resize_img.py
        processor = ImageProcessor(logger=logger, max_size=(1920, 1920), max_kb=500)
        processed_bytes = processor.process(BytesIO(image_bytes))
        processed_bytes.seek(0)
        
        # Загружаем в S3
        s3_url = s3_client.upload_bytes(processed_bytes.read(), s3_key, 'image/jpeg')
        return s3_url
        
    except Exception as e:
        logger.error(f"Ошибка загрузки base64 в S3: {e}")
        return None


def process_array(value, collection_name, doc_id, field_path, s3_prefix, dry_run=False):
    """Обрабатывает массив значений, заменяя base64 на S3 URL"""
    updated = False
    new_array = []
    
    for idx, item in enumerate(value):
        if isinstance(item, str) and is_base64_image(item):
            # Для массива image в apartment_types используем индекс
            timestamp_ms = int(datetime.now().timestamp() * 1000)
            s3_key = f"{s3_prefix}/photo-{timestamp_ms}-{idx}.jpg"
            
            if not dry_run:
                s3_url = upload_base64_to_s3(item, s3_key)
                if s3_url:
                    new_array.append(s3_url)
                    logger.info(f"  Заменено base64 [{idx}] -> {s3_url}")
                    updated = True
                else:
                    new_array.append(item)  # Оставляем base64 при ошибке
            else:
                logger.info(f"  [DRY-RUN] Найдено base64 изображение [{idx}] (будет заменено)")
                new_array.append(item)  # В dry-run оставляем как есть
        elif isinstance(item, dict):
            # Обрабатываем объекты в массиве (например, квартиры в apartment_types)
            # Используем точечную нотацию MongoDB вместо квадратных скобок
            array_index_path = f"{field_path}.{idx}" if field_path else str(idx)
            processed_item = process_dict(item, collection_name, doc_id, array_index_path, s3_prefix, dry_run)
            if processed_item:
                # Объединяем изменения с исходным объектом
                new_item = {**item}
                # Применяем обновления (которые уже в точечной нотации относительно item)
                for update_key, update_value in processed_item.items():
                    # update_key может быть относительным (например, "image") или полным ("apartments.0.image")
                    if '.' in update_key:
                        # Это вложенное поле, нужно объединить правильно
                        keys = update_key.split('.')
                        current = new_item
                        for k in keys[:-1]:
                            if k not in current:
                                current[k] = {}
                            elif not isinstance(current[k], dict):
                                current[k] = {}
                            current = current[k]
                        current[keys[-1]] = update_value
                    else:
                        new_item[update_key] = update_value
                new_array.append(new_item)
                updated = True
            else:
                new_array.append(item)
        else:
            new_array.append(item)
    
    return new_array if updated else None


def process_dict(value, collection_name, doc_id, field_path, s3_prefix, dry_run=False):
    """Рекурсивно обрабатывает словарь"""
    updates = {}
    
    for key, val in value.items():
        current_path = f"{field_path}.{key}" if field_path else key
        
        if isinstance(val, str) and is_base64_image(val):
            # Для development.photos используем development путь
            if field_path == 'development' and key == 'photos':
                photo_s3_prefix = f"{s3_prefix}/development"
            else:
                photo_s3_prefix = s3_prefix
            
            s3_key = f"{photo_s3_prefix}/photo-{int(datetime.now().timestamp()*1000)}.jpg"
            
            if not dry_run:
                s3_url = upload_base64_to_s3(val, s3_key)
                if s3_url:
                    if field_path:
                        # Для вложенных полей используем точечную нотацию
                        updates[current_path] = s3_url
                    else:
                        updates[key] = s3_url
                    logger.info(f"  Заменено {current_path}: base64 -> {s3_url}")
                else:
                    logger.warning(f"  Ошибка загрузки {current_path}, пропущено")
            else:
                logger.info(f"  [DRY-RUN] Найдено base64 в {current_path} (будет заменено)")
        
        elif isinstance(val, list):
            # Определяем путь для фото в массивах
            if key == 'photos':
                if field_path == 'development':
                    photo_s3_prefix = f"{s3_prefix}/development"
                else:
                    photo_s3_prefix = f"{s3_prefix}/{key}"
            elif key == 'image':  # Для apartment_types.apartments[].image
                # Извлекаем room_type из field_path если возможно
                if 'apartments' in field_path:
                    room_type = field_path.split('apartments')[0].split('.')[-1] if '.' in field_path else 'general'
                    photo_s3_prefix = f"{s3_prefix}/{room_type}"
                else:
                    photo_s3_prefix = f"{s3_prefix}/{key}"
            elif key == 'apartments':  # Для apartment_types
                # Извлекаем room_type из field_path
                room_type = field_path.split('.')[-1] if '.' in field_path else 'general'
                photo_s3_prefix = f"{s3_prefix}/{room_type}"
            else:
                photo_s3_prefix = f"{s3_prefix}/{key}"
            
            new_array = process_array(val, collection_name, doc_id, current_path, photo_s3_prefix, dry_run)
            if new_array is not None:
                if field_path:
                    updates[current_path] = new_array
                else:
                    updates[key] = new_array
        
        elif isinstance(val, dict):
            # Для apartment_types используем специальный префикс
            if key == 'apartment_types':
                nested_s3_prefix = f"{s3_prefix}/apartments"
            elif key == 'development':
                nested_s3_prefix = f"{s3_prefix}/development"
            elif key == 'construction_progress':
                nested_s3_prefix = f"{s3_prefix}/construction"
            else:
                nested_s3_prefix = f"{s3_prefix}/{key}"
            
            nested_updates = process_dict(val, collection_name, doc_id, current_path, nested_s3_prefix, dry_run)
            if nested_updates:
                # Объединяем обновления
                updates.update(nested_updates)
    
    return updates if updates else None


def migrate_collection(collection_name, dry_run=False):
    """Мигрирует base64 изображения в коллекции"""
    db = get_mongo_connection()
    col = db[collection_name]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Обработка коллекции: {collection_name}")
    logger.info(f"Режим: {'DRY-RUN (проверка)' if dry_run else 'РЕАЛЬНАЯ МИГРАЦИЯ'}")
    logger.info(f"{'='*60}\n")
    
    total_processed = 0
    total_updated = 0
    total_errors = 0
    
    # Получаем все документы
    cursor = col.find({})
    
    for doc in cursor:
        doc_id = str(doc['_id'])
        total_processed += 1
        
        # Определяем S3 префикс в зависимости от коллекции
        if collection_name == 'unified_houses':
            s3_prefix = f"unified_houses/{doc_id}"
        elif collection_name == 'secondary_properties':
            slug = doc.get('slug', doc_id)
            s3_prefix = f"secondary_complexes/{slug}"
        else:
            s3_prefix = f"{collection_name}/{doc_id}"
        
        logger.info(f"[{total_processed}] Документ {doc_id}")
        
        # Обрабатываем документ
        updates = process_dict(doc, collection_name, doc_id, '', s3_prefix, dry_run)
        
        if updates:
            total_updated += 1
            if not dry_run:
                try:
                    # Применяем обновления используя MongoDB точечную нотацию напрямую
                    # Это важно: используем точечную нотацию для вложенных полей,
                    # чтобы не заменять весь объект, а только конкретные поля
                    update_dict = {}
                    for key, value in updates.items():
                        # Используем точечную нотацию напрямую для MongoDB
                        # Например: 'development.photos' -> обновит только photos внутри development
                        update_dict[key] = value
                    
                    # Обновляем документ с точечной нотацией
                    col.update_one({'_id': ObjectId(doc_id)}, {'$set': update_dict})
                    logger.info(f"  ✅ Документ обновлен\n")
                except Exception as e:
                    total_errors += 1
                    logger.error(f"  ❌ Ошибка обновления документа: {e}\n")
            else:
                logger.info(f"  [DRY-RUN] Документ будет обновлен\n")
        else:
            logger.info(f"  ⏭️ Base64 изображений не найдено\n")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Результаты миграции коллекции '{collection_name}':")
    logger.info(f"  Обработано документов: {total_processed}")
    logger.info(f"  Обновлено документов: {total_updated}")
    logger.info(f"  Ошибок: {total_errors}")
    logger.info(f"{'='*60}\n")
    
    return total_processed, total_updated, total_errors


def main():
    parser = argparse.ArgumentParser(description='Миграция base64 изображений в S3')
    parser.add_argument('--collection', type=str, help='Имя коллекции (unified_houses, secondary_properties, или all)')
    parser.add_argument('--dry-run', action='store_true', help='Только проверка, без реальных изменений')
    args = parser.parse_args()
    
    collections = []
    if args.collection:
        if args.collection == 'all':
            collections = ['unified_houses', 'secondary_properties']
        else:
            collections = [args.collection]
    else:
        collections = ['unified_houses', 'secondary_properties']
    
    total_processed = 0
    total_updated = 0
    total_errors = 0
    
    for collection_name in collections:
        processed, updated, errors = migrate_collection(collection_name, args.dry_run)
        total_processed += processed
        total_updated += updated
        total_errors += errors
    
    logger.info(f"\n{'='*60}")
    logger.info(f"ИТОГО:")
    logger.info(f"  Обработано документов: {total_processed}")
    logger.info(f"  Обновлено документов: {total_updated}")
    logger.info(f"  Ошибок: {total_errors}")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()

