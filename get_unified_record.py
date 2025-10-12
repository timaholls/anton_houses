#!/usr/bin/env python3
"""
Скрипт для получения одной записи из коллекции unified_houses
и сохранения её в JSON файл для анализа структуры
"""
import os
import json
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки подключения к MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:Kfleirb_17@176.98.177.188:27017/admin")
DB_NAME = os.getenv("DB_NAME", "houses")

class MongoJSONEncoder(json.JSONEncoder):
    """Позволяет сериализовать ObjectId и другие BSON-типы"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

def get_and_save_unified_record():
    """Получить одну запись из unified_houses и сохранить в файл"""
    print("🔍 ПОЛУЧЕНИЕ ЗАПИСИ ИЗ UNIFIED_HOUSES")
    print("=" * 80)
    
    client = None
    try:
        # Подключаемся к MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        unified_collection = db['unified_houses']
        
        print(f"✅ Подключено к MongoDB: {MONGO_URI}")
        print(f"✅ База данных: {DB_NAME}")
        print(f"✅ Коллекция: unified_houses")
        
        # Получаем одну запись
        record = unified_collection.find_one({})
        
        if record:
            print(f"\n📋 Найдена запись с ID: {record['_id']}")
            print(f"📋 Источник: {record.get('source', 'unknown')}")
            
            # Сохраняем в файл
            file_path = "unified_record_sample.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2, cls=MongoJSONEncoder)
            
            print(f"\n✅ Запись сохранена в файл: {file_path}")
            
            # Выводим структуру в консоль для быстрого просмотра
            print(f"\n📊 СТРУКТУРА ЗАПИСИ:")
            print("-" * 50)
            print(f"_id: {record['_id']}")
            print(f"source: {record.get('source', 'N/A')}")
            
            if 'domrf' in record:
                domrf = record['domrf']
                print(f"domrf:")
                print(f"  - name: {domrf.get('name', 'N/A')}")
                print(f"  - latitude: {domrf.get('latitude', 'N/A')}")
                print(f"  - longitude: {domrf.get('longitude', 'N/A')}")
                print(f"  - url: {domrf.get('url', 'N/A')}")
            
            if 'avito' in record and record['avito']:
                avito = record['avito']
                print(f"avito:")
                print(f"  - _id: {avito.get('_id', 'N/A')}")
                print(f"  - url: {avito.get('url', 'N/A')}")
                if 'development' in avito:
                    dev = avito['development']
                    print(f"  - development.name: {dev.get('name', 'N/A')}")
                    print(f"  - development.address: {dev.get('address', 'N/A')[:50]}...")
            
            if 'domclick' in record and record['domclick']:
                domclick = record['domclick']
                print(f"domclick:")
                print(f"  - _id: {domclick.get('_id', 'N/A')}")
                print(f"  - url: {domclick.get('url', 'N/A')}")
                if 'development' in domclick:
                    dev = domclick['development']
                    print(f"  - development.complex_name: {dev.get('complex_name', 'N/A')}")
            
            print(f"\n📁 Полная структура записана в: {file_path}")
            
        else:
            print("❌ В коллекции 'unified_houses' не найдено ни одной записи!")
            print("💡 Убедитесь, что вы уже создали сопоставления через интерфейс ручного сопоставления")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if client:
            client.close()
            print("\n🔌 Соединение с MongoDB закрыто")

if __name__ == "__main__":
    get_and_save_unified_record()
