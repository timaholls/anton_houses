"""
Проверка unified записи и её source_ids
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from main.services.mongo_service import get_mongo_connection
from bson import ObjectId

def check_unified_record(unified_id_str):
    """Проверяет unified запись и её source_ids"""
    db = get_mongo_connection()
    unified_col = db['unified_houses']
    
    try:
        unified_id = ObjectId(unified_id_str)
    except:
        print(f"❌ Неверный формат ID: {unified_id_str}")
        return
    
    record = unified_col.find_one({'_id': unified_id})
    
    if not record:
        print(f"❌ Unified запись с ID {unified_id_str} НЕ НАЙДЕНА (возможно, уже удалена)")
        print(f"\nПроверяем, есть ли другие unified записи с этим avito_id в source_ids...")
        
        # Проверяем, есть ли другие unified записи, которые ссылаются на этот avito_id
        avito_id = "693b43fe284e071dafc61911"
        all_unified = list(unified_col.find({}, {'_source_ids': 1, 'development.name': 1}))
        
        print(f"\nВсе unified записи, которые ссылаются на avito_id {avito_id}:")
        found = False
        for rec in all_unified:
            source_ids = rec.get('_source_ids', {})
            if source_ids.get('avito') == avito_id:
                found = True
                print(f"  ✅ Найдена unified запись: {rec['_id']}")
                print(f"     source_ids: {source_ids}")
                name = rec.get('development', {}).get('name', 'Нет названия')
                print(f"     Название: {name}")
        
        if not found:
            print(f"  ❌ Нет unified записей, ссылающихся на этот avito_id")
        
        return
    
    print(f"\n{'='*80}")
    print(f"📋 Unified запись: {unified_id_str}")
    print(f"{'='*80}")
    
    name = record.get('development', {}).get('name', 'Нет названия')
    print(f"Название: {name}")
    
    source_ids = record.get('_source_ids', {})
    print(f"\n🔍 _source_ids:")
    print(f"  - domrf: {source_ids.get('domrf')}")
    print(f"  - avito: {source_ids.get('avito')}")
    print(f"  - domclick: {source_ids.get('domclick')}")
    
    # Проверяем старую структуру
    if not source_ids.get('avito'):
        avito_old = record.get('avito', {})
        if avito_old:
            print(f"\n⚠️ Найдена старая структура 'avito':")
            print(f"  - _id: {avito_old.get('_id')}")
    
    if not source_ids.get('avito'):
        avito2_old = record.get('avito_2', {})
        if avito2_old:
            print(f"\n⚠️ Найдена старая структура 'avito_2':")
            print(f"  - _id: {avito2_old.get('_id')}")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python check_unified_record.py <unified_id>")
        print("\nПример:")
        print("  python check_unified_record.py 693b502408ceb9a751716053")
        sys.exit(1)
    
    unified_id = sys.argv[1]
    check_unified_record(unified_id)

