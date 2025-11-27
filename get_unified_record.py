#!/usr/bin/env python3
"""
Скрипт для получения и вывода данных записи из unified_houses_3
"""
import json
from bson import ObjectId
from main.services.mongo_service import get_mongo_connection

def get_record_data(record_id: str):
    """Получает данные записи по ID"""
    db = get_mongo_connection()
    unified_col = db['unified_houses_3']
    
    try:
        record = unified_col.find_one({'_id': ObjectId(record_id)})
        if not record:
            print(f"❌ Запись с ID {record_id} не найдена")
            return None
        
        # Преобразуем ObjectId в строку для JSON
        def convert_to_json_serializable(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_json_serializable(item) for item in obj]
            elif isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return obj
        
        # Конвертируем для вывода
        serializable_record = convert_to_json_serializable(record)
        
        # Выводим структуру
        print("=" * 80)
        print("СТРУКТУРА ЗАПИСИ")
        print("=" * 80)
        print(json.dumps(serializable_record, indent=2, ensure_ascii=False))
        
        # Анализ структуры
        print("\n" + "=" * 80)
        print("АНАЛИЗ СТРУКТУРЫ")
        print("=" * 80)
        
        # Базовые поля
        print(f"\n📋 Базовые поля:")
        print(f"  - _id: {record.get('_id')}")
        print(f"  - name: {record.get('name', 'НЕТ')}")
        print(f"  - address: {record.get('address', 'НЕТ')}")
        print(f"  - city: {record.get('city', 'НЕТ')}")
        print(f"  - development.name: {record.get('development', {}).get('name', 'НЕТ')}")
        
        # Apartment types
        apartment_types = record.get('apartment_types', {})
        print(f"\n🏠 Apartment Types: {len(apartment_types)} типов")
        
        total_apartments = 0
        sample_apartment = None
        
        for apt_type, apt_data in apartment_types.items():
            apartments = apt_data.get('apartments', [])
            total_apartments += len(apartments)
            print(f"  - {apt_type}: {len(apartments)} квартир")
            
            # Берем первую квартиру как образец
            if apartments and not sample_apartment:
                sample_apartment = apartments[0]
        
        print(f"\n📊 Всего квартир: {total_apartments}")
        
        # Анализ структуры квартиры
        if sample_apartment:
            print(f"\n🔍 СТРУКТУРА КВАРТИРЫ (образец):")
            print(f"  Поля квартиры:")
            for key in sorted(sample_apartment.keys()):
                value = sample_apartment[key]
                value_type = type(value).__name__
                if isinstance(value, (str, int, float, bool)) or value is None:
                    value_preview = str(value)[:50] if value else 'None'
                    print(f"    - {key}: {value_type} = {value_preview}")
                elif isinstance(value, (list, dict)):
                    print(f"    - {key}: {value_type} (len={len(value) if hasattr(value, '__len__') else 'N/A'})")
                else:
                    print(f"    - {key}: {value_type}")
            
            # Проверяем ключевые поля для фильтрации
            print(f"\n✅ Ключевые поля для фильтрации:")
            print(f"    - rooms: {sample_apartment.get('rooms')} (тип: {type(sample_apartment.get('rooms')).__name__})")
            print(f"    - floorMin: {sample_apartment.get('floorMin')} (тип: {type(sample_apartment.get('floorMin')).__name__})")
            print(f"    - floorMax: {sample_apartment.get('floorMax')} (тип: {type(sample_apartment.get('floorMax')).__name__})")
            print(f"    - area: {sample_apartment.get('area')} (тип: {type(sample_apartment.get('area')).__name__})")
            print(f"    - totalArea: {sample_apartment.get('totalArea')} (тип: {type(sample_apartment.get('totalArea')).__name__})")
            print(f"    - kitchenArea: {sample_apartment.get('kitchenArea')} (тип: {type(sample_apartment.get('kitchenArea')).__name__})")
            print(f"    - livingArea: {sample_apartment.get('livingArea')} (тип: {type(sample_apartment.get('livingArea')).__name__})")
            print(f"    - price: {sample_apartment.get('price')} (тип: {type(sample_apartment.get('price')).__name__})")
            
            # Проверяем дополнительные поля
            print(f"\n📝 Дополнительные поля:")
            additional_fields = ['houseStatus', 'decorationType', 'housingType', 'houseType', 
                              'dealType', 'ceilingHeight', 'decoration']
            for field in additional_fields:
                value = sample_apartment.get(field)
                if value is not None:
                    if isinstance(value, dict):
                        print(f"    - {field}: dict с ключами {list(value.keys())}")
                    else:
                        print(f"    - {field}: {value}")
        
        return record
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    from datetime import datetime, date
    record_id = "6923e8527526e3b8a616bb18"
    print(f"🔍 Получаем данные записи: {record_id}\n")
    get_record_data(record_id)

