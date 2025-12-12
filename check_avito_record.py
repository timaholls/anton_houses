"""
Диагностический скрипт для проверки состояния записи Avito_2 после удаления unified
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from main.services.mongo_service import get_mongo_connection
from bson import ObjectId

def check_avito_record(avito_id_str):
    """Проверяет состояние записи в avito_2"""
    db = get_mongo_connection()
    avito2_col = db['avito_2']
    
    try:
        avito_id = ObjectId(avito_id_str)
    except:
        print(f"❌ Неверный формат ID: {avito_id_str}")
        return
    
    record = avito2_col.find_one({'_id': avito_id})
    
    if not record:
        print(f"❌ Запись с ID {avito_id_str} не найдена в avito_2")
        return
    
    print(f"\n{'='*80}")
    print(f"📋 Запись Avito_2: {avito_id_str}")
    print(f"{'='*80}")
    print(f"Название: {record.get('development', {}).get('name', 'Нет названия')}")
    print(f"\n🔍 Флаги состояния:")
    print(f"  - is_matched: {record.get('is_matched')} (тип: {type(record.get('is_matched'))})")
    print(f"  - is_processed: {record.get('is_processed')} (тип: {type(record.get('is_processed'))})")
    print(f"  - matched_unified_id: {record.get('matched_unified_id')}")
    print(f"  - matched_at: {record.get('matched_at')}")
    print(f"  - processed_at: {record.get('processed_at')}")
    
    # Проверяем, пройдет ли запись через фильтр get_unmatched_records
    print(f"\n🔍 Проверка фильтров get_unmatched_records:")
    
    # Фильтр 1: is_matched != True
    is_matched = record.get('is_matched')
    passes_matched_filter = (is_matched is not True) and (is_matched is not None or True)
    print(f"  - Фильтр 'is_matched != True': {'✅ ПРОХОДИТ' if passes_matched_filter else '❌ НЕ ПРОХОДИТ'}")
    print(f"    (значение: {is_matched}, проверка: {is_matched is not True})")
    
    # Фильтр 2: is_processed != True или не существует
    is_processed = record.get('is_processed')
    passes_processed_filter = (is_processed is not True) or (is_processed is None)
    print(f"  - Фильтр 'is_processed != True или не существует': {'✅ ПРОХОДИТ' if passes_processed_filter else '❌ НЕ ПРОХОДИТ'}")
    print(f"    (значение: {is_processed}, проверка: {is_processed is not True})")
    
    # Проверяем, есть ли запись в matched_avito_ids
    unified_col = db['unified_houses']
    matched_records = list(unified_col.find({}, {'_source_ids': 1}))
    matched_avito_ids = set()
    
    for rec in matched_records:
        source_ids = rec.get('_source_ids', {})
        if source_ids.get('avito'):
            try:
                matched_avito_ids.add(ObjectId(source_ids['avito']))
            except:
                pass
    
    is_in_matched = avito_id in matched_avito_ids
    print(f"  - В списке matched_avito_ids: {'❌ ДА (будет исключена)' if is_in_matched else '✅ НЕТ'}")
    
    # Итоговый результат
    will_appear = passes_matched_filter and passes_processed_filter and not is_in_matched
    print(f"\n{'='*80}")
    print(f"📊 ИТОГ: Запись {'✅ ДОЛЖНА ПОЯВИТЬСЯ' if will_appear else '❌ НЕ ПОЯВИТСЯ'} в списке unmatched")
    print(f"{'='*80}\n")
    
    # Показываем все поля для отладки
    print("📋 Все поля записи:")
    for key, value in sorted(record.items()):
        if key == '_id':
            print(f"  - {key}: {value} (ObjectId)")
        elif isinstance(value, (dict, list)):
            print(f"  - {key}: {type(value).__name__} (длина: {len(value) if isinstance(value, (dict, list)) else 'N/A'})")
        else:
            print(f"  - {key}: {value} (тип: {type(value).__name__})")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python check_avito_record.py <avito_id>")
        print("\nПример:")
        print("  python check_avito_record.py 692fcf2e6b64d70274b4fa40")
        sys.exit(1)
    
    avito_id = sys.argv[1]
    check_avito_record(avito_id)

