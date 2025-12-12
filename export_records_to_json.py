#!/usr/bin/env python3
"""
Скрипт для экспорта записей из DomRF и Avito_2 в JSON файлы
Формат: {"название": "url"}
"""
import sys
import json
from pathlib import Path
from typing import Dict

# Подтягиваем корень проекта для импорта модулей
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from domrf.db_config import get_collection as get_domrf_collection
    from main.services.mongo_service import get_mongo_connection
except Exception as exc:
    try:
        # Пробуем импортировать напрямую, если domrf в корне проекта
        from db_config import get_collection as get_domrf_collection
        from main.services.mongo_service import get_mongo_connection
    except Exception as exc2:
        print(f"❌ Не удалось импортировать модули: {exc}, {exc2}")
        sys.exit(1)


def export_domrf_to_json(db, output_file: str = "domrf_records.json"):
    """Экспортирует записи из DomRF в JSON"""
    print("📋 Загрузка записей из DomRF...")
    
    try:
        collection = get_domrf_collection()
        
        # Сначала считаем общее количество записей
        total_count = collection.count_documents({})
        print(f"   Всего записей в DomRF: {total_count}")
        
        # Получаем все записи
        cursor = collection.find({}, {
            'objCommercNm': 1,
            'complexShortName': 1,
            'objId': 1,
            'objUrl': 1,
            'url': 1,
            '_id': 1
        }).batch_size(500)
        
        records = {}
        count = 0
        skipped_no_name = 0
        duplicates = 0
        no_name_count = 0
        
        for doc in cursor:
            # Получаем название
            name = doc.get('objCommercNm') or doc.get('complexShortName') or ''
            
            # Если названия нет, используем "нет названия" с ID для уникальности
            if not name:
                doc_id = str(doc.get('_id', ''))
                name = f"нет названия ({doc_id[:8]})"
                no_name_count += 1
            
            # Получаем URL (пробуем разные поля)
            url = doc.get('url') or doc.get('objUrl') or ''
            
            # Если URL нет, формируем из objId
            if not url:
                obj_id = doc.get('objId')
                if obj_id:
                    url = f"https://наш.дом.рф/сервисы/каталог-новостроек/объект/{obj_id}"
                else:
                    url = ''
            
            # Проверяем на дубликаты названий
            if name in records:
                duplicates += 1
                # Если уже есть запись с таким названием, добавляем ID для различия
                doc_id = str(doc.get('_id', ''))
                name = f"{name} ({doc_id[:8]})"
            
            # Сохраняем в формате "название": "url"
            records[name] = url
            count += 1
        
        # Сохраняем в JSON файл
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"   Записей без названия (использовано 'нет названия'): {no_name_count}")
        print(f"   Дубликатов названий (добавлен ID): {duplicates}")
        print(f"✅ Экспортировано {count} записей из DomRF в {output_file}")
        print(f"   (Всего обработано: {count} из {total_count})")
        return count
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте DomRF: {e}")
        import traceback
        traceback.print_exc()
        return 0


def export_avito2_to_json(db, output_file: str = "avito2_records.json"):
    """Экспортирует записи из Avito_2 в JSON"""
    print("📋 Загрузка записей из Avito_2...")
    
    try:
        avito2_col = db['avito_2']
        
        # Получаем все записи
        cursor = avito2_col.find({}, {
            'development.name': 1,
            'development.url': 1,
            'url': 1,
            '_id': 1
        }).batch_size(500)
        
        # Сначала считаем общее количество записей
        total_count = avito2_col.count_documents({})
        print(f"   Всего записей в Avito_2: {total_count}")
        
        records = {}
        count = 0
        no_name_count = 0
        duplicates = 0
        
        for doc in cursor:
            # Получаем название из development.name
            development = doc.get('development', {})
            name = development.get('name') or ''
            
            # Если названия нет, используем "нет названия" с ID для уникальности
            if not name:
                doc_id = str(doc.get('_id', ''))
                name = f"нет названия ({doc_id[:8]})"
                no_name_count += 1
            
            # Получаем URL (пробуем разные поля)
            url = development.get('url') or doc.get('url') or ''
            
            # Если URL нет, используем пустую строку
            if not url:
                url = ''
            
            # Проверяем на дубликаты названий
            if name in records:
                duplicates += 1
                # Если уже есть запись с таким названием, добавляем ID для различия
                doc_id = str(doc.get('_id', ''))
                name = f"{name} ({doc_id[:8]})"
            
            # Сохраняем в формате "название": "url"
            records[name] = url
            count += 1
        
        # Сохраняем в JSON файл
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"   Записей без названия (использовано 'нет названия'): {no_name_count}")
        print(f"   Дубликатов названий (добавлен ID): {duplicates}")
        print(f"✅ Экспортировано {count} записей из Avito_2 в {output_file}")
        print(f"   (Всего обработано: {count} из {total_count})")
        return count
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте Avito_2: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """Основная функция"""
    try:
        db = get_mongo_connection()
    except Exception as exc:
        print(f"❌ Не удалось подключиться к MongoDB: {exc}")
        sys.exit(1)
    
    print("🚀 Начало экспорта записей...\n")
    
    # Экспортируем DomRF
    domrf_count = export_domrf_to_json(db, "domrf_records.json")
    
    print()
    
    # Экспортируем Avito_2
    avito2_count = export_avito2_to_json(db, "avito2_records.json")
    
    print(f"\n{'='*80}")
    print(f"✅ Экспорт завершен!")
    print(f"📊 DomRF: {domrf_count} записей → domrf_records.json")
    print(f"📊 Avito_2: {avito2_count} записей → avito2_records.json")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

