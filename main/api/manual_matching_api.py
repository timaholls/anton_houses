"""
API функции для ручного сопоставления записей из разных источников (DomRF, Avito, DomClick)
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime
import json
import os
import time
import requests

from ..services.mongo_service import get_mongo_connection
from ..s3_service import s3_client
from .subscription_api import notify_new_future_project
import re

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
    """Получает развернутый адрес через geocode.maps.co (как в update_unified_houses.py)."""
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
            headers={"User-Agent": "anton_houses_manual_matching/1.0"},
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
        # простая защита от rate-limit
        time.sleep(1)
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


def parse_apartment_info(title):
    """
    Парсит title и извлекает площадь и этаж
    Формат: '3-к. квартира, 58,9 м², 14/27 эт.'
    Возвращает: (площадь: float, этаж: int) или (None, None) если не удалось распарсить
    """
    if not title:
        return None, None

    area = None
    floor = None

    # Парсим площадь: ищем паттерн типа "58,9 м²" или "58.9 м²"
    area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
    if area_match:
        area_str = area_match.group(1).replace(',', '.')
        try:
            area = float(area_str)
        except ValueError:
            pass

    # Парсим этаж: ищем паттерн типа "14/27 эт." или "14/27"
    floor_match = re.search(r'(\d+)/(\d+)\s*эт', title)
    if floor_match:
        try:
            floor = int(floor_match.group(1))
        except ValueError:
            pass

    return area, floor


@require_http_methods(["GET"])
def get_unmatched_records(request):
    """API: Получить несопоставленные записи из трех коллекций"""
    try:
        db = get_mongo_connection()
        
        # Получаем коллекции
        domrf_col = db['domrf']
        avito_col = db['avito']
        domclick_col = db['domclick']
        unified_col = db['unified_houses']
        
        # Получаем ID уже сопоставленных записей
        matched_records = list(unified_col.find({}, {
            'domrf.name': 1, 
            'avito._id': 1, 
            'domclick._id': 1,
            '_source_ids': 1
        }))
        
        # Собираем ID сопоставленных записей
        matched_domrf_names = set()
        matched_avito_ids = set()
        matched_domclick_ids = set()
        
        for record in matched_records:
            # Проверяем старую структуру
            if record.get('domrf', {}).get('name'):
                matched_domrf_names.add(record['domrf']['name'])
            if record.get('avito', {}).get('_id'):
                matched_avito_ids.add(ObjectId(record['avito']['_id']))
            if record.get('domclick', {}).get('_id'):
                matched_domclick_ids.add(ObjectId(record['domclick']['_id']))
            
            # Проверяем новую структуру с _source_ids
            source_ids = record.get('_source_ids', {})
            if source_ids.get('domrf'):
                # Для DomRF нужно получить имя из исходной записи
                domrf_record = domrf_col.find_one({'_id': ObjectId(source_ids['domrf'])})
                if domrf_record and domrf_record.get('objCommercNm'):
                    matched_domrf_names.add(domrf_record['objCommercNm'])
            if source_ids.get('avito'):
                matched_avito_ids.add(ObjectId(source_ids['avito']))
            if source_ids.get('domclick'):
                matched_domclick_ids.add(ObjectId(source_ids['domclick']))
        
        # Получаем параметры пагинации и поиска
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 50))  # Увеличиваем до 50 записей
        search = request.GET.get('search', '').strip()
        
        # Формируем фильтры для поиска
        domrf_conditions = [{'is_processed': {'$ne': True}}]  # исключаем обработанные
        if matched_domrf_names:
            domrf_conditions.append({'objCommercNm': {'$nin': list(matched_domrf_names)}})
        if search:
            domrf_conditions.append({'objCommercNm': {'$regex': search, '$options': 'i'}})
        domrf_filter = {'$and': domrf_conditions}

        avito_conditions = [{'is_matched': {'$ne': True}}]
        if matched_avito_ids:
            avito_conditions.append({'_id': {'$nin': list(matched_avito_ids)}})
        if search:
            avito_conditions.append({'development.name': {'$regex': search, '$options': 'i'}})
        avito_filter = {'$and': avito_conditions}

        domclick_conditions = [{'is_matched': {'$ne': True}}]
        if matched_domclick_ids:
            domclick_conditions.append({'_id': {'$nin': list(matched_domclick_ids)}})
        if search:
            domclick_conditions.append({'development.complex_name': {'$regex': search, '$options': 'i'}})
        domclick_filter = {'$and': domclick_conditions}
        
        # Получаем несопоставленные записи (убираем ограничение для лучшего отображения)
        domrf_records = list(domrf_col.find(domrf_filter).limit(100))
        
        domrf_unmatched = [
            {
                '_id': str(r['_id']),
                'name': r.get('objCommercNm', 'Без названия'),
                'url': r.get('url', ''),
                'address': r.get('address', ''),
                'latitude': r.get('latitude'),
                'longitude': r.get('longitude'),
                'objId': r.get('objId') or r.get('projectId')
            }
            for r in domrf_records
        ][:per_page]
        
        avito_records = list(avito_col.find(avito_filter).limit(100))
        avito_unmatched = [
            {
                '_id': str(r['_id']),
                'name': r.get('development', {}).get('name', 'Без названия'),
                'url': r.get('url', ''),
                'address': r.get('development', {}).get('address', ''),
                'development': r.get('development', {}),
                'location': r.get('location', {})
            }
            for r in avito_records
        ][:per_page]
        
        domclick_records = list(domclick_col.find(domclick_filter).limit(100))
        domclick_unmatched = [
            {
                '_id': str(r['_id']),
                'name': r.get('development', {}).get('complex_name', 'Без названия'),
                'url': r.get('url', ''),
                'address': r.get('development', {}).get('address', ''),
                'development': r.get('development', {}),
                'location': r.get('location', {})
            }
            for r in domclick_records
        ][:per_page]
        
        # Считаем общее количество
        total_domrf = domrf_col.count_documents(domrf_filter)
        total_avito = avito_col.count_documents(avito_filter)
        total_domclick = domclick_col.count_documents(domclick_filter)
        
        return JsonResponse({
            'success': True,
            'data': {
                'domrf': domrf_unmatched,
                'avito': avito_unmatched,
                'domclick': domclick_unmatched
            },
            'totals': {
                'domrf': len(domrf_unmatched),
                'avito': len(avito_unmatched),
                'domclick': len(domclick_unmatched),
                'total_domrf': max(0, total_domrf - len(matched_domrf_names)),
                'total_avito': max(0, total_avito - len(matched_avito_ids)),
                'total_domclick': max(0, total_domclick - len(matched_domclick_ids))
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def save_manual_match(request):
    """API: Сохранить ручное сопоставление (новая упрощенная структура)"""
    try:
        data = json.loads(request.body)
        domrf_id = data.get('domrf_id')
        avito_id = data.get('avito_id')
        domclick_id = data.get('domclick_id')
        is_featured = data.get('is_featured', False)  # Флаг "показывать на главной"
        agent_id = (data.get('agent_id') or '').strip()  # Закрепляем за агентом
        
        # Координаты могут быть переданы напрямую (из модального окна)
        provided_latitude = data.get('latitude')
        provided_longitude = data.get('longitude')
        
        # Проверка: должно быть минимум 2 источника (исключаем null)
        selected_sources = [domrf_id, avito_id, domclick_id]
        selected_count = sum(1 for source_id in selected_sources if source_id and source_id != 'null')
        
        if selected_count < 2:
            return JsonResponse({
                'success': False,
                'error': 'Необходимо выбрать минимум 2 источника для сопоставления'
            }, status=400)
        
        db = get_mongo_connection()
        
        # Получаем полные записи
        domrf_col = db['domrf']
        avito_col = db['avito']
        domclick_col = db['domclick']
        unified_col = db['unified_houses']
        
        # Получаем DomRF запись если она выбрана
        domrf_record = None
        if domrf_id and domrf_id != 'null':
            try:
                domrf_record = domrf_col.find_one({'_id': ObjectId(domrf_id)})
                if not domrf_record:
                    return JsonResponse({
                        'success': False,
                        'error': 'Запись DomRF не найдена'
                    }, status=404)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка получения DomRF записи: {str(e)}'
                }, status=400)
        
        avito_record = None
        if avito_id and avito_id != 'null':
            try:
                avito_record = avito_col.find_one({'_id': ObjectId(avito_id)})
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка получения Avito записи: {str(e)}'
                }, status=400)
        
        domclick_record = None
        if domclick_id and domclick_id != 'null':
            try:
                domclick_record = domclick_col.find_one({'_id': ObjectId(domclick_id)})
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка получения DomClick записи: {str(e)}'
                }, status=400)
        
        # Проверяем, что хотя бы одна запись найдена
        if not avito_record and not domclick_record:
            return JsonResponse({
                'success': False,
                'error': 'Не найдены записи для объединения'
            }, status=400)
        
        # === НОВАЯ УПРОЩЕННАЯ СТРУКТУРА ===
        
        # 1. Координаты (приоритет: переданные напрямую -> DomRF -> Avito -> DomClick)
        latitude = None
        longitude = None
        
        # Сначала проверяем переданные координаты (из модального окна)
        if provided_latitude and provided_longitude:
            latitude = normalize_coordinate(provided_latitude)
            longitude = normalize_coordinate(provided_longitude)
            if latitude is None or longitude is None:
                return JsonResponse({
                    'success': False,
                    'error': f'Некорректный формат координат. Широта: {provided_latitude}, Долгота: {provided_longitude}',
                    'error_type': 'invalid_coordinates'
                }, status=400)
        elif domrf_record:
            latitude = normalize_coordinate(domrf_record.get('latitude'))
            longitude = normalize_coordinate(domrf_record.get('longitude'))
        elif avito_record:
            # Пытаемся взять координаты из Avito
            latitude = normalize_coordinate(avito_record.get('latitude'))
            longitude = normalize_coordinate(avito_record.get('longitude'))
        elif domclick_record:
            # Пытаемся взять координаты из DomClick
            latitude = normalize_coordinate(domclick_record.get('latitude'))
            longitude = normalize_coordinate(domclick_record.get('longitude'))
        
        # Если координат нет ни в одном источнике - требуем ввести вручную
        if latitude is None or longitude is None:
            # Формируем подробное сообщение об ошибке
            error_details = []
            if domrf_record:
                error_details.append(f"DomRF: широта={domrf_record.get('latitude')}, долгота={domrf_record.get('longitude')}")
            if avito_record:
                error_details.append(f"Avito: широта={avito_record.get('latitude')}, долгота={avito_record.get('longitude')}")
            if domclick_record:
                error_details.append(f"DomClick: широта={domclick_record.get('latitude')}, долгота={domclick_record.get('longitude')}")
            
            return JsonResponse({
                'success': False,
                'error': 'Необходимо ввести координаты. Координаты не найдены ни в одном источнике.',
                'error_type': 'missing_coordinates',
                'details': {
                    'provided_latitude': provided_latitude,
                    'provided_longitude': provided_longitude,
                    'sources': error_details
                }
            }, status=400)
        
        geocoded_address = fetch_address_from_coords(latitude, longitude)
        fallback_address = ''
        if avito_record:
            fallback_address = avito_record.get('development', {}).get('address', '')
        elif domclick_record:
            fallback_address = domclick_record.get('development', {}).get('address', '')
        parsed_address = parse_address_string(fallback_address)

        unified_record = {
            'latitude': latitude,
            'longitude': longitude,
            'source': 'manual',
            'created_by': 'manual',
            'is_featured': is_featured,  # Флаг "показывать на главной"
            # Поля адреса будут заполнены чуть ниже
            # Поля рейтинга
            'rating': None,  # Рейтинг от 1 до 5
            'rating_description': '',  # Описание причины низкого рейтинга
            'rating_created_at': None,  # Дата создания рейтинга
            'rating_updated_at': None   # Дата обновления рейтинга
        }
        unified_record['address_full'] = (geocoded_address or {}).get('full') or fallback_address
        unified_record['address_city'] = (geocoded_address or {}).get('city') or parsed_address.get('city')
        unified_record['address_district'] = (geocoded_address or {}).get('district') or parsed_address.get('district')
        unified_record['address_street'] = (geocoded_address or {}).get('street') or parsed_address.get('street')
        unified_record['address_house'] = (geocoded_address or {}).get('house_number') or parsed_address.get('house_number')
        unified_record['city'] = unified_record['address_city'] or 'Уфа'
        unified_record['district'] = unified_record['address_district'] or ''
        unified_record['street'] = unified_record['address_street'] or ''
        
        # Привязка агента
        if agent_id:
            try:
                unified_record['agent_id'] = ObjectId(agent_id)
            except Exception:
                unified_record['agent_id'] = None
        
        # 2. Development из Avito + photos из DomClick
        if avito_record:
            avito_dev = avito_record.get('development', {})
            unified_record['development'] = {
                'name': avito_dev.get('name', ''),
                'address': unified_record['address_full'] or avito_dev.get('address', ''),
                'price_range': avito_dev.get('price_range', ''),
                'parameters': avito_dev.get('parameters', {}),
                'korpuses': avito_dev.get('korpuses', []),
                'photos': []  # Будет заполнено из DomClick
            }
            
            # Добавляем фото ЖК и ход строительства из DomClick
            if domclick_record:
                domclick_dev = domclick_record.get('development', {})
                unified_record['development']['photos'] = domclick_dev.get('photos', [])
                # Ход строительства: берём из development.construction_progress,
                # если нет — из корня записи DomClick
                dc_construction = domclick_dev.get('construction_progress') or domclick_record.get('construction_progress')
                if dc_construction:
                    unified_record['construction_progress'] = dc_construction
        
        # 3. Объединяем apartment_types (Avito + фото из DomClick)
        unified_record['apartment_types'] = {}
        
        if avito_record and domclick_record:
            avito_apt_types = avito_record.get('apartment_types', {})
            domclick_apt_types = domclick_record.get('apartment_types', {})
            
            # Маппинг старых названий на новые упрощенные
            name_mapping = {
                # Студия
                'Студия': 'Студия',
                # 1-комнатные (разные варианты названий из Avito и DomClick)
                '1 ком.': '1',
                '1-комн': '1',
                '1-комн.': '1',
                # 2-комнатные (ИСПРАВЛЕНО: добавляем все варианты)
                '2 ком.': '2',  # ← ДОБАВЛЕНО: маппинг для Avito
                '2': '2',
                '2-комн': '2',
                '2-комн.': '2',
                # 3-комнатные
                '3': '3',
                '3-комн': '3',
                '3-комн.': '3',
                # 4-комнатные
                '4': '4',
                '4-комн': '4',
                '4-комн.': '4',
                '4-комн.+': '4',
                '4-комн+': '4'
            }
            
            # Сначала обрабатываем все типы из DomClick (чтобы не пропустить 1-комнатные)
            processed_types = set()
            
            for dc_type_name, dc_type_data in domclick_apt_types.items():
                # Упрощаем название типа
                simplified_name = name_mapping.get(dc_type_name, dc_type_name)
                
                # Пропускаем если уже обработали этот упрощенный тип
                if simplified_name in processed_types:
                    continue
                processed_types.add(simplified_name)
                
                # Получаем квартиры из DomClick
                dc_apartments = dc_type_data.get('apartments', [])
                if not dc_apartments:
                    continue
                
                # Берем ВСЕ данные из DomClick без сопоставления с Avito (как в update_unified_houses.py)
                combined_apartments = []
                
                for i, dc_apt in enumerate(dc_apartments):
                    # Получаем ВСЕ фото этой квартиры из DomClick как МАССИВ
                    # Проверяем оба поля для совместимости
                    apartment_photos = dc_apt.get('photos') or dc_apt.get('images') or []
                    
                    # Если фото нет - пропускаем эту квартиру
                    if not apartment_photos:
                        continue
                    
                    # Парсим информацию о квартире из DomClick
                    dc_title = dc_apt.get('title', '')
                    dc_area, dc_floor = parse_apartment_info(dc_title)
                    
                    # Берем ВСЕ данные из DomClick
                    combined_apartments.append({
                        'title': dc_title,  # Title из DomClick
                        'area': str(dc_area) if dc_area else '',  # Площадь из DomClick как строка
                        'totalArea': dc_area if dc_area else None,  # Площадь из DomClick как число (для совместимости)
                        'floor': str(dc_floor) if dc_floor else '',  # Этаж из DomClick
                        'price': dc_apt.get('price', ''),  # Цена из DomClick (если есть)
                        'pricePerSquare': dc_apt.get('pricePerSquare', ''),  # Цена за м² из DomClick (если есть)
                        'completionDate': dc_apt.get('completionDate', ''),  # Дата сдачи из DomClick (если есть)
                        'url': dc_apt.get('url', '') or dc_apt.get('urlPath', ''),  # URL из DomClick (если есть)
                        'image': apartment_photos  # МАССИВ всех фото этой планировки из DomClick!
                    })
                
                # Добавляем в результат все квартиры из DomClick с фото
                if combined_apartments:
                    unified_record['apartment_types'][simplified_name] = {
                        'apartments': combined_apartments
                    }
        
        # Сохраняем ссылки на исходные записи для отладки
        unified_record['_source_ids'] = {
            'domrf': str(domrf_record['_id']) if domrf_record else None,
            'avito': str(avito_record['_id']) if avito_record else None,
            'domclick': str(domclick_record['_id']) if domclick_record else None
        }
        
        # Сохраняем
        result = unified_col.insert_one(unified_record)

        # Помечаем исходники как сопоставленные, чтобы скрывать их из списков
        try:
            if avito_record:
                avito_col.update_one({'_id': avito_record['_id']}, {'$set': {
                    'is_matched': True,
                    'matched_unified_id': result.inserted_id,
                    'matched_at': datetime.now()
                }})
            if domclick_record:
                domclick_col.update_one({'_id': domclick_record['_id']}, {'$set': {
                    'is_matched': True,
                    'matched_unified_id': result.inserted_id,
                    'matched_at': datetime.now()
                }})
            if domrf_record:
                # DomRF раньше помечался is_processed, сохраним обратную совместимость
                domrf_col.update_one({'_id': domrf_record['_id']}, {'$set': {
                    'is_processed': True,
                    'processed_at': datetime.now(),
                    'matched_unified_id': result.inserted_id
                }})
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'message': 'Сопоставление успешно сохранено',
            'unified_id': str(result.inserted_id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"]) 
def preview_manual_match(request):
    """API: Предпросмотр объединения без сохранения. Возвращает структуру как для unified_get."""
    try:
        data = json.loads(request.body)
        domrf_id = data.get('domrf_id')
        avito_id = data.get('avito_id')
        domclick_id = data.get('domclick_id')
        is_featured = data.get('is_featured', False)
        agent_id = (data.get('agent_id') or '').strip()
        provided_latitude = data.get('latitude')
        provided_longitude = data.get('longitude')

        selected_sources = [domrf_id, avito_id, domclick_id]
        selected_count = sum(1 for source_id in selected_sources if source_id and source_id != 'null')
        if selected_count < 2:
            return JsonResponse({'success': False, 'error': 'Необходимо выбрать минимум 2 источника для сопоставления'}, status=400)

        db = get_mongo_connection()
        domrf_col = db['domrf']
        avito_col = db['avito']
        domclick_col = db['domclick']

        domrf_record = None
        if domrf_id and domrf_id != 'null':
            domrf_record = domrf_col.find_one({'_id': ObjectId(domrf_id)})

        avito_record = None
        if avito_id and avito_id != 'null':
            avito_record = avito_col.find_one({'_id': ObjectId(avito_id)})

        domclick_record = None
        if domclick_id and domclick_id != 'null':
            domclick_record = domclick_col.find_one({'_id': ObjectId(domclick_id)})

        if not avito_record and not domclick_record:
            return JsonResponse({'success': False, 'error': 'Не найдены записи для объединения'}, status=400)

        # Координаты (для предпросмотра — необязательны)
        latitude = None
        longitude = None
        if provided_latitude and provided_longitude:
            latitude = normalize_coordinate(provided_latitude)
            longitude = normalize_coordinate(provided_longitude)
            if latitude is None or longitude is None:
                return JsonResponse({
                    'success': False,
                    'error': f'Некорректный формат координат. Широта: {provided_latitude}, Долгота: {provided_longitude}',
                    'error_type': 'invalid_coordinates'
                }, status=400)
        else:
            if domrf_record:
                latitude = normalize_coordinate(domrf_record.get('latitude'))
                longitude = normalize_coordinate(domrf_record.get('longitude'))
            if latitude is None or longitude is None:
                if avito_record:
                    latitude = normalize_coordinate(avito_record.get('latitude'))
                    longitude = normalize_coordinate(avito_record.get('longitude'))
            if latitude is None or longitude is None:
                if domclick_record:
                    latitude = normalize_coordinate(domclick_record.get('latitude'))
                    longitude = normalize_coordinate(domclick_record.get('longitude'))

        geocoded_address = {}
        if latitude is not None and longitude is not None:
            geocoded_address = fetch_address_from_coords(latitude, longitude)
        fallback_address = ''
        if avito_record:
            fallback_address = avito_record.get('development', {}).get('address', '')
        elif domclick_record:
            fallback_address = domclick_record.get('development', {}).get('address', '')
        parsed_address = parse_address_string(fallback_address)

        fallback_city = ''
        if not (geocoded_address or {}).get('city'):
            if fallback_address and 'уфа' in fallback_address.lower():
                fallback_city = 'Уфа'
            else:
                fallback_city = 'Уфа'

        preview = {
            'latitude': latitude,
            'longitude': longitude,
            'source': 'manual_preview',
            'created_by': 'manual',
            'is_featured': is_featured,
            'address_full': (geocoded_address or {}).get('full') or fallback_address,
            'address_city': (geocoded_address or {}).get('city') or parsed_address.get('city'),
            'address_district': (geocoded_address or {}).get('district') or parsed_address.get('district'),
            'address_street': (geocoded_address or {}).get('street') or parsed_address.get('street'),
            'address_house': (geocoded_address or {}).get('house_number') or parsed_address.get('house_number'),
            'city': (geocoded_address or {}).get('city') or parsed_address.get('city') or fallback_city,
            'district': (geocoded_address or {}).get('district') or parsed_address.get('district') or '',
            'street': (geocoded_address or {}).get('street') or parsed_address.get('street') or '',
            'rating': None,
            'rating_description': '',
            'rating_created_at': None,
            'rating_updated_at': None
        }

        if agent_id:
            try:
                preview['agent_id'] = str(ObjectId(agent_id))
            except Exception:
                preview['agent_id'] = None

        if avito_record:
            avito_dev = avito_record.get('development', {})
            preview['development'] = {
                'name': avito_dev.get('name', ''),
                'address': preview['address_full'] or avito_dev.get('address', ''),
                'price_range': avito_dev.get('price_range', ''),
                'parameters': avito_dev.get('parameters', {}),
                'korpuses': avito_dev.get('korpuses', []),
                'photos': []
            }
            if domclick_record:
                domclick_dev = domclick_record.get('development', {})
                preview['development']['photos'] = domclick_dev.get('photos', [])
                dc_construction = domclick_dev.get('construction_progress') or domclick_record.get('construction_progress')
                if dc_construction:
                    preview['construction_progress'] = dc_construction

        preview['apartment_types'] = {}
        if avito_record and domclick_record:
            avito_apt_types = avito_record.get('apartment_types', {})
            domclick_apt_types = domclick_record.get('apartment_types', {})
            name_mapping = {
                'Студия': 'Студия',
                '1 ком.': '1','1-комн': '1','1-комн.': '1',
                '2 ком.': '2','2': '2','2-комн': '2','2-комн.': '2',
                '3': '3','3-комн': '3','3-комн.': '3',
                '4': '4','4-комн': '4','4-комн.': '4','4-комн.+': '4','4-комн+': '4'
            }
            processed = set()
            for dc_type_name, dc_type_data in domclick_apt_types.items():
                simplified_name = name_mapping.get(dc_type_name, dc_type_name)
                if simplified_name in processed:
                    continue
                processed.add(simplified_name)
                dc_apartments = dc_type_data.get('apartments', []) or []
                if not dc_apartments:
                    continue
                
                # Берем ВСЕ данные из DomClick без сопоставления с Avito (как в update_unified_houses.py)
                combined_apartments = []
                for i, dc_apt in enumerate(dc_apartments):
                    # Получаем ВСЕ фото этой квартиры из DomClick как МАССИВ
                    # Проверяем оба поля для совместимости
                    apartment_photos = dc_apt.get('photos') or dc_apt.get('images') or []
                    if not apartment_photos:
                        continue
                    
                    # Парсим информацию о квартире из DomClick
                    dc_title = dc_apt.get('title', '')
                    dc_area, dc_floor = parse_apartment_info(dc_title)
                    
                    # Берем ВСЕ данные из DomClick
                    combined_apartments.append({
                        'title': dc_title,  # Title из DomClick
                        'area': str(dc_area) if dc_area else '',  # Площадь из DomClick как строка
                        'totalArea': dc_area if dc_area else None,  # Площадь из DomClick как число (для совместимости)
                        'floor': str(dc_floor) if dc_floor else '',  # Этаж из DomClick
                        'price': dc_apt.get('price', ''),  # Цена из DomClick (если есть)
                        'pricePerSquare': dc_apt.get('pricePerSquare', ''),  # Цена за м² из DomClick (если есть)
                        'completionDate': dc_apt.get('completionDate', ''),  # Дата сдачи из DomClick (если есть)
                        'url': dc_apt.get('url', '') or dc_apt.get('urlPath', ''),  # URL из DomClick (если есть)
                        'image': apartment_photos  # МАССИВ всех фото этой планировки из DomClick!
                    })
                if combined_apartments:
                    preview['apartment_types'][simplified_name] = {'apartments': combined_apartments}

        preview['_source_ids'] = {
            'domrf': str(domrf_record['_id']) if domrf_record else None,
            'avito': str(avito_record['_id']) if avito_record else None,
            'domclick': str(domclick_record['_id']) if domclick_record else None
        }

        # Приводим ObjectId к строкам для фронтенда
        preview = convert_objectid_to_str(preview)
        return JsonResponse({'success': True, 'item': preview})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def domrf_create(request):
    """API: Создать новую запись DomRF"""
    try:
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        developer = request.POST.get('developer', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # Валидация обязательных полей
        if not name or not address or not city or not latitude or not longitude:
            return JsonResponse({
                'success': False,
                'error': 'Заполните все обязательные поля'
            }, status=400)
        
        # Проверяем корректность координат
        try:
            lat_float = float(latitude)
            lng_float = float(longitude)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Некорректные координаты'
            }, status=400)
        
        db = get_mongo_connection()
        domrf_col = db['domrf']
        
        # Проверяем, нет ли уже записи с таким названием
        existing = domrf_col.find_one({'objCommercNm': name})
        if existing:
            return JsonResponse({
                'success': False,
                'error': 'Запись с таким названием уже существует'
            }, status=400)
        
        # Создаем новую запись DomRF
        domrf_record = {
            'objCommercNm': name,
            'address': address,
            'city': city,
            'latitude': lat_float,
            'longitude': lng_float,
            'developer': developer,
            'description': description,
            'is_active': is_active,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'source': 'manual_creation'
        }
        
        result = domrf_col.insert_one(domrf_record)
        
        return JsonResponse({
            'success': True,
            'message': 'Запись DomRF создана успешно',
            'domrf_id': str(result.inserted_id)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_record(request):
    """API: Удалить запись из коллекции"""
    try:
        data = json.loads(request.body)
        source = data.get('source')  # 'domrf', 'avito', 'domclick'
        record_id = data.get('record_id')
        
        if not source or not record_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указан источник или ID записи'
            }, status=400)
        
        if source not in ['domrf', 'avito', 'domclick', 'future_complexes']:
            return JsonResponse({
                'success': False,
                'error': 'Неверный источник'
            }, status=400)
        
        db = get_mongo_connection()
        collection = db[source]
        
        # Проверяем, что запись существует
        try:
            existing_record = collection.find_one({'_id': ObjectId(record_id)})
            if not existing_record:
                return JsonResponse({
                    'success': False,
                    'error': 'Запись не найдена'
                }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Ошибка поиска записи: {str(e)}'
            }, status=400)
        
        # Удаляем запись
        try:
            result = collection.delete_one({'_id': ObjectId(record_id)})
            if result.deleted_count == 1:
                # Если удаляем будущий проект, снимаем флаг is_processed с исходной записи DomRF
                if source == 'future_complexes':
                    future_record = existing_record
                    if future_record and future_record.get('source_domrf_id'):
                        domrf_collection = db['domrf']
                        domrf_collection.update_one(
                            {'_id': ObjectId(future_record['source_domrf_id'])},
                            {'$unset': {'is_processed': '', 'processed_at': '', 'future_project_id': ''}}
                        )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Запись из {source} успешно удалена'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Запись не была удалена'
                }, status=500)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Ошибка удаления записи: {str(e)}'
            }, status=500)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_future_project(request):
    """API: Создать запись в будущих проектах из DomRF"""
    try:
        data = json.loads(request.body)
        domrf_id = data.get('domrf_id')
        
        if not domrf_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указан ID записи DomRF'
            }, status=400)
        
        db = get_mongo_connection()
        domrf_collection = db['domrf']
        future_collection = db['future_complexes']
        
        # Получаем запись DomRF
        try:
            domrf_record = domrf_collection.find_one({'_id': ObjectId(domrf_id)})
            if not domrf_record:
                return JsonResponse({
                    'success': False,
                    'error': 'Запись DomRF не найдена'
                }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Ошибка поиска записи DomRF: {str(e)}'
            }, status=400)
        
        # Извлекаем object_details из DomRF записи
        object_details = domrf_record.get('object_details', {})
        
        # Создаем запись для будущих проектов
        now = datetime.now()
        future_project = {
            'name': data.get('name', domrf_record.get('objCommercNm', 'Без названия')),
            'description': data.get('description', domrf_record.get('description', '')),
            'city': data.get('city', 'Уфа'),
            'district': data.get('district', domrf_record.get('district', '')),
            'street': data.get('street', domrf_record.get('street', '')),
            'delivery_date': datetime.strptime(data.get('delivery_date', '2026-12-31'), '%Y-%m-%d'),
            'sales_start': datetime.strptime(data.get('sales_start', '2024-01-01'), '%Y-%m-%d') if data.get('sales_start') else None,
            'house_class': data.get('house_class', ''),
            'developer': data.get('developer', domrf_record.get('developer', '')),
            'is_active': True,
            'is_featured': False,
            'created_at': now,
            'updated_at': now,
            'images': [],
            'construction_progress': [],
            'object_details': domrf_record.get('object_details', {}),
            'latitude': domrf_record.get('latitude'),
            'longitude': domrf_record.get('longitude'),
            'source_domrf_id': str(domrf_record['_id']),
            # Поля из формы (приоритетно) или из DomRF
            'energy_efficiency': data.get('energy_efficiency', domrf_record.get('energy_efficiency', '')),
            'floors': data.get('floors', domrf_record.get('floors', '')),
            'contractors': data.get('contractors', domrf_record.get('contractors', '')),
            # Основные характеристики
            'walls_material': data.get('walls_material', domrf_record.get('walls_material', '')),
            'decoration_type': data.get('decoration_type', domrf_record.get('decoration_type', '')),
            'free_planning': data.get('free_planning', domrf_record.get('free_planning', '')),
            'ceiling_height': data.get('ceiling_height', domrf_record.get('ceiling_height', '')),
            'living_area': data.get('living_area', domrf_record.get('living_area', '')),
            # Благоустройство двора
            'bicycle_paths': data.get('bicycle_paths', domrf_record.get('bicycle_paths', '')),
            'children_playgrounds_count': data.get('children_playgrounds_count', 0),
            'sports_grounds_count': data.get('sports_grounds_count', 0),
            # Доступная среда
            'ramp_available': data.get('ramp_available', domrf_record.get('ramp', '')),
            'lowering_platforms_available': data.get('lowering_platforms_available', domrf_record.get('lowering_platforms', '')),
            # Лифты и подъезды
            'entrances_count': data.get('entrances_count', domrf_record.get('entrances_count', '')),
            'passenger_elevators_count': data.get('passenger_elevators_count', 0),
            'cargo_elevators_count': data.get('cargo_elevators_count', 0),
            # Сохраняем фотографии и другие данные из DomRF
            'gallery_photos': object_details.get('gallery_photos', domrf_record.get('gallery_photos', [])),
            'construction_progress_data': object_details.get('construction_progress', domrf_record.get('construction_progress', {})),
            'objPublDt': domrf_record.get('objPublDt', ''),
            'objId': domrf_record.get('objId', ''),
            'url': domrf_record.get('url', ''),
            'address': domrf_record.get('address', ''),
            'completion_date': domrf_record.get('completion_date', ''),
            'apartments_count': domrf_record.get('apartments_count', ''),
            'parking': domrf_record.get('parking', ''),
            'material': domrf_record.get('material', ''),
            'finishing': domrf_record.get('finishing', ''),
            'heating': domrf_record.get('heating', ''),
            'water_supply': domrf_record.get('water_supply', ''),
            'sewerage': domrf_record.get('sewerage', ''),
            'gas_supply': domrf_record.get('gas_supply', ''),
            'electricity': domrf_record.get('electricity', ''),
            'ventilation': domrf_record.get('ventilation', ''),
            'security': domrf_record.get('security', ''),
            'concierge': domrf_record.get('concierge', ''),
            'intercom': domrf_record.get('intercom', ''),
            'video_surveillance': domrf_record.get('video_surveillance', ''),
            'access_control': domrf_record.get('access_control', ''),
            'fire_safety': domrf_record.get('fire_safety', ''),
            'children_playground': domrf_record.get('children_playground', ''),
            'sports_ground': domrf_record.get('sports_ground', ''),
            'landscaping': domrf_record.get('landscaping', ''),
            'underground_parking': domrf_record.get('underground_parking', ''),
            'ground_parking': domrf_record.get('ground_parking', ''),
            'guest_parking': domrf_record.get('guest_parking', ''),
            # Сохраняем всю структуру flats_data для статистики квартир (может быть в object_details или в корне)
            'flats_data': domrf_record.get('object_details', {}).get('flats_data', domrf_record.get('flats_data', {}))
        }
        
        # Вставляем в коллекцию будущих проектов
        try:
            result = future_collection.insert_one(future_project)
            if result.inserted_id:
                # Помечаем запись в DomRF как обработанную (не удаляем!)
                domrf_collection.update_one(
                    {'_id': ObjectId(domrf_id)},
                    {'$set': {'is_processed': True, 'processed_at': now, 'future_project_id': str(result.inserted_id)}}
                )
                
                # Отправляем уведомления подписчикам
                try:
                    notify_new_future_project(future_project)
                except Exception as e:
                    print(f"Ошибка отправки уведомлений о новом проекте: {e}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Проект успешно перенесен в будущие проекты',
                    'future_project_id': str(result.inserted_id)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Не удалось создать запись в будущих проектах'
                }, status=500)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Ошибка создания записи: {str(e)}'
            }, status=500)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_future_projects(request):
    """API: Получить список будущих проектов для manual_matching"""
    try:
        db = get_mongo_connection()
        collection = db['future_complexes']
        
        # Получаем все активные проекты
        projects = list(collection.find({'is_active': True}).sort('_id', -1))
        
        # Форматируем для отображения
        formatted_projects = []
        for project in projects:
            formatted_projects.append({
                '_id': str(project['_id']),
                'name': project.get('name', 'Без названия'),
                'city': project.get('city', ''),
                'district': project.get('district', ''),
                'delivery_date': project.get('delivery_date', ''),
                'price_from': project.get('price_from', 0),
                'developer': project.get('developer', ''),
                'created_at': project.get('created_at', ''),
                'updated_at': project.get('updated_at', '')
            })
        
        return JsonResponse({
            'success': True,
            'data': formatted_projects
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_future_project(request, project_id):
    """API: Получить один будущий проект по ID"""
    try:
        db = get_mongo_connection()
        collection = db['future_complexes']
        
        # Получаем проект по ID
        project = collection.find_one({'_id': ObjectId(project_id), 'is_active': True})
        
        if not project:
            return JsonResponse({
                'success': False,
                'error': 'Проект не найден'
            }, status=404)
        
        # Форматируем для отображения
        formatted_project = {
            '_id': str(project['_id']),
            'name': project.get('name', 'Без названия'),
            'city': project.get('city', ''),
            'district': project.get('district', ''),
            'street': project.get('street', ''),
            'delivery_date': project.get('delivery_date', ''),
            'sales_start': project.get('sales_start', ''),
            'house_class': project.get('house_class', ''),
            'developer': project.get('developer', ''),
            'description': project.get('description', ''),
            'price_from': project.get('price_from', 0),
            'created_at': project.get('created_at', ''),
            'updated_at': project.get('updated_at', '')
        }
        
        return JsonResponse({
            'success': True,
            'data': formatted_project
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_future_project(request, project_id):
    """API: Обновить будущий проект"""
    try:
        data = json.loads(request.body)
        
        db = get_mongo_connection()
        collection = db['future_complexes']
        
        # Проверяем существование проекта
        project = collection.find_one({'_id': ObjectId(project_id), 'is_active': True})
        if not project:
            return JsonResponse({
                'success': False,
                'error': 'Проект не найден'
            }, status=404)
        
        # Подготавливаем данные для обновления
        update_data = {
            'name': data.get('name', project.get('name')),
            'city': data.get('city', project.get('city')),
            'district': data.get('district', project.get('district')),
            'street': data.get('street', project.get('street')),
            'house_class': data.get('house_class', project.get('house_class')),
            'developer': data.get('developer', project.get('developer')),
            'description': data.get('description', project.get('description')),
            'updated_at': datetime.now()
        }
        
        # Обрабатываем даты
        if data.get('delivery_date'):
            update_data['delivery_date'] = datetime.strptime(data.get('delivery_date'), '%Y-%m-%d')
        
        if data.get('sales_start'):
            update_data['sales_start'] = datetime.strptime(data.get('sales_start'), '%Y-%m-%d')
        elif 'sales_start' in data and not data.get('sales_start'):
            update_data['sales_start'] = None
        
        # Обновляем проект
        result = collection.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return JsonResponse({
                'success': True,
                'message': 'Проект успешно обновлен'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Не удалось обновить проект'
            }, status=500)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_domrf_data(request, domrf_id):
    """API: Получить данные DomRF записи для заполнения формы"""
    try:
        db = get_mongo_connection()
        collection = db['domrf']
        
        # Получаем запись DomRF
        domrf_record = collection.find_one({'_id': ObjectId(domrf_id)})
        if not domrf_record:
            return JsonResponse({
                'success': False,
                'error': 'Запись DomRF не найдена'
            }, status=404)
        
        # Извлекаем данные из объекта developer
        developer_info = domrf_record.get('developer', {})
        developer_name = ''
        if isinstance(developer_info, dict):
            developer_name = developer_info.get('shortName', developer_info.get('fullName', ''))
        
        # Извлекаем данные из object_details
        object_details = domrf_record.get('object_details', {})
        main_characteristics = object_details.get('main_characteristics', {})
        yard_improvement = object_details.get('yard_improvement', {})
        parking_space = object_details.get('parking_space', {})
        accessible_environment = object_details.get('accessible_environment', {})
        elevators = object_details.get('elevators', {})
        construction_progress = object_details.get('construction_progress', {})
        
        # Извлекаем фотографии
        gallery_photos = object_details.get('gallery_photos', domrf_record.get('gallery_photos', []))
        construction_photos = []
        if construction_progress and isinstance(construction_progress, dict):
            # Проверяем новую структуру с этапами
            construction_stages = construction_progress.get('construction_stages', [])
            if construction_stages:
                # Собираем все фотографии из всех этапов
                for stage in construction_stages:
                    if stage.get('photos'):
                        construction_photos.extend(stage['photos'])
            else:
                # Fallback на старую структуру
                construction_photos = construction_progress.get('photos', [])
        
        # Форматируем данные для формы
        formatted_data = {
            'name': domrf_record.get('objCommercNm', domrf_record.get('name', 'Без названия')),
            'city': domrf_record.get('city', 'Уфа'),
            'district': domrf_record.get('district', ''),
            'street': domrf_record.get('street', ''),
            'price_from': domrf_record.get('price_from', ''),
            'price_to': domrf_record.get('price_to', ''),
            'area_from': domrf_record.get('area_from', ''),
            'area_to': domrf_record.get('area_to', ''),
            'rooms': domrf_record.get('rooms', ''),
            'house_class': domrf_record.get('house_class', main_characteristics.get('Класс недвижимости', '')),
            'developer': developer_name,
            'description': domrf_record.get('description', ''),
            'latitude': domrf_record.get('latitude'),
            'longitude': domrf_record.get('longitude'),
            'object_details': object_details,
            'gallery_photos': gallery_photos,
            'construction_progress': construction_progress,
            'construction_photos': construction_photos,
            # Дополнительные поля из DomRF и object_details
            'energy_efficiency': object_details.get('energy_efficiency', domrf_record.get('energy_efficiency', '')),
            'contractors': object_details.get('contractors', domrf_record.get('contractors', '')),
            'objPublDt': domrf_record.get('objPublDt', ''),
            'objId': domrf_record.get('objId', ''),
            'url': domrf_record.get('url', ''),
            'address': domrf_record.get('address', ''),
            'completion_date': domrf_record.get('completion_date', ''),
            'floors': main_characteristics.get('Количество этажей', domrf_record.get('floors', '')),
            'apartments_count': domrf_record.get('apartments_count', ''),
            'parking': domrf_record.get('parking', ''),
            'elevators': domrf_record.get('elevators', ''),
            'material': main_characteristics.get('Материал стен', domrf_record.get('material', '')),
            'finishing': main_characteristics.get('Тип отделки', domrf_record.get('finishing', '')),
            'heating': domrf_record.get('heating', ''),
            'water_supply': domrf_record.get('water_supply', ''),
            'sewerage': domrf_record.get('sewerage', ''),
            'gas_supply': domrf_record.get('gas_supply', ''),
            'electricity': domrf_record.get('electricity', ''),
            'ventilation': domrf_record.get('ventilation', ''),
            'security': domrf_record.get('security', ''),
            'concierge': domrf_record.get('concierge', ''),
            'intercom': domrf_record.get('intercom', ''),
            'video_surveillance': domrf_record.get('video_surveillance', ''),
            'access_control': domrf_record.get('access_control', ''),
            'fire_safety': domrf_record.get('fire_safety', ''),
            'children_playground': domrf_record.get('children_playground', ''),
            'sports_ground': domrf_record.get('sports_ground', ''),
            'landscaping': domrf_record.get('landscaping', ''),
            'bicycle_paths': domrf_record.get('bicycle_paths', ''),
            'ramp': domrf_record.get('ramp', ''),
            'lowering_platforms': domrf_record.get('lowering_platforms', ''),
            'underground_parking': domrf_record.get('underground_parking', ''),
            'ground_parking': domrf_record.get('ground_parking', ''),
            'guest_parking': domrf_record.get('guest_parking', ''),
            'cargo_elevators': domrf_record.get('cargo_elevators', ''),
            'passenger_elevators': domrf_record.get('passenger_elevators', ''),
            'entrances_count': domrf_record.get('entrances_count', ''),
            'free_planning': main_characteristics.get('Свободная планировка', domrf_record.get('free_planning', '')),
            'ceiling_height': main_characteristics.get('Высота потолков', domrf_record.get('ceiling_height', '')),
            'living_area': main_characteristics.get('Жилая площадь', domrf_record.get('living_area', '')),
            'walls_material': main_characteristics.get('Материал стен', domrf_record.get('walls_material', '')),
            'decoration_type': main_characteristics.get('Тип отделки', domrf_record.get('decoration_type', '')),
            # Данные из yard_improvement
            'bicycle_paths_available': yard_improvement.get('Велосипедные дорожки', ''),
            'children_playgrounds_count': yard_improvement.get('Количество детских площадок', ''),
            'sports_grounds_count': yard_improvement.get('Количество спортивных площадок', ''),
            # Данные из accessible_environment
            'ramp_available': accessible_environment.get('Наличие пандуса', ''),
            'lowering_platforms_available': accessible_environment.get('Наличие понижающих площадок', ''),
            # Данные из elevators
            'entrances_count_detail': elevators.get('Количество подъездов', ''),
            'passenger_elevators_count': elevators.get('Количество пассажирских лифтов', ''),
            'cargo_elevators_count': elevators.get('Количество грузовых лифтов', '')
        }
        
        return JsonResponse({
            'success': True,
            'data': formatted_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_photo(request):
    """API: Удалить фотографию (файл и запись в базе)"""
    try:
        import os
        from django.conf import settings
        
        data = json.loads(request.body)
        photo_path = data.get('photo_path')
        photo_type = data.get('photo_type')  # 'gallery' или 'construction'
        
        if not photo_path or not photo_type:
            return JsonResponse({
                'success': False,
                'error': 'Не указан путь к фото или тип'
            }, status=400)
        
        # Удаляем файл из S3
        try:
            s3_key = s3_client.extract_key_from_url(photo_path)
            if s3_key:
                s3_client.delete_object(s3_key)
        except Exception as e:
            pass
        
        # Удаляем путь из базы данных
        db = get_mongo_connection()
        collection = db['domrf']
        
        if photo_type == 'gallery':
            # Удаляем из gallery_photos
            collection.update_many(
                {'gallery_photos': photo_path},
                {'$pull': {'gallery_photos': photo_path}}
            )
        elif photo_type == 'construction':
            # Удаляем из construction_progress (новая структура с этапами)
            # Сначала пытаемся удалить из construction_stages[].photos
            collection.update_many(
                {'object_details.construction_progress.construction_stages.photos': photo_path},
                {'$pull': {'object_details.construction_progress.construction_stages.$[].photos': photo_path}}
            )
            
            # Также удаляем из старой структуры construction_progress.photos (fallback)
            collection.update_many(
                {'object_details.construction_progress.photos': photo_path},
                {'$pull': {'object_details.construction_progress.photos': photo_path}}
            )
            
            # И из корневой структуры (если есть)
            collection.update_many(
                {'construction_progress.photos': photo_path},
                {'$pull': {'construction_progress.photos': photo_path}}
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Фотография удалена'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_apartment_stats(request, domrf_id):
    """API: Получить статистику квартир по типам"""
    try:
        db = get_mongo_connection()
        collection = db['domrf']
        
        # Получаем запись DomRF
        domrf_record = collection.find_one({'_id': ObjectId(domrf_id)})
        if not domrf_record:
            return JsonResponse({
                'success': False,
                'error': 'Запись DomRF не найдена'
            }, status=404)
        
        # Получаем flats_data (может быть в object_details или в корне)
        object_details = domrf_record.get('object_details', {})
        flats_data = object_details.get('flats_data', domrf_record.get('flats_data', {}))
        
        if not flats_data:
            return JsonResponse({
                'success': True,
                'data': []
            })
        
        # Подсчитываем статистику по типам квартир
        stats = {}
        
        for apt_type, apartments in flats_data.items():
            if isinstance(apartments, dict):
                # Новая структура: {flats: [...], total_count: ...}
                apartments_list = apartments.get('flats', [])
                count = apartments.get('total_count', len(apartments_list))
            elif isinstance(apartments, list):
                # Старая структура: просто массив
                apartments_list = apartments
                count = len(apartments_list)
            else:
                continue
                
            areas = []
            
            for apt in apartments_list:
                if isinstance(apt, dict):
                    # Пробуем найти площадь в разных полях
                    area_value = apt.get('totalArea') or apt.get('area') or apt.get('total_area')
                    if area_value:
                        try:
                            area = float(area_value)
                            if area > 0:
                                areas.append(area)
                        except (ValueError, TypeError):
                            pass
            
            if count > 0:
                min_area = min(areas) if areas else 0
                max_area = max(areas) if areas else 0
                
                # Нормализуем название типа квартиры
                # Преобразуем oneRoom -> 1, twoRoom -> 2, threeRoom -> 3, fourRoom -> 4+
                import re
                type_name = apt_type
                
                # Маппинг для английских названий
                room_mapping = {
                    'oneRoom': '1',
                    'twoRoom': '2',
                    'threeRoom': '3',
                    'fourRoom': '4+'
                }
                
                if apt_type in room_mapping:
                    type_name = room_mapping[apt_type]
                else:
                    # Пытаемся извлечь число из названия
                    type_name = apt_type.replace('Room', '').replace('_комн', '').replace('комн', '').replace('комнат', '').strip()
                    if not type_name.isdigit():
                        numbers = re.findall(r'\d+', apt_type)
                        type_name = numbers[0] if numbers else apt_type
                
                stats[type_name] = {
                    'type': type_name,
                    'count': count,
                    'min_area': round(min_area, 1) if min_area > 0 else 0,
                    'max_area': round(max_area, 1) if max_area > 0 else 0
                }
        
        # Сортируем по количеству комнат
        sorted_stats = sorted(stats.values(), key=lambda x: int(x['type']) if x['type'].isdigit() else 999)
        
        return JsonResponse({
            'success': True,
            'data': sorted_stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def toggle_featured(request):
    """API: Переключить флаг is_featured для ЖК"""
    try:
        data = json.loads(request.body)
        complex_id = data.get('complex_id')
        is_featured = data.get('is_featured')
        
        if not complex_id:
            return JsonResponse({'success': False, 'error': 'Не указан complex_id'}, status=400)
        
        db = get_mongo_connection()
        unified_collection = db['unified_houses']
        residential_collection = db['residential_complexes']
        
        # Обновляем флаг в объединенной записи
        unified_collection.update_one(
            {'_id': ObjectId(complex_id)},
            {'$set': {'is_featured': is_featured}}
        )
        
        # Также обновляем в коллекции residential_complexes если есть
        residential_collection.update_one(
            {'_id': ObjectId(complex_id)},
            {'$set': {'is_featured': is_featured}}
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_unified_records(request):
    """API: Получить уже объединенные записи"""
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Параметры пагинации
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        skip = (page - 1) * per_page
        
        # Получаем записи (сортируем по дате создания, новые сверху)
        records = list(unified_col.find({}).sort('_id', -1).skip(skip).limit(per_page))
        total = unified_col.count_documents({})
        
        # Форматируем записи
        formatted_records = []
        for record in records:
            # Имя ЖК для новой и старой структуры
            unified_name = None
            domrf_name = 'N/A'
            avito_name = 'N/A'
            domclick_name = 'N/A'
            
            if 'development' in record and 'avito' not in record:
                # НОВАЯ СТРУКТУРА
                unified_name = record.get('development', {}).get('name', 'N/A')
                # Для новой структуры источники определяем по _source_ids
                source_ids = record.get('_source_ids', {})
                if source_ids:
                    # Пытаемся получить названия из исходных записей (если доступны)
                    domrf_name = 'N/A' if not source_ids.get('domrf') else 'DomRF запись'
                    avito_name = 'N/A' if not source_ids.get('avito') else 'Avito запись'
                    domclick_name = 'N/A' if not source_ids.get('domclick') else 'DomClick запись'
            else:
                # СТАРАЯ СТРУКТУРА (для обратной совместимости)
                unified_name = (record.get('avito', {}) or {}).get('development', {}) .get('name') or \
                               (record.get('domclick', {}) or {}).get('development', {}) .get('complex_name') or \
                               (record.get('domrf', {}) or {}).get('name', 'N/A')
                domrf_name = record.get('domrf', {}).get('name', 'N/A')
                avito_name = record.get('avito', {}).get('development', {}).get('name', 'N/A') if record.get('avito') else 'N/A'
                domclick_name = record.get('domclick', {}).get('development', {}).get('complex_name', 'N/A') if record.get('domclick') else 'N/A'

            formatted_records.append({
                '_id': str(record['_id']),
                'name': unified_name or 'N/A',
                'domrf_name': domrf_name,
                'avito_name': avito_name,
                'domclick_name': domclick_name,
                'source': record.get('source', 'unknown'),
                'is_featured': record.get('is_featured', False)
            })
        
        return JsonResponse({
            'success': True,
            'data': formatted_records,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def convert_objectid_to_str(obj):
    """Рекурсивно конвертирует все ObjectId в строки для JSON сериализации"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj


@require_http_methods(["GET"]) 
def unified_get(request, unified_id: str):
    """API: получить одну объединенную запись для редактирования."""
    try:
        db = get_mongo_connection()
        col = db['unified_houses']
        doc = col.find_one({'_id': ObjectId(unified_id)})
        if not doc:
            return JsonResponse({'success': False, 'error': 'Запись не найдена'}, status=404)
        # Автозаполняем адрес, если он отсутствует, но есть координаты
        addr_fields = ['address_full', 'address_city', 'address_district', 'address_street', 'address_house']
        has_address = any(doc.get(field) for field in addr_fields)
        lat = doc.get('latitude')
        lon = doc.get('longitude')
        if not has_address:
            updates = {}
            if lat is not None and lon is not None:
                geo = fetch_address_from_coords(lat, lon)
                if geo:
                    updates.update({
                        'address_full': geo.get('full') or doc.get('address_full'),
                        'address_city': geo.get('city') or doc.get('address_city'),
                        'address_district': geo.get('district') or doc.get('address_district'),
                        'address_street': geo.get('street') or doc.get('address_street'),
                        'address_house': geo.get('house_number') or doc.get('address_house'),
                    })
            if not updates or not any(updates.values()):
                fallback_addr = doc.get('development', {}).get('address') or doc.get('address_full')
                parsed = parse_address_string(fallback_addr)
                if parsed:
                    updates.update({
                        'address_full': doc.get('address_full') or fallback_addr,
                        'address_city': parsed.get('city') or doc.get('address_city'),
                        'address_district': parsed.get('district') or doc.get('address_district'),
                        'address_street': parsed.get('street') or doc.get('address_street'),
                        'address_house': parsed.get('house_number') or doc.get('address_house'),
                    })
            if updates:
                if not doc.get('city') and updates.get('address_city'):
                    updates['city'] = updates['address_city']
                if not doc.get('district') and updates.get('address_district'):
                    updates['district'] = updates['address_district']
                if not doc.get('street') and updates.get('address_street'):
                    updates['street'] = updates['address_street']
                doc.update({k: v for k, v in updates.items() if v})
                col.update_one({'_id': ObjectId(unified_id)}, {'$set': {k: v for k, v in updates.items() if v}})
        # Конвертируем все ObjectId в строки
        doc = convert_objectid_to_str(doc)
        return JsonResponse({'success': True, 'item': doc})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"]) 
def unified_update(request, unified_id: str):
    """API: обновить произвольные поля объединенной записи (безопасный апдейт)."""
    try:
        db = get_mongo_connection()
        col = db['unified_houses']
        # Поддерживаем form-data и JSON
        payload = {}
        if request.content_type and 'application/json' in request.content_type:
            payload = json.loads(request.body or '{}')
        else:
            payload = {k: v for k, v in request.POST.items()}

        # Нельзя менять _id
        payload.pop('_id', None)
        
        # Приведение типов для известных полей
        if 'is_featured' in payload:
            val = payload['is_featured']
            payload['is_featured'] = True if str(val).lower() in ('1', 'true', 'on') else False
        
        if 'agent_id' in payload:
            try:
                payload['agent_id'] = ObjectId(str(payload['agent_id'])) if payload['agent_id'] else None
            except Exception:
                payload['agent_id'] = None
        
        # Обработка координат
        if 'latitude' in payload:
            try:
                payload['latitude'] = float(payload['latitude']) if payload['latitude'] else None
            except (ValueError, TypeError):
                payload['latitude'] = None
                
        if 'longitude' in payload:
            try:
                payload['longitude'] = float(payload['longitude']) if payload['longitude'] else None
            except (ValueError, TypeError):
                payload['longitude'] = None
        
        # Обработка рейтинга
        if 'rating' in payload:
            try:
                rating = int(payload['rating']) if payload['rating'] else None
                if rating is not None and (rating < 1 or rating > 5):
                    return JsonResponse({'success': False, 'error': 'Рейтинг должен быть от 1 до 5'}, status=400)
                payload['rating'] = rating
                # Обновляем даты рейтинга
                if rating is not None:
                    payload['rating_updated_at'] = datetime.now()
                    if not col.find_one({'_id': ObjectId(unified_id), 'rating': {'$exists': True}}):
                        payload['rating_created_at'] = datetime.now()
            except (ValueError, TypeError):
                payload['rating'] = None
        
        # Обработка вложенных полей (development.name, development.parameters.X и т.д.)
        update_operations = {}
        for key, value in payload.items():
            if '.' in key:
                # Это вложенное поле
                update_operations[key] = value
            else:
                # Это простое поле
                update_operations[key] = value
        
        if not update_operations:
            return JsonResponse({'success': False, 'error': 'Нет полей для обновления'}, status=400)

        col.update_one({'_id': ObjectId(unified_id)}, {'$set': update_operations})
        return JsonResponse({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_location_options(request):
    """API: Получить списки городов, районов и улиц для фильтров каталога"""
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем уникальные города
        cities = unified_col.distinct('city', {'city': {'$ne': None, '$ne': ''}})
        cities = [city for city in cities if city]  # Убираем пустые значения
        
        # Получаем уникальные районы
        districts = unified_col.distinct('district', {'district': {'$ne': None, '$ne': ''}})
        districts = [district for district in districts if district]
        
        # Получаем уникальные улицы
        streets = unified_col.distinct('street', {'street': {'$ne': None, '$ne': ''}})
        streets = [street for street in streets if street]
        
        return JsonResponse({
            'success': True,
            'cities': sorted(cities),
            'districts': sorted(districts),
            'streets': sorted(streets)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_not_recommended_objects(request):
    """API: получить объекты с рейтингом меньше 3 для страницы 'Не рекомендуем'."""
    try:
        db = get_mongo_connection()
        col = db['unified_houses']
        
        # Параметры пагинации
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 12))
        skip = (page - 1) * per_page
        
        # Получаем объекты с рейтингом меньше или равным 3
        query = {
            'rating': {'$lte': 3, '$exists': True}
        }
        
        records = list(col.find(query).sort('rating_created_at', -1).skip(skip).limit(per_page))
        total = col.count_documents(query)
        
        # Форматируем записи
        formatted_records = []
        for record in records:
            # Получаем основную информацию
            name = ''
            if 'development' in record and 'name' in record['development']:
                name = record['development']['name']
            elif 'domrf' in record and 'objCommercNm' in record['domrf']:
                name = record['domrf']['objCommercNm']
            elif 'avito' in record and 'name' in record['avito']:
                name = record['avito']['name']
            
            # Получаем адрес
            address = ''
            if 'development' in record and 'address' in record['development']:
                address = record['development']['address']
            elif 'domrf' in record and 'address' in record['domrf']:
                address = record['domrf']['address']
            elif 'avito' in record and 'address' in record['avito']:
                address = record['avito']['address']
            
            # Получаем изображения
            images = []
            if 'development' in record and 'photos' in record['development']:
                images = record['development']['photos']
            elif 'domclick' in record and 'photos' in record['domclick']:
                images = record['domclick']['photos']
            
            formatted_records.append({
                '_id': str(record['_id']),
                'name': name,
                'address': address,
                'images': images[:3] if images else [],  # Берем первые 3 изображения
                'rating': record.get('rating'),
                'rating_description': record.get('rating_description', ''),
                'city': record.get('city', 'Уфа'),
                'district': record.get('district', ''),
                'street': record.get('street', ''),
                'latitude': record.get('latitude'),
                'longitude': record.get('longitude'),
                'rating_created_at': record.get('rating_created_at'),
                'rating_updated_at': record.get('rating_updated_at')
            })
        
        return JsonResponse({
            'success': True, 
            'records': formatted_records,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ===================== Mortgage Programs (Mongo) =====================
@require_http_methods(["GET"])
def mortgage_programs_list(request):
    """API: список ипотечных программ из MongoDB."""
    try:
        db = get_mongo_connection()
        col = db['mortgage_programs']
        unified_col = db['unified_houses']
        items = []
        for doc in col.find({}).sort('rate', 1):
            # Получаем информацию о связанных ЖК
            complexes = []
            if doc.get('complexes'):
                for complex_id in doc.get('complexes', []):
                    try:
                        complex_doc = unified_col.find_one({'_id': ObjectId(complex_id)})
                        if complex_doc:
                            # Получаем название ЖК из новой или старой структуры
                            complex_name = None
                            if 'development' in complex_doc and 'avito' not in complex_doc:
                                complex_name = complex_doc.get('development', {}).get('name', '')
                            else:
                                complex_name = (complex_doc.get('avito', {}) or {}).get('development', {}).get('name') or \
                                             (complex_doc.get('domclick', {}) or {}).get('development', {}).get('complex_name', '')
                            
                            if complex_name:
                                complexes.append({
                                    '_id': str(complex_id),
                                    'name': complex_name
                                })
                    except Exception:
                        continue
            
            items.append({
                '_id': str(doc.get('_id')),
                'name': doc.get('name', ''),
                'rate': float(doc.get('rate', 0)),
                'is_active': bool(doc.get('is_active', True)),
                'is_individual': bool(doc.get('is_individual', False)),
                'complexes': complexes
            })
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mortgage_programs_create(request):
    """API: создать ипотечную программу."""
    try:
        db = get_mongo_connection()
        col = db['mortgage_programs']
        name = request.POST.get('name', '').strip()
        rate_raw = request.POST.get('rate', '').strip()
        is_individual = request.POST.get('is_individual', 'false') in ['true', 'on', '1']
        complexes = request.POST.getlist('complexes')  # Список ID ЖК
        
        if not name or not rate_raw:
            return JsonResponse({'success': False, 'error': 'Название и ставка обязательны'}, status=400)
        try:
            rate = float(rate_raw.replace(',', '.'))
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Неверный формат ставки'}, status=400)
        
        # Валидация ЖК для индивидуальных программ
        complex_ids = []
        if is_individual and complexes:
            unified_col = db['unified_houses']
            for complex_id in complexes:
                try:
                    if unified_col.find_one({'_id': ObjectId(complex_id)}):
                        complex_ids.append(ObjectId(complex_id))
                except Exception:
                    continue
        
        doc = {
            'name': name,
            'rate': rate,
            'is_active': request.POST.get('is_active', 'true') in ['true', 'on', '1'],
            'is_individual': is_individual,
            'complexes': complex_ids,
            'created_at': datetime.utcnow(),
        }
        res = col.insert_one(doc)
        return JsonResponse({'success': True, 'id': str(res.inserted_id)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




@require_http_methods(["GET"])
def get_complexes_for_mortgage(request):
    """API: получить список ЖК для выбора в ипотечных программах."""
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем все ЖК
        complexes = []
        for doc in unified_col.find({}).sort('_id', -1):
            # Получаем название ЖК из новой или старой структуры
            complex_name = None
            if 'development' in doc and 'avito' not in doc:
                complex_name = doc.get('development', {}).get('name', '')
            else:
                complex_name = (doc.get('avito', {}) or {}).get('development', {}).get('name') or \
                             (doc.get('domclick', {}) or {}).get('development', {}).get('complex_name', '')
            
            if complex_name:
                # Получаем изображения из новой или старой структуры
                photos = []
                if 'development' in doc and 'avito' not in doc:
                    # Новая структура
                    photos = doc.get('development', {}).get('photos', [])
                else:
                    # Старая структура - берем из avito или domclick
                    avito_photos = (doc.get('avito', {}) or {}).get('photos', [])
                    domclick_photos = (doc.get('domclick', {}) or {}).get('photos', [])
                    photos = avito_photos + domclick_photos
                
                # Получаем отдельные поля изображений
                image_url = doc.get('image_url')
                image_2_url = doc.get('image_2_url')
                image_3_url = doc.get('image_3_url')
                image_4_url = doc.get('image_4_url')
                
            # Извлекаем данные точно как в каталоге (UnifiedComplexAdapter)
            development = doc.get('development', {})
            
            # Адрес - как в каталоге
            address = development.get('address', '')
            if not address:
                address = doc.get('street', '')
            
            # Город
            city = doc.get('city', 'Уфа')
            
            # Дата сдачи - пока не используется в каталоге, оставляем None
            completion_date = None
            
            # Квартиры - как в каталоге (из apartment_types)
            apartment_types = doc.get('apartment_types', {})
            total_apartments = len(apartment_types) if apartment_types else None
            
            # Цена - как в каталоге
            price_range = development.get('price_range', '')
            
            complexes.append({
                '_id': str(doc.get('_id')),
                'name': complex_name,
                'rating': doc.get('rating', 0),
                'photos': photos,
                'image_url': image_url,
                'image_2_url': image_2_url,
                'image_3_url': image_3_url,
                'image_4_url': image_4_url,
                'address': address,
                'city': city,
                'completion_date': completion_date,
                'total_apartments': total_apartments,
                'price_range': price_range,
                'price_display': price_range
            })
        
        return JsonResponse({'success': True, 'complexes': complexes})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_mortgage_program(request, program_id):
    """API: получить данные ипотечной программы для редактирования."""
    try:
        db = get_mongo_connection()
        col = db['mortgage_programs']
        
        # Получаем программу
        program = col.find_one({'_id': ObjectId(program_id)})
        if not program:
            return JsonResponse({'success': False, 'error': 'Программа не найдена'}, status=404)
        
        # Получаем информацию о связанных ЖК
        complexes = []
        if program.get('complexes'):
            unified_col = db['unified_houses']
            for complex_id in program.get('complexes', []):
                try:
                    complex_doc = unified_col.find_one({'_id': ObjectId(complex_id)})
                    if complex_doc:
                        # Получаем название ЖК из новой или старой структуры
                        complex_name = None
                        if 'development' in complex_doc and 'avito' not in complex_doc:
                            complex_name = complex_doc.get('development', {}).get('name', '')
                        else:
                            complex_name = (complex_doc.get('avito', {}) or {}).get('development', {}).get('name') or \
                                         (complex_doc.get('domclick', {}) or {}).get('development', {}).get('complex_name', '')
                        
                        if complex_name:
                            complexes.append({
                                '_id': str(complex_id),
                                'name': complex_name
                            })
                except Exception:
                    continue
        
        return JsonResponse({
            'success': True,
            'program': {
                '_id': str(program.get('_id')),
                'name': program.get('name', ''),
                'rate': float(program.get('rate', 0)),
                'is_active': bool(program.get('is_active', True)),
                'is_individual': bool(program.get('is_individual', False)),
                'complexes': complexes
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"]) 
def promotions_create(request):
    """Создать акцию для ЖК (MongoDB promotions)."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        complex_id = payload.get('complex_id')
        title = (payload.get('title') or '').strip()
        description = (payload.get('description') or '').strip()
        starts_at = payload.get('starts_at')
        ends_at = payload.get('ends_at')

        if not complex_id or not title:
            return JsonResponse({'success': False, 'error': 'complex_id и title обязательны'}, status=400)

        db = get_mongo_connection()
        promotions = db['promotions']

        doc = {
            'complex_id': ObjectId(complex_id),
            'title': title[:120],
            'description': description[:2000],
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        if starts_at: doc['starts_at'] = starts_at
        if ends_at: doc['ends_at'] = ends_at

        inserted = promotions.insert_one(doc)
        return JsonResponse({'success': True, 'id': str(inserted.inserted_id)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"]) 
def promotions_list(request):
    """Список акций (опционально только активные)."""
    try:
        active = request.GET.get('active')
        db = get_mongo_connection()
        promotions = db['promotions']
        q = {}
        if active in ('1', 'true', 'True'):
            q['is_active'] = True
        items = []
        unified = db['unified_houses']
        for p in promotions.find(q).sort('created_at', -1):
            comp_name = ''
            try:
                comp = unified.find_one({'_id': ObjectId(str(p.get('complex_id')))})
                if comp:
                    if 'development' in comp and 'avito' not in comp:
                        comp_name = (comp.get('development', {}) or {}).get('name', '')
                    else:
                        comp_name = (comp.get('avito', {}) or {}).get('development', {}) .get('name') or (comp.get('domclick', {}) or {}).get('development', {}) .get('complex_name', '')
            except Exception:
                comp_name = ''
            items.append({
                '_id': str(p.get('_id')),
                'complex_id': str(p.get('complex_id')) if p.get('complex_id') else None,
                'complex_name': comp_name,
                'title': p.get('title'),
                'description': p.get('description'),
                'is_active': p.get('is_active', True)
            })
        return JsonResponse({'success': True, 'data': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"]) 
def promotions_delete(request, promo_id):
    try:
        db = get_mongo_connection()
        promotions = db['promotions']
        promotions.delete_one({'_id': ObjectId(promo_id)})
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"]) 
def promotions_toggle(request, promo_id):
    try:
        db = get_mongo_connection()
        promotions = db['promotions']
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        if 'is_active' in payload:
            new_val = bool(payload.get('is_active'))
        else:
            doc = promotions.find_one({'_id': ObjectId(promo_id)})
            current = bool(doc.get('is_active', True)) if doc else True
            new_val = not current
        promotions.update_one({'_id': ObjectId(promo_id)}, {'$set': {'is_active': new_val, 'updated_at': datetime.utcnow()}})
        return JsonResponse({'success': True, 'is_active': new_val})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"]) 
def unified_delete(request, unified_id):
    try:
        db = get_mongo_connection()
        unified = db['unified_houses']
        
        # Сначала получаем документ чтобы узнать связанные файлы
        doc = unified.find_one({'_id': ObjectId(unified_id)})
        if not doc:
            return JsonResponse({'success': False, 'error': 'Запись не найдена'}, status=404)
        
        # Удаляем связанные файлы из галереи
        gallery = db['gallery']
        gallery_files = gallery.find({'content_type': 'residential_complex', 'object_id': str(unified_id)})
        for gallery_file in gallery_files:
            if gallery_file.get('image'):
                try:
                    s3_key = s3_client.extract_key_from_url(gallery_file['image'].name)
                    if s3_key:
                        s3_client.delete_object(s3_key)
                except:
                    pass  # Игнорируем ошибки удаления файлов
            if gallery_file.get('video_file'):
                try:
                    s3_key = s3_client.extract_key_from_url(gallery_file['video_file'].name)
                    if s3_key:
                        s3_client.delete_object(s3_key)
                except:
                    pass  # Игнорируем ошибки удаления файлов
        
        # Удаляем записи из галереи
        gallery.delete_many({'content_type': 'residential_complex', 'object_id': str(unified_id)})
        
        # Перед удалением сбрасываем флаги matched у исходников, чтобы они снова появились в списках
        try:
            source_ids = doc.get('_source_ids', {}) if isinstance(doc, dict) else {}
            domrf_id = source_ids.get('domrf')
            avito_id = source_ids.get('avito')
            domclick_id = source_ids.get('domclick')

            domrf_col = db['domrf']
            avito_col = db['avito']
            domclick_col = db['domclick']

            if domrf_id:
                try:
                    domrf_col.update_one({'_id': ObjectId(domrf_id)}, {'$unset': {
                        'is_processed': '', 'processed_at': '', 'matched_unified_id': ''
                    }})
                except Exception:
                    pass
            # Обратная совместимость: старые структуры могли хранить вложенные id
            if not avito_id:
                avito_id = (doc.get('avito') or {}).get('_id')
            if not domclick_id:
                domclick_id = (doc.get('domclick') or {}).get('_id')

            if avito_id:
                try:
                    avito_col.update_one({'_id': ObjectId(avito_id)}, {'$unset': {
                        'is_matched': '', 'matched_unified_id': '', 'matched_at': ''
                    }})
                except Exception:
                    pass
            if domclick_id:
                try:
                    domclick_col.update_one({'_id': ObjectId(domclick_id)}, {'$unset': {
                        'is_matched': '', 'matched_unified_id': '', 'matched_at': ''
                    }})
                except Exception:
                    pass
        except Exception:
            # Сбрасывание флагов не должно блокировать удаление unified
            pass

        # Удаляем объединенную запись
        result = unified.delete_one({'_id': ObjectId(unified_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'Запись не найдена'}, status=404)
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ===================== Photo Deletion APIs =====================

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_apartment_photo(request):
    """API: Удалить фото квартиры из unified_houses"""
    try:
        data = json.loads(request.body)
        unified_id = data.get('unified_id')
        room_type = data.get('room_type')
        apt_idx = data.get('apt_idx')
        photo_idx = data.get('photo_idx')
        photo_url = data.get('photo_url')
        
        if not all([unified_id, room_type, apt_idx is not None, photo_idx is not None, photo_url]):
            return JsonResponse({
                'success': False,
                'error': 'Не все параметры указаны'
            }, status=400)
        
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем документ
        doc = unified_col.find_one({'_id': ObjectId(unified_id)})
        if not doc:
            return JsonResponse({'success': False, 'error': 'Запись не найдена'}, status=404)
        
        # Удаляем файл из S3
        try:
            s3_key = s3_client.extract_key_from_url(photo_url)
            if s3_key:
                s3_client.delete_object(s3_key)
        except Exception as e:
            pass  # Игнорируем ошибки удаления файла
        
        # Удаляем фото из базы данных
        apartment_types = doc.get('apartment_types', {})
        if room_type in apartment_types:
            apartments = apartment_types[room_type].get('apartments', [])
            if apt_idx < len(apartments):
                apartment = apartments[apt_idx]
                photos = apartment.get('image', [])
                if photo_idx < len(photos) and photos[photo_idx] == photo_url:
                    # Удаляем фото из массива
                    photos.pop(photo_idx)
                    apartment['image'] = photos
                    
                    # Обновляем документ в базе
                    unified_col.update_one(
                        {'_id': ObjectId(unified_id)},
                        {'$set': {f'apartment_types.{room_type}.apartments.{apt_idx}': apartment}}
                    )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_development_photo(request):
    """API: Удалить фото ЖК из unified_houses"""
    try:
        data = json.loads(request.body)
        unified_id = data.get('unified_id')
        photo_idx = data.get('photo_idx')
        photo_url = data.get('photo_url')
        
        if not all([unified_id, photo_idx is not None, photo_url]):
            return JsonResponse({
                'success': False,
                'error': 'Не все параметры указаны'
            }, status=400)
        
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем документ
        doc = unified_col.find_one({'_id': ObjectId(unified_id)})
        if not doc:
            return JsonResponse({'success': False, 'error': 'Запись не найдена'}, status=404)
        
        # Удаляем файл из S3
        try:
            s3_key = s3_client.extract_key_from_url(photo_url)
            if s3_key:
                s3_client.delete_object(s3_key)
        except Exception as e:
            pass  # Игнорируем ошибки удаления файла
        
        # Удаляем фото из development.photos
        development = doc.get('development', {})
        photos = development.get('photos', [])
        if photo_idx < len(photos) and photos[photo_idx] == photo_url:
            # Удаляем фото из массива
            photos.pop(photo_idx)
            
            # Обновляем документ в базе
            unified_col.update_one(
                {'_id': ObjectId(unified_id)},
                {'$set': {'development.photos': photos}}
            )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_construction_photo(request):
    """API: Удалить фото хода строительства из unified_houses"""
    try:
        data = json.loads(request.body)
        unified_id = data.get('unified_id')
        stage_idx = data.get('stage_idx')
        photo_idx = data.get('photo_idx')
        photo_url = data.get('photo_url')
        
        if not all([unified_id, stage_idx is not None, photo_idx is not None, photo_url]):
            return JsonResponse({
                'success': False,
                'error': 'Не все параметры указаны'
            }, status=400)
        
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем документ
        doc = unified_col.find_one({'_id': ObjectId(unified_id)})
        if not doc:
            return JsonResponse({'success': False, 'error': 'Запись не найдена'}, status=404)
        
        # Удаляем файл из S3
        try:
            s3_key = s3_client.extract_key_from_url(photo_url)
            if s3_key:
                s3_client.delete_object(s3_key)
        except Exception as e:
            pass  # Игнорируем ошибки удаления файла
        
        # Удаляем фото из construction_progress
        construction_progress = doc.get('construction_progress', [])
        
        # Проверяем разные структуры данных
        if isinstance(construction_progress, list):
            # Старая структура: массив объектов с photos
            if stage_idx < len(construction_progress):
                stage = construction_progress[stage_idx]
                photos = stage.get('photos', [])
                if photo_idx < len(photos) and photos[photo_idx] == photo_url:
                    photos.pop(photo_idx)
                    stage['photos'] = photos
                    
                    # Обновляем документ в базе
                    unified_col.update_one(
                        {'_id': ObjectId(unified_id)},
                        {'$set': {f'construction_progress.{stage_idx}': stage}}
                    )
        else:
            # Новая структура: объект с construction_stages
            construction_stages = construction_progress.get('construction_stages', [])
            if stage_idx < len(construction_stages):
                stage = construction_stages[stage_idx]
                photos = stage.get('photos', [])
                if photo_idx < len(photos) and photos[photo_idx] == photo_url:
                    photos.pop(photo_idx)
                    stage['photos'] = photos
                    
                    # Обновляем документ в базе
                    unified_col.update_one(
                        {'_id': ObjectId(unified_id)},
                        {'$set': {f'construction_progress.construction_stages.{stage_idx}': stage}}
                    )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_client_catalog_apartments(request):
    """API: Получить квартиры для клиентского каталога по выбранным ЖК"""
    try:
        # Получаем параметры из URL
        complexes_param = request.GET.get('complexes', '').strip()
        apartments_param = request.GET.get('apartments', '').strip()
        
        if not complexes_param:
            return JsonResponse({
                'success': False,
                'error': 'Не указаны ЖК'
            }, status=400)
        
        # Парсим ID ЖК
        try:
            complex_ids = [ObjectId(cid.strip()) for cid in complexes_param.split(',') if cid.strip()]
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Неверный формат ID ЖК: {str(e)}'
            }, status=400)
        
        # Парсим ID квартир (если указаны)
        apartment_ids = []
        if apartments_param:
            try:
                apartment_ids = [aid.strip() for aid in apartments_param.split(',') if aid.strip()]
            except Exception:
                apartment_ids = []
        
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем ЖК
        complexes = list(unified_col.find({'_id': {'$in': complex_ids}}))
        
        # Проверяем, что все ЖК найдены
        if len(complexes) != len(complex_ids):
            found_ids = {str(c['_id']) for c in complexes}
            missing_ids = [str(cid) for cid in complex_ids if str(cid) not in found_ids]
            if missing_ids:
                return JsonResponse({
                    'success': False,
                    'error': f'Не найдены ЖК с ID: {", ".join(missing_ids)}'
                }, status=404)
        
        # Собираем все квартиры из выбранных ЖК
        all_apartments = []
        
        for complex_data in complexes:
            complex_id = str(complex_data['_id'])
            
            # Определяем название и адрес ЖК
            complex_name = ''
            complex_address = ''
            
            # Проверяем структуру данных
            is_new_structure = 'apartment_types' in complex_data or ('development' in complex_data and 'avito' not in complex_data)
            
            if is_new_structure:
                # Новая структура
                development = complex_data.get('development', {})
                complex_name = complex_data.get('name', '') or development.get('name', '')
                if not complex_name:
                    city = complex_data.get('city', '') or development.get('city', '')
                    street = complex_data.get('street', '') or development.get('street', '')
                    if city and street:
                        complex_name = f"ЖК на {street}, {city}"
                    elif city:
                        complex_name = f"ЖК в {city}"
                    else:
                        complex_name = "Жилой комплекс"
                
                complex_address = complex_data.get('address', '') or complex_data.get('street', '') or development.get('address', '')
                city = complex_data.get('city', '') or development.get('city', '')
                if city:
                    if complex_address:
                        complex_address = f"{complex_address}, {city}"
                    else:
                        complex_address = city
                
                # Проверяем наличие apartment_types или development.apartments
                apartment_types_data = complex_data.get('apartment_types', {})
                if not apartment_types_data and development.get('apartments'):
                    # Если есть development.apartments, преобразуем в формат apartment_types
                    apartments_list = development.get('apartments', [])
                    apartment_types_data = {'all': {'apartments': apartments_list}}
            else:
                # Старая структура
                avito_data = complex_data.get('avito', {})
                domclick_data = complex_data.get('domclick', {})
                
                avito_dev = avito_data.get('development', {}) if avito_data else {}
                domclick_dev = domclick_data.get('development', {}) if domclick_data else {}
                
                complex_name = avito_dev.get('name') or domclick_dev.get('complex_name', 'Без названия')
                complex_address = avito_dev.get('address', '').split('/')[0].strip() if avito_dev.get('address') else ''
                if not complex_address:
                    complex_address = domclick_dev.get('address', '')
                
                apartment_types_data = avito_data.get('apartment_types', {})
            
            # Извлекаем квартиры
            # Группируем квартиры по типам для правильной генерации ID (как в get_complexes_with_apartments)
            apartments_by_type = {}  # {apt_type: [apartments]}
            for apt_type, apt_data in apartment_types_data.items():
                apartments_by_type[apt_type] = apt_data.get('apartments', [])
            
            for apt_type, apartments in apartments_by_type.items():
                for apt_index, apt in enumerate(apartments):
                    # Генерируем ID квартиры (должно совпадать с get_complexes_with_apartments)
                    apt_id = apt.get('_id')
                    if not apt_id:
                        # Используем индекс внутри типа (как в get_complexes_with_apartments)
                        apt_id = f"{complex_id}_{apt_type}_{apt_index}"
                    else:
                        apt_id = str(apt_id)
                    
                    # Если указаны конкретные квартиры, фильтруем
                    if apartment_ids:
                        # Проверяем точное совпадение
                        apt_id_normalized = apt_id.strip()
                        apartment_ids_normalized = [aid.strip() for aid in apartment_ids]
                        if apt_id_normalized not in apartment_ids_normalized:
                            continue
                    
                    # Получаем фото планировки
                    layout_photos = apt.get('image', [])
                    if isinstance(layout_photos, str):
                        layout_photos = [layout_photos] if layout_photos else []
                    
                    # Извлекаем данные
                    title = apt.get('title', '')
                    rooms = apt.get('rooms', '')
                    floor = apt.get('floor', '')
                    area = apt.get('area') or apt.get('totalArea', '')
                    price = apt.get('price', '')
                    price_per_sqm = apt.get('pricePerSquare', '') or apt.get('pricePerSqm', '')
                    
                    # Парсим из title если нет в отдельных полях
                    if title:
                        import re
                        if not rooms:
                            if '-комн' in title:
                                rooms = title.split('-комн')[0].strip()
                            elif '-к.' in title:
                                rooms = title.split('-к.')[0].strip()
                            elif ' ком.' in title:
                                rooms = title.split(' ком.')[0].strip()
                        
                        if not floor:
                            floor_range_match = re.search(r'(\d+)-(\d+)\s*этаж', title)
                            if floor_range_match:
                                floor = f"{floor_range_match.group(1)}-{floor_range_match.group(2)}"
                            else:
                                floor_match = re.search(r'(\d+)/(\d+)\s*эт', title)
                                if floor_match:
                                    floor = f"{floor_match.group(1)}/{floor_match.group(2)}"
                        
                        if not area:
                            area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                            if area_match:
                                area = area_match.group(1).replace(',', '.')
                    
                    all_apartments.append({
                        'id': apt_id,
                        'complex_id': complex_id,
                        'complex_name': complex_name,
                        'complex_address': complex_address,
                        'type': apt_type,
                        'title': title,
                        'rooms': rooms,
                        'area': area,
                        'floor': floor,
                        'price': price,
                        'price_per_sqm': price_per_sqm,
                        'image': layout_photos[0] if layout_photos else '',
                        'images': layout_photos,
                        'url': apt.get('url', ''),
                        'completion_date': apt.get('completionDate', ''),
                    })
        
        # Группируем по ЖК для отладки
        apartments_by_complex = {}
        for apt in all_apartments:
            complex_id = apt['complex_id']
            if complex_id not in apartments_by_complex:
                apartments_by_complex[complex_id] = []
            apartments_by_complex[complex_id].append(apt)
        
        return JsonResponse({
            'success': True,
            'apartments': all_apartments,
            'total': len(all_apartments),
            'debug': {
                'requested_complexes': len(complex_ids),
                'found_complexes': len(complexes),
                'apartments_by_complex': {k: len(v) for k, v in apartments_by_complex.items()},
                'filtered_by_apartments': len(apartment_ids) > 0 if apartment_ids else False
            }
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_apartment_selection(request):
    """API: Создать подборку квартир"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        complexes = data.get('complexes', [])  # [{complex_id, apartment_ids: []}]
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Название подборки обязательно'
            }, status=400)
        
        if not complexes or len(complexes) == 0:
            return JsonResponse({
                'success': False,
                'error': 'Выберите хотя бы один ЖК'
            }, status=400)
        
        db = get_mongo_connection()
        selections_col = db['apartment_selections']
        
        # Создаем подборку
        selection = {
            'name': name,
            'complexes': complexes,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = selections_col.insert_one(selection)
        
        return JsonResponse({
            'success': True,
            'selection_id': str(result.inserted_id)
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@require_http_methods(["GET"])
def get_apartment_selections(request):
    """API: Получить список всех подборок"""
    try:
        db = get_mongo_connection()
        selections_col = db['apartment_selections']
        
        selections = list(selections_col.find({}).sort('created_at', -1))
        
        result = []
        for sel in selections:
            # Подсчитываем количество квартир
            total_apartments = 0
            for comp in sel.get('complexes', []):
                total_apartments += len(comp.get('apartment_ids', []))
            
            result.append({
                'id': str(sel['_id']),
                'name': sel.get('name', 'Без названия'),
                'complexes_count': len(sel.get('complexes', [])),
                'apartments_count': total_apartments,
                'created_at': sel.get('created_at', datetime.now()).isoformat() if isinstance(sel.get('created_at'), datetime) else str(sel.get('created_at', '')),
                'updated_at': sel.get('updated_at', datetime.now()).isoformat() if isinstance(sel.get('updated_at'), datetime) else str(sel.get('updated_at', ''))
            })
        
        return JsonResponse({
            'success': True,
            'selections': result
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@require_http_methods(["GET"])
def get_apartment_selection(request, selection_id):
    """API: Получить подборку по ID"""
    try:
        db = get_mongo_connection()
        selections_col = db['apartment_selections']
        
        selection = selections_col.find_one({'_id': ObjectId(selection_id)})
        
        if not selection:
            return JsonResponse({
                'success': False,
                'error': 'Подборка не найдена'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'selection': {
                'id': str(selection['_id']),
                'name': selection.get('name', ''),
                'complexes': selection.get('complexes', [])
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_apartment_selection(request, selection_id):
    """API: Обновить подборку"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        complexes = data.get('complexes', [])
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Название подборки обязательно'
            }, status=400)
        
        db = get_mongo_connection()
        selections_col = db['apartment_selections']
        
        update_data = {
            'name': name,
            'complexes': complexes,
            'updated_at': datetime.now()
        }
        
        selections_col.update_one(
            {'_id': ObjectId(selection_id)},
            {'$set': update_data}
        )
        
        return JsonResponse({
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_apartment_selection(request, selection_id):
    """API: Удалить подборку"""
    try:
        db = get_mongo_connection()
        selections_col = db['apartment_selections']
        
        result = selections_col.delete_one({'_id': ObjectId(selection_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({
                'success': False,
                'error': 'Подборка не найдена'
            }, status=404)
        
        return JsonResponse({
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_complex_by_id(request, complex_id):
    """API: Получить данные ЖК по ID для страницы избранного"""
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        complex_data = unified_col.find_one({'_id': ObjectId(complex_id)})
        
        if not complex_data:
            return JsonResponse({
                'success': False,
                'error': 'ЖК не найден'
            }, status=404)
        
        # Определяем название и адрес ЖК
        complex_name = ''
        complex_address = ''
        photos = []
        
        is_new_structure = 'apartment_types' in complex_data or ('development' in complex_data and 'avito' not in complex_data)
        
        if is_new_structure:
            development = complex_data.get('development', {})
            complex_name = complex_data.get('name', '') or development.get('name', '')
            if not complex_name:
                city = complex_data.get('city', '') or development.get('city', '')
                street = complex_data.get('street', '') or development.get('street', '')
                if city and street:
                    complex_name = f"ЖК на {street}, {city}"
                elif city:
                    complex_name = f"ЖК в {city}"
                else:
                    complex_name = "Жилой комплекс"
            
            complex_address = complex_data.get('address', '') or complex_data.get('street', '') or development.get('address', '')
            city = complex_data.get('city', '') or development.get('city', '')
            if city:
                if complex_address:
                    complex_address = f"{complex_address}, {city}"
                else:
                    complex_address = city
            
            photos = complex_data.get('photos', []) or development.get('photos', [])
        else:
            avito_data = complex_data.get('avito', {})
            domclick_data = complex_data.get('domclick', {})
            avito_dev = avito_data.get('development', {}) if avito_data else {}
            domclick_dev = domclick_data.get('development', {}) if domclick_data else {}
            complex_name = avito_dev.get('name') or domclick_dev.get('complex_name', 'Без названия')
            complex_address = avito_dev.get('address', '') or domclick_dev.get('address', '')
            photos = avito_dev.get('photos', []) or domclick_dev.get('photos', [])
        
        return JsonResponse({
            'success': True,
            'id': str(complex_data['_id']),
            'name': complex_name,
            'address': complex_address,
            'photos': photos,
            'apartment_types': complex_data.get('apartment_types', {})
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@require_http_methods(["GET"])
def get_complexes_with_apartments(request):
    """API: Получить все ЖК с их квартирами, сгруппированными по категориям"""
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses']
        
        # Получаем все ЖК
        complexes = list(unified_col.find({}))
        
        result = []
        
        for complex_data in complexes:
            complex_id = str(complex_data['_id'])
            
            # Определяем название ЖК
            complex_name = ''
            is_new_structure = 'apartment_types' in complex_data or ('development' in complex_data and 'avito' not in complex_data)
            
            if is_new_structure:
                development = complex_data.get('development', {})
                complex_name = complex_data.get('name', '') or development.get('name', '')
                if not complex_name:
                    city = complex_data.get('city', '') or development.get('city', '')
                    street = complex_data.get('street', '') or development.get('street', '')
                    if city and street:
                        complex_name = f"ЖК на {street}, {city}"
                    elif city:
                        complex_name = f"ЖК в {city}"
                    else:
                        complex_name = "Жилой комплекс"
            else:
                avito_data = complex_data.get('avito', {})
                domclick_data = complex_data.get('domclick', {})
                avito_dev = avito_data.get('development', {}) if avito_data else {}
                domclick_dev = domclick_data.get('development', {}) if domclick_data else {}
                complex_name = avito_dev.get('name') or domclick_dev.get('complex_name', 'Без названия')
            
            # Группируем квартиры по категориям (количество комнат)
            categories = {}  # {rooms: [apartments]}
            
            apartment_types_data = {}
            if is_new_structure:
                apartment_types_data = complex_data.get('apartment_types', {})
                development = complex_data.get('development', {})
                if not apartment_types_data and development.get('apartments'):
                    apartments_list = development.get('apartments', [])
                    apartment_types_data = {'all': {'apartments': apartments_list}}
            else:
                apartment_types_data = complex_data.get('avito', {}).get('apartment_types', {})
            
            for apt_type, apt_data in apartment_types_data.items():
                apartments = apt_data.get('apartments', [])
                
                # Используем enumerate для правильной генерации ID
                for apt_index, apt in enumerate(apartments):
                    # Определяем количество комнат
                    rooms = apt.get('rooms', '')
                    title = apt.get('title', '')
                    
                    if not rooms and title:
                        if '-комн' in title:
                            rooms = title.split('-комн')[0].strip()
                        elif '-к.' in title:
                            rooms = title.split('-к.')[0].strip()
                        elif ' ком.' in title:
                            rooms = title.split(' ком.')[0].strip()
                    
                    # Нормализуем значение комнат
                    if not rooms:
                        rooms = 'Студия'
                    elif rooms.isdigit():
                        rooms = f"{rooms}-комн"
                    else:
                        rooms = str(rooms)
                    
                    if rooms not in categories:
                        categories[rooms] = []
                    
                    # Генерируем ID квартиры (должно совпадать с get_client_catalog_apartments)
                    apt_id = apt.get('_id')
                    if not apt_id:
                        # Используем индекс внутри типа (как в get_client_catalog_apartments)
                        apt_id = f"{complex_id}_{apt_type}_{apt_index}"
                    else:
                        apt_id = str(apt_id)
                    
                    # Извлекаем данные
                    area = apt.get('area') or apt.get('totalArea', '')
                    floor = apt.get('floor', '')
                    
                    # Извлекаем цену квартиры (общая цена, не цена за м²)
                    price = apt.get('price', '')
                    
                    # Если цена не найдена, пытаемся извлечь из title
                    if not price and title:
                        import re
                        # Ищем цену в формате "8 240 000 ₽" или "8240000" или "8.24 млн"
                        price_match = re.search(r'(\d+[\s,.]?\d*[\s,.]?\d*)\s*(?:₽|руб|млн|млн\.)', title)
                        if price_match:
                            price_str = price_match.group(1).replace(' ', '').replace(',', '')
                            try:
                                if 'млн' in title.lower():
                                    price_num = float(price_str) * 1000000
                                else:
                                    price_num = float(price_str)
                                price = price_num
                            except:
                                pass
                    
                    # Форматируем цену
                    if price:
                        if isinstance(price, (int, float)) and price > 0:
                            price = f"{price:,.0f} ₽".replace(',', ' ')
                        elif isinstance(price, str) and price.strip():
                            # Если это строка с числом, форматируем
                            price_clean = price.replace(' ', '').replace('₽', '').replace('руб', '').replace(',', '').replace('.', '').strip()
                            if price_clean.isdigit():
                                try:
                                    price_num = float(price.replace(' ', '').replace('₽', '').replace('руб', '').replace(',', '.').strip())
                                    if price_num > 0:
                                        price = f"{price_num:,.0f} ₽".replace(',', ' ')
                                    else:
                                        price = ''
                                except:
                                    price = ''
                            elif not price.strip():
                                price = ''
                    else:
                        price = ''
                    
                    categories[rooms].append({
                        'id': apt_id,
                        'title': title or f"{rooms} квартира",
                        'area': area,
                        'floor': floor,
                        'price': price
                    })
            
            if categories:
                result.append({
                    'id': complex_id,
                    'name': complex_name,
                    'categories': categories
                })
        
        return JsonResponse({
            'success': True,
            'complexes': result
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


