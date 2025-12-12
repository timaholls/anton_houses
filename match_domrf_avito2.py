#!/usr/bin/env python3
"""
Скрипт для матчинга записей DomRF с Avito_2

Логика:
- DomRF предназначен для создания будущих проектов (еще не сданы)
- Avito_2 - для уже сданных и в продаже
- Если находим проект из DomRF в Avito_2 - значит это уже не будущий проект,
  он уже есть в продаже
- Помечаем только DomRF запись как обработанную (is_processed: True),
  чтобы она не показывалась в manual-matching
- Avito_2 не трогаем, так как там уже все обработано
"""
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import datetime

# Подтягиваем корень проекта для импорта модулей
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from domrf.db_config import get_collection as get_domrf_collection, normalize_name as normalize_domrf_name
    from main.services.mongo_service import get_mongo_connection
    from bson import ObjectId
except Exception as exc:
    try:
        # Пробуем импортировать напрямую, если domrf в корне проекта
        from db_config import get_collection as get_domrf_collection, normalize_name as normalize_domrf_name
        from main.services.mongo_service import get_mongo_connection
        from bson import ObjectId
    except Exception as exc2:
        print(f"❌ Не удалось импортировать модули: {exc}, {exc2}")
        sys.exit(1)


def extract_key_words(name: str) -> str:
    """Извлекает ключевые слова из названия для более гибкого поиска"""
    if not name:
        return ""
    
    normalized = name.lower()
    # Убираем кавычки
    normalized = normalized.translate(str.maketrans({
        '"': '', '«': '', '»': '', '"': '', '"': '', '„': '',
    }))
    # Убираем содержимое в скобках
    normalized = re.sub(r'\([^)]*\)', '', normalized)
    # Убираем лишние символы
    normalized = re.sub(r'[^\w\s&]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Убираем префиксы
    prefixes = [
        r'^жк\s+', r'^жилой\s+комплекс\s+', r'^комплекс\s+',
        r'^клубный\s+дом\s+', r'^комплекс\s+апартаментов\s+',
    ]
    for prefix in prefixes:
        normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE)
    
    # Убираем служебные слова
    common_words = [
        'жк', 'жилой', 'комплекс', 'клубный', 'дом', 'дома',
        'квартиры', 'литер', 'литера', 'секции', 'секция',
        'этап', 'очередь', 'паркинг', 'квартал', 'микрорайон',
    ]
    for word in common_words:
        normalized = re.sub(r'\b' + word + r'\b', '', normalized, flags=re.IGNORECASE)
    
    # Убираем короткие слова и цифры
    words = normalized.split()
    filtered_words = []
    for word in words:
        if word.isdigit() and len(word) <= 2:
            continue
        if len(word) <= 2 and word.isalpha():
            continue
        filtered_words.append(word)
    
    normalized = ' '.join(filtered_words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def clean_avito_name(name: str) -> str:
    """Очищает название из Avito"""
    if not name:
        return ""
    
    normalized = name.lower()
    normalized = normalized.translate(str.maketrans({
        '"': '', '«': '', '»': '', '"': '', '"': '', '„': '',
    }))
    
    prefixes = [
        r'^жк\s+', r'^жилой\s+комплекс\s+', r'^комплекс\s+',
    ]
    for prefix in prefixes:
        normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE)
    
    common_words = [
        'жк', 'жилой', 'комплекс', 'литер', 'литера',
        'секции', 'секция', 'этап', 'очередь', 'паркинг',
    ]
    for word in common_words:
        normalized = re.sub(r'\b' + word + r'\b', '', normalized, flags=re.IGNORECASE)
    
    words = normalized.split()
    filtered_words = []
    for word in words:
        if word.isdigit() and len(word) <= 2:
            continue
        if len(word) <= 2 and word.isalpha():
            continue
        filtered_words.append(word)
    
    normalized = ' '.join(filtered_words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def load_domrf_records(db) -> List[Tuple[str, str, str, Dict]]:
    """Загружает несопоставленные записи из DomRF"""
    result = []
    try:
        collection = get_domrf_collection()
        
        # Ищем записи, которые не обработаны и не сопоставлены
        query = {
            '$or': [
                {'is_processed': {'$ne': True}},
                {'is_processed': {'$exists': False}}
            ]
        }
        
        cursor = collection.find(query, {
            'objCommercNm': 1,
            'complexShortName': 1,
            'normalized_name': 1,
            '_id': 1
        }).batch_size(500)
        
        for doc in cursor:
            orig_name = doc.get('objCommercNm') or doc.get('complexShortName') or ''
            if not orig_name:
                continue
            
            normalized = doc.get('normalized_name') or normalize_domrf_name(orig_name)
            doc_id = str(doc['_id'])
            
            result.append((orig_name, normalized, doc_id, doc))
    except Exception as exc:
        print(f"❌ Ошибка загрузки записей DomRF: {exc}")
    
    return result


def find_avito2_matches(db, domrf_name: str, normalized: str, key_words: str) -> List[Dict]:
    """Находит совпадения в avito_2 для названия DomRF"""
    matched_names = []
    matched_set = set()
    
    avito2_col = db['avito_2']
    
    # Ищем только несопоставленные записи
    base_query = {
        '$or': [
            {'is_processed': {'$ne': True}},
            {'is_processed': {'$exists': False}}
        ]
    }
    
    # 1) Поиск по normalized_name в development.name
    if normalized:
        # Сначала пробуем найти по normalized_name, если он есть в avito_2
        # Но обычно его нет, поэтому ищем по development.name
        words = [w for w in normalized.split() if w and len(w) > 2]
        if words:
            pattern = ".*".join(map(re.escape, words))
            cursor = avito2_col.find({
                **base_query,
                'development.name': {'$regex': pattern, '$options': 'i'}
            }, {
                'development.name': 1,
                '_id': 1
            })
            for doc in cursor:
                avito_name = doc.get('development', {}).get('name', '')
                if avito_name and avito_name not in matched_set:
                    matched_names.append({
                        'name': avito_name,
                        '_id': str(doc['_id']),
                        'doc': doc
                    })
                    matched_set.add(avito_name)
    
    # 2) Поиск по ключевым словам в development.name
    if not matched_names and key_words:
        words = [w for w in key_words.split() if w and len(w) > 2]
        if words:
            pattern = ".*".join(map(re.escape, words))
            cursor = avito2_col.find({
                **base_query,
                'development.name': {'$regex': pattern, '$options': 'i'}
            }, {
                'development.name': 1,
                '_id': 1
            })
            for doc in cursor:
                avito_name = doc.get('development', {}).get('name', '')
                if avito_name and avito_name not in matched_set:
                    matched_names.append({
                        'name': avito_name,
                        '_id': str(doc['_id']),
                        'doc': doc
                    })
                    matched_set.add(avito_name)
    
    # 3) Поиск по оригинальному названию
    if not matched_names:
        search_name = extract_key_words(domrf_name)
        if search_name:
            words = [w for w in search_name.split() if w and len(w) > 2]
            if words:
                pattern = ".*".join(map(re.escape, words))
                cursor = avito2_col.find({
                    **base_query,
                    'development.name': {'$regex': pattern, '$options': 'i'}
                }, {
                    'development.name': 1,
                    '_id': 1
                })
                for doc in cursor:
                    avito_name = doc.get('development', {}).get('name', '')
                    if avito_name and avito_name not in matched_set:
                        matched_names.append({
                            'name': avito_name,
                            '_id': str(doc['_id']),
                            'doc': doc
                        })
                        matched_set.add(avito_name)
    
    # Фильтруем результаты
    if matched_names:
        key_words_clean = extract_key_words(domrf_name)
        if key_words_clean:
            filtered_matches = []
            key_words_list = set(key_words_clean.split())
            for match in matched_names:
                match_clean = clean_avito_name(match['name'])
                match_words_list = set(match_clean.split())
                if key_words_list and match_words_list:
                    significant_key_words = {w for w in key_words_list if len(w) >= 4}
                    significant_match_words = {w for w in match_words_list if len(w) >= 4}
                    if significant_key_words and significant_match_words:
                        if significant_key_words & significant_match_words:
                            filtered_matches.append(match)
                    elif not significant_key_words:
                        if key_words_list & match_words_list:
                            filtered_matches.append(match)
                else:
                    filtered_matches.append(match)
            matched_names = filtered_matches if filtered_matches else matched_names
    
    return matched_names


def mark_as_processed(db, source: str, record_id: str) -> bool:
    """Помечает запись как обработанную"""
    try:
        now = datetime.now()
        if source == 'domrf':
            collection = db['domrf']
        elif source == 'avito_2':
            collection = db['avito_2']
        else:
            return False
        
        result = collection.update_one(
            {'_id': ObjectId(record_id)},
            {'$set': {
                'is_processed': True,
                'processed_at': now
            }}
        )
        return result.modified_count == 1
    except Exception as e:
        print(f"❌ Ошибка при пометке записи: {e}")
        return False


def main() -> None:
    try:
        db = get_mongo_connection()
    except Exception as exc:
        print(f"❌ Не удалось подключиться к MongoDB: {exc}")
        sys.exit(1)
    
    # Загружаем все несопоставленные записи из DomRF
    domrf_records = load_domrf_records(db)
    
    print(f"\n📋 Найдено {len(domrf_records)} несопоставленных ЖК из DomRF\n")
    
    if not domrf_records:
        print("✅ Все записи DomRF уже обработаны!")
        return
    
    processed_count = 0
    skipped_count = 0
    
    for orig_name, normalized, domrf_id, domrf_doc in domrf_records:
        key_words = extract_key_words(orig_name)
        search_key = normalized or key_words or orig_name
        
        # Находим совпадения в avito_2
        matched_avito = find_avito2_matches(db, orig_name, normalized, key_words)
        
        if not matched_avito:
            print(f"⏭️  {orig_name}: совпадений в avito_2 не найдено")
            continue
        
        print(f"\n{'='*80}")
        print(f"🏗️  DomRF: {orig_name}")
        print(f"   ID в domrf: {domrf_id}")
        
        if len(matched_avito) == 1:
            match = matched_avito[0]
            print(f"🏢 Avito_2: {match['name']}")
            print(f"   ID в avito_2: {match['_id']}")
            print()
            
            while True:
                answer = input("❓ Отметить как обработанное? (да/нет/пропустить все): ").strip().lower()
                if answer in ['да', 'д', 'yes', 'y']:
                    # Помечаем только DomRF как обработанную
                    # Avito_2 не трогаем, так как там уже все обработано
                    domrf_ok = mark_as_processed(db, 'domrf', domrf_id)
                    
                    if domrf_ok:
                        print("✅ Запись DomRF помечена как обработанная")
                        processed_count += 1
                    else:
                        print("⚠️  Ошибка при пометке записи DomRF")
                    break
                elif answer in ['нет', 'н', 'no', 'n']:
                    print("⏭️  Пропущено")
                    skipped_count += 1
                    break
                elif answer in ['пропустить все', 'пропустить', 'skip all', 'skip']:
                    print("⏭️  Пропускаем все оставшиеся записи")
                    return
                else:
                    print("❌ Введите 'да', 'нет' или 'пропустить все'")
        else:
            print(f"🔍 Найдено {len(matched_avito)} совпадений в avito_2:")
            for idx, match in enumerate(matched_avito, 1):
                print(f"   {idx}. {match['name']} (ID: {match['_id']})")
            print()
            
            while True:
                answer = input("❓ Выберите номер совпадения (1-{}) или 'нет' для пропуска: ".format(len(matched_avito))).strip().lower()
                if answer.isdigit():
                    idx = int(answer) - 1
                    if 0 <= idx < len(matched_avito):
                        match = matched_avito[idx]
                        # Помечаем только DomRF как обработанную
                        # Avito_2 не трогаем, так как там уже все обработано
                        domrf_ok = mark_as_processed(db, 'domrf', domrf_id)
                        
                        if domrf_ok:
                            print("✅ Запись DomRF помечена как обработанная")
                            processed_count += 1
                        else:
                            print("⚠️  Ошибка при пометке записи DomRF")
                        break
                    else:
                        print(f"❌ Введите число от 1 до {len(matched_avito)}")
                elif answer in ['нет', 'н', 'no', 'n']:
                    print("⏭️  Пропущено")
                    skipped_count += 1
                    break
                elif answer in ['пропустить все', 'пропустить', 'skip all', 'skip']:
                    print("⏭️  Пропускаем все оставшиеся записи")
                    return
                else:
                    print("❌ Введите номер или 'нет'")
    
    print(f"\n{'='*80}")
    print(f"✅ Обработано: {processed_count}")
    print(f"⏭️  Пропущено: {skipped_count}")
    print(f"📊 Всего: {len(domrf_records)}")


if __name__ == "__main__":
    main()

