"""
API функции для ручного сопоставления записей из разных источников (DomRF, Avito, DomClick)
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime
import json

from ..services.mongo_service import get_mongo_connection
from ..s3_service import s3_client
from .subscription_api import notify_new_future_project


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
        domrf_filter = {'is_processed': {'$ne': True}}  # Исключаем обработанные записи
        avito_filter = {}
        domclick_filter = {}
        
        if search:
            domrf_filter['objCommercNm'] = {'$regex': search, '$options': 'i'}
            avito_filter['development.name'] = {'$regex': search, '$options': 'i'}
            domclick_filter['development.complex_name'] = {'$regex': search, '$options': 'i'}
        
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
                'objId': r.get('objId')  # Добавляем objId для формирования ссылки на дом.рф
            }
            for r in domrf_records 
            if r.get('objCommercNm') not in matched_domrf_names
        ][:per_page]
        
        avito_records = list(avito_col.find(avito_filter).limit(100))
        avito_unmatched = [
            {
                '_id': str(r['_id']),
                'name': r.get('development', {}).get('name', 'Без названия'),
                'url': r.get('url', ''),
                'address': r.get('development', {}).get('address', ''),
                'development': r.get('development', {}),  # Передаем всю структуру development
                'location': r.get('location', {})  # И location тоже для совместимости
            }
            for r in avito_records 
            if r['_id'] not in matched_avito_ids
        ][:per_page]
        
        domclick_records = list(domclick_col.find(domclick_filter).limit(100))
        domclick_unmatched = [
            {
                '_id': str(r['_id']),
                'name': r.get('development', {}).get('complex_name', 'Без названия'),
                'url': r.get('url', ''),
                'address': r.get('development', {}).get('address', ''),
                'development': r.get('development', {}),  # Передаем всю структуру development
                'location': r.get('location', {})  # И location тоже для совместимости
            }
            for r in domclick_records 
            if r['_id'] not in matched_domclick_ids
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
                'total_domrf': total_domrf - len(matched_domrf_names),
                'total_avito': total_avito - len(matched_avito_ids),
                'total_domclick': total_domclick - len(matched_domclick_ids)
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
            latitude = float(provided_latitude)
            longitude = float(provided_longitude)
        elif domrf_record:
            latitude = domrf_record.get('latitude')
            longitude = domrf_record.get('longitude')
        elif avito_record:
            # Пытаемся взять координаты из Avito
            latitude = avito_record.get('latitude')
            longitude = avito_record.get('longitude')
        elif domclick_record:
            # Пытаемся взять координаты из DomClick
            latitude = domclick_record.get('latitude')
            longitude = domclick_record.get('longitude')
        
        # Если координат нет ни в одном источнике - требуем ввести вручную
        if not latitude or not longitude:
            return JsonResponse({
                'success': False,
                'error': 'Необходимо ввести координаты',
                'error_type': 'missing_coordinates'
            }, status=400)
        
        unified_record = {
            'latitude': latitude,
            'longitude': longitude,
            'source': 'manual',
            'created_by': 'manual',
            'is_featured': is_featured,  # Флаг "показывать на главной"
            # Добавляем поля для адреса
            'city': 'Уфа',  # По умолчанию
            'district': '',
            'street': '',
            # Поля рейтинга
            'rating': None,  # Рейтинг от 1 до 5
            'rating_description': '',  # Описание причины низкого рейтинга
            'rating_created_at': None,  # Дата создания рейтинга
            'rating_updated_at': None   # Дата обновления рейтинга
        }
        
        # Привязка агента
        if agent_id:
            try:
                unified_record['agent_id'] = ObjectId(agent_id)
            except Exception:
                unified_record['agent_id'] = None
        
        # Пытаемся извлечь город/район/улицу из адреса Avito или DomClick
        address = ''
        if avito_record:
            address = avito_record.get('development', {}).get('address', '')
        elif domclick_record:
            address = domclick_record.get('development', {}).get('address', '')
        
        # Простое извлечение города (можно улучшить)
        if 'Уфа' in address or 'уфа' in address.lower():
            unified_record['city'] = 'Уфа'
        
        # 2. Development из Avito + photos из DomClick
        if avito_record:
            avito_dev = avito_record.get('development', {})
            unified_record['development'] = {
                'name': avito_dev.get('name', ''),
                'address': avito_dev.get('address', ''),
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
                
                # Ищем соответствующий тип в Avito
                avito_apartments = []
                for avito_type_name, avito_data in avito_apt_types.items():
                    avito_simplified = name_mapping.get(avito_type_name, avito_type_name)
                    if avito_simplified == simplified_name:
                        avito_apartments = avito_data.get('apartments', [])
                        break
                
                # ИЗМЕНЕНО: Добавляем тип только если есть данные в Avito
                if not avito_apartments:
                    continue  # Пропускаем тип, если нет данных в Avito
                
                # Объединяем: количество квартир = количество квартир в DomClick
                combined_apartments = []
                
                for i, dc_apt in enumerate(dc_apartments):
                    # Получаем ВСЕ фото этой квартиры из DomClick как МАССИВ
                    apartment_photos = dc_apt.get('photos', [])
                    
                    # Если фото нет - пропускаем эту квартиру
                    if not apartment_photos:
                        continue
                    
                    # Берем соответствующую квартиру из Avito (циклически)
                    avito_apt = avito_apartments[i % len(avito_apartments)]
                    
                    combined_apartments.append({
                        'title': avito_apt.get('title', ''),
                        'price': avito_apt.get('price', ''),
                        'pricePerSquare': avito_apt.get('pricePerSquare', ''),
                        'completionDate': avito_apt.get('completionDate', ''),
                        'url': avito_apt.get('urlPath', ''),
                        'image': apartment_photos  # МАССИВ всех фото этой планировки!
                    })
                
                # Добавляем в результат только если есть квартиры с фото И данными из Avito
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


