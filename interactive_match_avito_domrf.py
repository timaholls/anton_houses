#!/usr/bin/env python3
"""
Интерактивный скрипт для объединения записей Avito и DomRF
Находит совпадения и спрашивает пользователя, объединять ли их
"""

import json
import sys
import re
import os
import time
import requests
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from typing import Optional, Dict, List, Tuple

# Подтягиваем корень проекта, чтобы импортировать модуль domrf
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from domrf.db_config import get_collection as get_domrf_collection, normalize_name as normalize_domrf_name
except Exception as exc:
    try:
        # Пробуем импортировать напрямую, если domrf в корне проекта
        from db_config import get_collection as get_domrf_collection, normalize_name as normalize_domrf_name
    except Exception as exc2:
        print(f"Не удалось импортировать db_config: {exc}, {exc2}")
        sys.exit(1)


def get_mongo_connection():
    """Получить подключение к MongoDB"""
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:Kfleirb_17@176.98.177.188:27017/admin")
    DB_NAME = os.getenv("DB_NAME", "houses")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db


GEOCODE_CACHE = {}
GEOCODE_API_KEY = os.getenv("GEOCODE_MAPS_API_KEY", "6918e469cfcf9979670183uvrbb9a1f")


def normalize_coordinate(value):
    """Преобразует строку/число в float, поддерживает '54,77'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        value_str = str(value).strip()
        if not value_str:
            return None
        return float(value_str.replace(',', '.'))
    except (TypeError, ValueError):
        return None


def format_full_address(city: str, district: str, street: str, house: str) -> str:
    parts = []
    if city:
        parts.append(f"г. {city}")
    if district:
        parts.append(f"р-он {district}")
    if street:
        parts.append(f"ул. {street}")
    if house:
        parts.append(f"д. {house}")
    return ", ".join(parts)


def fetch_address_from_coords(lat, lon):
    """Получает развернутый адрес через geocode.maps.co"""
    if lat is None or lon is None:
        return {}

    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return {}

    cache_key = (round(lat_f, 6), round(lon_f, 6))
    if cache_key in GEOCODE_CACHE:
        return GEOCODE_CACHE[cache_key]

    try:
        resp = requests.get(
            "https://geocode.maps.co/reverse",
            params={"lat": lat_f, "lon": lon_f, "api_key": GEOCODE_API_KEY},
            headers={"User-Agent": "anton_houses_interactive_match/1.0"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        addr = data.get("address", {}) or {}
        city = addr.get("city") or addr.get("town") or addr.get("village")
        district = addr.get("city_district") or addr.get("district") or addr.get("suburb")
        street = addr.get("road") or addr.get("residential") or addr.get("pedestrian")
        house_number = addr.get("house_number")
        formatted_full = format_full_address(city, district, street, house_number)
        details = {
            "full": formatted_full or data.get("display_name"),
            "city": city,
            "district": district,
            "street": street,
            "house_number": house_number,
        }
        time.sleep(1)  # Защита от rate-limit
        GEOCODE_CACHE[cache_key] = details
        return details
    except Exception:
        return {}


def parse_address_string(address: str):
    """Пытается извлечь части адреса из строки (город, район, улица, дом)."""
    if not address:
        return {}

    city = district = street = house = None
    normalized = address.replace('ё', 'е').replace('Ё', 'Е')
    parts = [p.strip() for p in normalized.split(',') if p.strip()]

    for part in parts:
        lower = part.lower()
        if not city and ('г.' in lower or 'город' in lower or 'уфа' in lower):
            city = (
                part.replace('г.', '')
                    .replace('город', '')
                    .strip()
            )
        elif not district and any(token in lower for token in ['район', 'р-он', 'р-н']):
            district = (
                part.replace('район', '')
                    .replace('р-он', '')
                    .replace('р-н', '')
                    .strip()
            )
        elif not street and any(token in lower for token in ['улица', 'ул.', 'ул ']):
            street = (
                part.replace('улица', '')
                    .replace('ул.', '')
                    .replace('ул', '')
                    .strip()
            )
        elif not house and any(token in lower for token in ['д.', 'дом', 'строение']):
            house = (
                part.replace('дом', '')
                    .replace('д.', '')
                    .replace('строение', '')
                    .strip()
            )

    return {
        'city': city,
        'district': district,
        'street': street,
        'house_number': house,
    }


def format_price_number(price):
    """Форматирует цену в читаемый формат"""
    if not price:
        return ''
    try:
        price_num = float(str(price).replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').strip())
        if price_num >= 1000000:
            return f"{int(price_num / 1000000)} млн ₽"
        elif price_num >= 1000:
            return f"{int(price_num / 1000)} тыс. ₽"
        else:
            return f"{int(price_num)} ₽"
    except (ValueError, TypeError):
        return str(price)


def format_price_per_square(price_per_m2):
    """Форматирует цену за м²"""
    if not price_per_m2:
        return ''
    try:
        price_num = float(str(price_per_m2).replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').strip())
        return f"{int(price_num):,} ₽/м²".replace(',', ' ')
    except (ValueError, TypeError):
        return str(price_per_m2)


def convert_avito2_apartment_to_unified(avito2_apt, plan_title=''):
    """
    Преобразует квартиру из формата avito_2 в формат unified_houses
    """
    area = avito2_apt.get('total_area')
    floor = avito2_apt.get('floor')
    total_floors = avito2_apt.get('total_floors')

    title_parts = []
    if plan_title:
        title_parts.append(plan_title)
    elif avito2_apt.get('plan_title'):
        title_parts.append(avito2_apt.get('plan_title'))

    if area:
        title_parts.append(f"{area} м²")

    if floor and total_floors:
        title_parts.append(f"{floor}/{total_floors} эт.")
    elif floor:
        title_parts.append(f"{floor} эт.")

    title = ', '.join(title_parts) if title_parts else 'Квартира'

    price = format_price_number(avito2_apt.get('price'))
    price_per_square = format_price_per_square(avito2_apt.get('price_per_m2'))

    photo = avito2_apt.get('photo', '')
    image = [photo] if photo else []

    return {
        'title': title,
        'url': avito2_apt.get('url', ''),
        'price': price,
        'pricePerSquare': price_per_square,
        'image': image,
        'area': str(area) if area else '',
        'totalArea': area if area else None,
        'completionDate': avito2_apt.get('completion_status', ''),
        'floor': str(floor) if floor else ''
    }


def convert_avito2_apartment_types(avito2_apt_types):
    """
    Преобразует apartment_types из формата avito_2 в формат unified_houses
    """
    unified_apt_types = {}

    name_mapping = {
        'Студия': 'Студия',
        '1 ком.': '1', '1-комн': '1', '1-комн.': '1',
        '2 ком.': '2', '2': '2', '2-комн': '2', '2-комн.': '2',
        '3': '3', '3-комн': '3', '3-комн.': '3',
        '4': '4', '4-комн': '4', '4-комн.': '4', '4-комн.+': '4', '4-комн+': '4',
        '5-к. квартиры': '5', '5-комн': '5', '5-комн.': '5'
    }

    for type_name, type_data in avito2_apt_types.items():
        simplified_name = name_mapping.get(type_name, type_name)

        apartments = type_data.get('apartments', [])
        if not apartments:
            continue

        unified_apartments = []
        for apt in apartments:
            plan_title = apt.get('plan_title', '') or type_name
            unified_apt = convert_avito2_apartment_to_unified(apt, plan_title)
            unified_apartments.append(unified_apt)

        if unified_apartments:
            unified_apt_types[simplified_name] = {
                'apartments': unified_apartments
            }

    return unified_apt_types


def extract_key_words(name: str) -> str:
    """Извлекает ключевые слова из названия"""
    if not name:
        return ""
    
    normalized = name.lower()
    normalized = normalized.translate(str.maketrans({
        '"': '', '«': '', '»': '', '"': '', '"': '', '„': '',
    }))
    normalized = re.sub(r'\([^)]*\)', '', normalized)
    normalized = re.sub(r'[^\w\s&]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    prefixes = [
        r'^жк\s+', r'^жилой\s+комплекс\s+', r'^комплекс\s+', r'^клубный\s+дом\s+',
        r'^комплекс\s+апартаментов\s+', r'^комплекс\s+высотных\s+домов\s+',
        r'^комплекс\s+жилых\s+апартаментов\s+', r'^квартал\s+', r'^микрорайон\s+',
        r'^знаковый\s+квартал\s+', r'^красочный\s+квартал\s+', r'^городской\s+квартал\s+',
        r'^экогород\s+', r'^ток\s+', r'^дом\s+по\s+ул\.\s*'
    ]
    for prefix in prefixes:
        normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE)
    
    common_words = [
        'жк', 'жилой', 'комплекс', 'комлпекс', 'клубный', 'дом', 'дома', 
        'квартиры', 'литер', 'литера', 'секции', 'секция', 'этап', 'очередь', 
        'паркинг', 'квартал', 'микрорайон', 'апартаментов', 'апартаменты', 
        'высотных', 'экогород', 'клубная', 'резиденция', 'ток'
    ]
    for word in common_words:
        normalized = re.sub(r'\b' + word + r'\b', '', normalized, flags=re.IGNORECASE)
    
    words = normalized.split()
    filtered_words = []
    for word in words:
        if word.isdigit() and len(word) <= 2:
            continue
        if len(word) <= 2 and word.isalpha() and word not in ['8', 'no', 'go', 'le']:
            continue
        filtered_words.append(word)
    
    normalized = ' '.join(filtered_words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def clean_domrf_name(name: str) -> str:
    """Очищает название из DomRF"""
    if not name:
        return ""
    
    normalized = name.lower()
    normalized = normalized.translate(str.maketrans({
        '"': '', '«': '', '»': '', '"': '', '"': '', '„': '',
    }))
    
    prefixes = [
        r'^жк\s+', r'^жилой\s+комплекс\s+', r'^комплекс\s+', r'^клубная\s+резиденция\s+',
        r'^комплекс\s+апартаментов\s+', r'^комплекс\s+жилых\s+апартаментов\s+',
    ]
    for prefix in prefixes:
        normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE)
    
    common_words = [
        'жк', 'жилой', 'комплекс', 'клубная', 'резиденция', 'литер', 'литера',
        'секции', 'секция', 'этап', 'очередь', 'паркинг', 'квартал'
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


def load_avito_records_from_db(db) -> List[Tuple[str, str, str, Dict]]:
    """
    Загружает все несопоставленные записи из коллекции avito_2
    Возвращает список кортежей (name, normalized_name, avito2_id, avito2_record)
    """
    result = []
    avito2_col = db['avito_2']
    unified_col = db['unified_houses']
    
    # Получаем ID уже сопоставленных записей из unified_houses
    matched_avito_ids = set()
    matched_records = list(unified_col.find({}, {
        'avito._id': 1,
        '_source_ids': 1
    }))
    
    for record in matched_records:
        # Проверяем старую структуру
        if record.get('avito', {}).get('_id'):
            matched_avito_ids.add(ObjectId(record['avito']['_id']))
        
        # Проверяем новую структуру с _source_ids
        source_ids = record.get('_source_ids', {})
        if source_ids.get('avito'):
            matched_avito_ids.add(ObjectId(source_ids['avito']))
    
    # Получаем все несопоставленные записи из avito_2
    avito2_conditions = []
    if matched_avito_ids:
        avito2_conditions.append({'_id': {'$nin': list(matched_avito_ids)}})
    
    # Исключаем уже помеченные как сопоставленные
    avito2_conditions.append({'is_matched': {'$ne': True}})
    
    avito2_filter = {'$and': avito2_conditions} if len(avito2_conditions) > 1 else (avito2_conditions[0] if avito2_conditions else {})
    
    avito2_records = list(avito2_col.find(avito2_filter))
    
    for avito2_record in avito2_records:
        try:
            dev = avito2_record.get('development', {})
            name = dev.get('name', 'Без названия')
            normalized = normalize_domrf_name(name) if normalize_domrf_name else ""
            avito2_id = str(avito2_record['_id'])
            
            result.append((name, normalized, avito2_id, avito2_record))
        except Exception as exc:
            print(f"[WARN] Ошибка обработки записи avito_2: {exc}")
    
    return result


def find_domrf_matches(collection, avito_name: str, normalized: str, key_words: str) -> List[Dict]:
    """Находит совпадения в DomRF для названия Avito"""
    matched_names = []
    matched_set = set()
    
    # 1) Точное совпадение по normalized_name
    if normalized:
        cursor = collection.find(
            {"normalized_name": normalized},
            {"objCommercNm": 1, "complexShortName": 1, "_id": 1}
        )
        for doc in cursor:
            name = doc.get("objCommercNm") or doc.get("complexShortName") or ""
            if name and name not in matched_set:
                matched_names.append({
                    'name': name,
                    '_id': str(doc['_id']),
                    'doc': doc
                })
                matched_set.add(name)
    
    # 2) Regex по normalized_name
    if not matched_names and normalized:
        words = [w for w in normalized.split() if w and len(w) > 2]
        if words:
            pattern = ".*".join(map(re.escape, words))
            cursor = collection.find(
                {"normalized_name": {"$regex": pattern, "$options": "i"}},
                {"objCommercNm": 1, "complexShortName": 1, "_id": 1},
            )
            for doc in cursor:
                name = doc.get("objCommercNm") or doc.get("complexShortName") or ""
                if name and name not in matched_set:
                    matched_names.append({
                        'name': name,
                        '_id': str(doc['_id']),
                        'doc': doc
                    })
                    matched_set.add(name)
    
    # 3) Поиск по ключевым словам
    if not matched_names and key_words:
        words = [w for w in key_words.split() if w and len(w) > 2]
        if words:
            pattern = ".*".join(map(re.escape, words))
            cursor = collection.find(
                {"objCommercNm": {"$regex": pattern, "$options": "i"}},
                {"objCommercNm": 1, "complexShortName": 1, "_id": 1},
            )
            for doc in cursor:
                name = doc.get("objCommercNm") or doc.get("complexShortName") or ""
                if name and name not in matched_set:
                    matched_names.append({
                        'name': name,
                        '_id': str(doc['_id']),
                        'doc': doc
                    })
                    matched_set.add(name)
    
    # Фильтруем результаты
    if matched_names:
        key_words_clean = extract_key_words(avito_name)
        if key_words_clean:
            filtered_matches = []
            key_words_list = set(key_words_clean.split())
            for match in matched_names:
                match_clean = clean_domrf_name(match['name'])
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


def merge_records(avito2_record: Dict, domrf_record: Dict, db) -> Optional[str]:
    """
    Объединяет записи Avito_2 и DomRF в unified_houses
    Возвращает ID созданной записи или None при ошибке
    """
    try:
        domrf_col = db['domrf']
        avito2_col = db['avito_2']
        unified_col = db['unified_houses']
        
        # Координаты (приоритет: DomRF -> Avito_2)
        latitude = None
        longitude = None
        
        if domrf_record:
            latitude = normalize_coordinate(domrf_record.get('latitude'))
            longitude = normalize_coordinate(domrf_record.get('longitude'))
        
        if (latitude is None or longitude is None) and avito2_record:
            avito2_dev = avito2_record.get('development', {})
            latitude = normalize_coordinate(avito2_dev.get('latitude') or avito2_record.get('latitude'))
            longitude = normalize_coordinate(avito2_dev.get('longitude') or avito2_record.get('longitude'))
        
        if latitude is None or longitude is None:
            print(f"⚠️  Ошибка: не найдены координаты для объединения")
            return None
        
        # Геокодирование адреса
        geocoded_address = fetch_address_from_coords(latitude, longitude)
        fallback_address = ''
        if avito2_record:
            fallback_address = avito2_record.get('development', {}).get('address', '')
        elif domrf_record:
            domrf_address_parts = []
            if domrf_record.get('city'):
                domrf_address_parts.append(domrf_record['city'])
            if domrf_record.get('district'):
                domrf_address_parts.append(domrf_record['district'])
            if domrf_record.get('street'):
                domrf_address_parts.append(domrf_record['street'])
            fallback_address = ', '.join(domrf_address_parts)
        
        parsed_address = parse_address_string(fallback_address)
        
        # Создаем unified запись
        unified_record = {
            'latitude': latitude,
            'longitude': longitude,
            'source': 'manual',
            'created_by': 'manual',
            'is_featured': False,
            'rating': None,
            'rating_description': '',
            'rating_created_at': None,
            'rating_updated_at': None
        }
        
        unified_record['address_full'] = (geocoded_address or {}).get('full') or fallback_address
        unified_record['address_city'] = (geocoded_address or {}).get('city') or parsed_address.get('city')
        unified_record['address_district'] = (geocoded_address or {}).get('district') or parsed_address.get('district')
        unified_record['address_street'] = (geocoded_address or {}).get('street') or parsed_address.get('street')
        unified_record['address_house'] = (geocoded_address or {}).get('house_number') or parsed_address.get('house_number')
        unified_record['city'] = unified_record['address_city'] or 'Уфа'
        unified_record['district'] = unified_record['address_district'] or ''
        unified_record['street'] = unified_record['address_street'] or ''
        
        # Development из Avito_2
        if avito2_record:
            avito2_dev = avito2_record.get('development', {})
            
            price_range = ''
            price_min = avito2_dev.get('price_range_min')
            price_max = avito2_dev.get('price_range_max')
            if price_min is not None and price_max is not None:
                price_range = f'От {price_min} до {price_max} млн ₽'
            elif price_min is not None:
                price_range = f'От {price_min} млн ₽'
            elif price_max is not None:
                price_range = f'До {price_max} млн ₽'
            
            unified_record['development'] = {
                'name': avito2_dev.get('name', ''),
                'address': unified_record['address_full'] or avito2_dev.get('address', ''),
                'price_range': price_range,
                'parameters': avito2_dev.get('parameters', {}),
                'korpuses': avito2_dev.get('korpuses', []),
                'photos': avito2_dev.get('photos', [])
            }
            
            # Ход строительства ТОЛЬКО из Дом.РФ
            if domrf_record:
                domrf_details = domrf_record.get('object_details', {})
                dr_construction = domrf_details.get('construction_progress', {})
                if dr_construction:
                    construction_stages = dr_construction.get('construction_stages', [])
                    if construction_stages:
                        unified_record['construction_progress'] = {'construction_stages': construction_stages}
                    else:
                        construction_photos = dr_construction.get('photos', [])
                        if construction_photos:
                            unified_record['construction_progress'] = {
                                'construction_stages': [{
                                    'stage': 'Строительство',
                                    'date': '',
                                    'photos': construction_photos
                                }]
                            }
        
        # Apartment_types из Avito_2
        unified_record['apartment_types'] = {}
        if avito2_record:
            avito2_apt_types = avito2_record.get('apartment_types', {})
            unified_record['apartment_types'] = convert_avito2_apartment_types(avito2_apt_types)
        
        # Сохраняем ссылки на исходные записи
        unified_record['_source_ids'] = {
            'domrf': str(domrf_record['_id']) if domrf_record else None,
            'avito': str(avito2_record['_id']) if avito2_record else None,
            'domclick': None
        }
        
        # Сохраняем
        result = unified_col.insert_one(unified_record)
        unified_id = str(result.inserted_id)
        
        # Помечаем исходники как сопоставленные
        try:
            if domrf_record:
                domrf_col.update_one({'_id': domrf_record['_id']}, {'$set': {
                    'is_matched': True,
                    'matched_unified_id': result.inserted_id,
                    'matched_at': datetime.now(),
                    'is_processed': True,
                    'processed_at': datetime.now()
                }})
            if avito2_record:
                avito2_col.update_one({'_id': avito2_record['_id']}, {'$set': {
                    'is_matched': True,
                    'matched_unified_id': result.inserted_id,
                    'matched_at': datetime.now()
                }})
        except Exception as e:
            print(f"⚠️  Предупреждение: не удалось пометить записи как сопоставленные: {e}")
        
        return unified_id
        
    except Exception as e:
        print(f"❌ Ошибка при объединении: {e}")
        import traceback
        traceback.print_exc()
        return None


def main() -> None:
    try:
        collection = get_domrf_collection()
        db = get_mongo_connection()
    except Exception as exc:
        print(f"❌ Не удалось подключиться к коллекции DomRF: {exc}")
        sys.exit(1)
    
    # Загружаем все несопоставленные записи из avito_2
    avito_records = load_avito_records_from_db(db)
    
    print(f"\n📋 Найдено {len(avito_records)} несопоставленных ЖК из avito_2\n")
    
    if not avito_records:
        print("✅ Все записи уже сопоставлены!")
        return
    
    merged_count = 0
    skipped_count = 0
    
    for orig_name, normalized, avito2_id, avito2_record in avito_records:
        
        key_words = extract_key_words(orig_name)
        search_key = normalized or key_words or orig_name
        
        # Находим совпадения в DomRF
        matched_domrf = find_domrf_matches(collection, orig_name, normalized, key_words)
        
        if not matched_domrf:
            print(f"⏭️  {orig_name}: совпадений в DomRF не найдено")
            continue
        
        print(f"\n{'='*80}")
        print(f"🏢 Avito: {orig_name}")
        print(f"   ID в avito_2: {avito2_id}")
        
        if len(matched_domrf) == 1:
            match = matched_domrf[0]
            print(f"🏗️  DomRF: {match['name']}")
            print(f"   ID в domrf: {match['_id']}")
            
            # Получаем полную запись для objId
            domrf_full = collection.find_one({'_id': ObjectId(match['_id'])}, {'objId': 1, 'projectId': 1})
            if domrf_full:
                obj_id = domrf_full.get('objId') or domrf_full.get('projectId')
                if obj_id:
                    print(f"   objId: {obj_id}")
            
            response = input("\n❓ Объединяем? (да/нет/пропустить все): ").strip().lower()
            
            if response in ['нет', 'н', 'no', 'n', 'skip', 'пропустить все']:
                if response == 'пропустить все':
                    print("⏭️  Пропускаем все оставшиеся записи")
                    break
                skipped_count += 1
                continue
            elif response in ['да', 'д', 'yes', 'y', '']:
                # Получаем полную запись DomRF
                domrf_record = collection.find_one({'_id': ObjectId(match['_id'])})
                
                if not domrf_record:
                    print(f"❌ Запись DomRF с ID {match['_id']} не найдена")
                    continue
                
                unified_id = merge_records(avito2_record, domrf_record, db)
                
                if unified_id:
                    print(f"✅ Успешно объединено! ID unified: {unified_id}")
                    merged_count += 1
                else:
                    print(f"❌ Ошибка при объединении")
            else:
                print("⚠️  Непонятный ответ, пропускаем")
                skipped_count += 1
        else:
            print(f"🏗️  Найдено {len(matched_domrf)} совпадений в DomRF:")
            for i, match in enumerate(matched_domrf, 1):
                # Получаем objId для каждого совпадения
                domrf_full = collection.find_one({'_id': ObjectId(match['_id'])}, {'objId': 1, 'projectId': 1})
                obj_id = ''
                if domrf_full:
                    obj_id_val = domrf_full.get('objId') or domrf_full.get('projectId')
                    if obj_id_val:
                        obj_id = f", objId: {obj_id_val}"
                print(f"   {i}. {match['name']} (ID: {match['_id']}{obj_id})")
            
            choice = input("\n❓ Выберите номер для объединения (или 'пропустить'): ").strip().lower()
            
            if choice in ['пропустить', 'skip', 'нет', 'н']:
                skipped_count += 1
                continue
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(matched_domrf):
                    match = matched_domrf[choice_num - 1]
                    domrf_record = collection.find_one({'_id': ObjectId(match['_id'])})
                    
                    if not domrf_record:
                        print(f"❌ Запись DomRF с ID {match['_id']} не найдена")
                        continue
                    
                    unified_id = merge_records(avito2_record, domrf_record, db)
                    
                    if unified_id:
                        print(f"✅ Успешно объединено! ID unified: {unified_id}")
                        merged_count += 1
                    else:
                        print(f"❌ Ошибка при объединении")
                else:
                    print("⚠️  Неверный номер, пропускаем")
                    skipped_count += 1
            except ValueError:
                print("⚠️  Неверный ввод, пропускаем")
                skipped_count += 1
    
    print(f"\n{'='*80}")
    print(f"📊 Итого:")
    print(f"   ✅ Объединено: {merged_count}")
    print(f"   ⏭️  Пропущено: {skipped_count}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

