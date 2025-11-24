"""
API функции для бронирования квартир
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime
import json

from ..services.mongo_service import get_mongo_connection


@csrf_exempt
@require_http_methods(["POST"])
def book_apartment(request):
    """Забронировать квартиру"""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        
        # Получаем данные из запроса
        apartment_id = payload.get('apartment_id')
        complex_id = payload.get('complex_id')
        client_name = (payload.get('client_name') or '').strip()
        client_phone = (payload.get('client_phone') or '').strip()
        
        # Валидация
        if not apartment_id or not complex_id:
            return JsonResponse({
                'success': False, 
                'error': 'ID квартиры и ЖК обязательны'
            })
        
        if not client_name:
            return JsonResponse({
                'success': False, 
                'error': 'Имя клиента обязательно'
            })
        
        if not client_phone:
            return JsonResponse({
                'success': False, 
                'error': 'Телефон клиента обязателен'
            })
        
        # Валидация телефона (простая проверка)
        phone_digits = ''.join(filter(str.isdigit, client_phone))
        if len(phone_digits) < 10:
            return JsonResponse({
                'success': False, 
                'error': 'Некорректный номер телефона'
            })
        
        db = get_mongo_connection()
        
        # Получаем информацию о ЖК
        complex_collection = db['unified_houses']
        complex_data = complex_collection.find_one({'_id': ObjectId(complex_id)})
        
        if not complex_data:
            return JsonResponse({
                'success': False, 
                'error': 'ЖК не найден'
            })
        
        # Отладочная информация о структуре данных
        # print(f"Ключи в complex_data: {list(complex_data.keys())}")
        # print(f"Есть development: {'development' in complex_data}")
        # print(f"Есть apartment_types: {'apartment_types' in complex_data}")
        # print(f"Есть avito: {'avito' in complex_data}")
        
        # Получаем информацию о квартире
        apartment_data = None
        complex_name = ''
        
        # Определяем название ЖК и данные квартиры в зависимости от структуры
        if 'apartment_types' in complex_data:
            # Новая структура с apartment_types (используем ту же логику, что и в apartment_views.py)
            complex_name = complex_data.get('name', '')
            if not complex_name:
                city = complex_data.get('city', '')
                street = complex_data.get('street', '')
                complex_name = f"ЖК на {street}, {city}" if street else f"ЖК в {city}"
            
            # Собираем все квартиры из apartment_types
            apartments = []
            apartment_types_data = complex_data.get('apartment_types', {})
            
            # print(f"Найдено типов квартир: {len(apartment_types_data)}")
            
            for apt_type, apt_data in apartment_types_data.items():
                apt_apartments = apt_data.get('apartments', [])
                # print(f"Тип {apt_type}: {len(apt_apartments)} квартир")
                
                # Используем enumerate для правильной генерации ID (как в apartment_views.py)
                for apt_index, apt in enumerate(apt_apartments):
                    # Генерируем уникальный ID если его нет (формат: {complex_id}_{apt_type}_{apt_index})
                    apt_id = apt.get('_id')
                    if not apt_id:
                        apt_id = f"{complex_id}_{apt_type}_{apt_index}"
                    
                    apt['id'] = str(apt_id)
                    apt['type'] = apt_type
                    apartments.append(apt)
        elif 'development' in complex_data and 'avito' not in complex_data:
            complex_name = complex_data.get('development', {}).get('name', 'Неизвестный ЖК')
            apartments = complex_data.get('development', {}).get('apartments', [])
        else:
            # Для структуры с avito/domclick
            avito_data = complex_data.get('avito', {})
            domclick_data = complex_data.get('domclick', {})
            
            if avito_data and avito_data.get('development'):
                complex_name = avito_data['development'].get('name', 'Неизвестный ЖК')
                apartments = avito_data.get('apartments', [])
            elif domclick_data and domclick_data.get('development'):
                complex_name = domclick_data['development'].get('complex_name', 'Неизвестный ЖК')
                apartments = domclick_data.get('apartments', [])
            else:
                complex_name = 'Неизвестный ЖК'
                apartments = []
        
        # Ищем конкретную квартиру
        apartment_data = None
        
        # print(f"Поиск квартиры с ID: {apartment_id}")
        # print(f"Всего квартир найдено: {len(apartments)}")
        
        # Преобразуем apartment_id в строку для безопасной проверки
        apartment_id_str = str(apartment_id) if apartment_id is not None else ''
        
        # Если apartment_id содержит подчеркивание, это сгенерированный ID
        if '_' in apartment_id_str:
            # Проверяем формат ID: может быть {complex_id}_{type}_{index} или {type}_{index}
            apt_id_parts = apartment_id_str.split('_')
            
            # Если ID начинается с complex_id (24 символа), убираем его
            if len(apt_id_parts) >= 3 and len(apt_id_parts[0]) == 24:
                # Формат: {complex_id}_{type}_{index}
                # Проверяем, что первый элемент совпадает с complex_id
                if apt_id_parts[0] == str(complex_id):
                    apt_type = apt_id_parts[1]
                    try:
                        apartment_index = int(apt_id_parts[2])
                    except (ValueError, IndexError):
                        apt_type = None
                        apartment_index = None
                else:
                    # Не совпадает с complex_id, пробуем как {type}_{index}
                    apt_type = apt_id_parts[0]
                    try:
                        apartment_index = int(apt_id_parts[1])
                    except (ValueError, IndexError):
                        apt_type = None
                        apartment_index = None
            else:
                # Формат: {type}_{index}
                try:
                    apt_type = apt_id_parts[0]
                    apartment_index = int(apt_id_parts[1])
                except (ValueError, IndexError):
                    apt_type = None
                    apartment_index = None
            
            # Ищем квартиру по типу и индексу
            if apt_type is not None and apartment_index is not None:
                current_index = 0
                for apt in apartments:
                    if apt.get('type') == apt_type:
                        if current_index == apartment_index:
                            apartment_data = apt
                            break
                        current_index += 1
        else:
            # Обычный поиск по _id или id
            for apt in apartments:
                if str(apt.get('id')) == apartment_id_str or str(apt.get('_id')) == apartment_id_str:
                    apartment_data = apt
                    break
        
        if not apartment_data:
            return JsonResponse({
                'success': False, 
                'error': 'Квартира не найдена'
            })
        
        # Получаем информацию об агенте
        agent_data = None
        agent_name = 'Будет назначен'
        
        # Ищем агента в данных ЖК
        if complex_data.get('agent_id'):
            agents_collection = db['employees']
            agent_data = agents_collection.find_one({'_id': ObjectId(complex_data['agent_id'])})
            if agent_data:
                agent_name = agent_data.get('full_name', 'Будет назначен')
        
        # Парсим данные из title (используем ту же логику, что и в apartment_views.py)
        title = apartment_data.get('title', '')
        rooms = ''
        area = ''
        floor = ''
        
        if title:
            # Извлекаем количество комнат
            if '-к.' in title:
                rooms = title.split('-к.')[0].strip()
            
            # Извлекаем площадь
            import re
            area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
            if area_match:
                area = area_match.group(1).replace(',', '.')
            
            # Извлекаем этаж
            floor_match = re.search(r'(\d+)/(\d+)\s*эт', title)
            if floor_match:
                floor = f"{floor_match.group(1)}/{floor_match.group(2)}"
        
        # Создаем запись бронирования
        booking_data = {
            'apartment_id': apartment_id,  # Сохраняем как строку, так как это сгенерированный ID
            'complex_id': ObjectId(complex_id),
            'complex_name': complex_name,
            'client_name': client_name,
            'client_phone': client_phone,
            'apartment_details': {
                'rooms': rooms,
                'area': area,
                'floor': floor,
                'price': apartment_data.get('price', ''),
                'url': apartment_data.get('url', ''),
            },
            'agent_name': agent_name,
            'agent_id': complex_data.get('agent_id'),
            'status': 'pending',  # pending, contacted, booked, cancelled
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'notes': '',
            'contacted_at': None,
            'booked_at': None,
            'cancelled_at': None
        }
        
        # Сохраняем в коллекцию бронирований
        bookings_collection = db['apartment_bookings']
        result = bookings_collection.insert_one(booking_data)
        
        if result.inserted_id:
            return JsonResponse({
                'success': True,
                'message': 'Бронирование успешно создано. Ожидайте звонка в течение 10 минут.',
                'booking_id': str(result.inserted_id)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Не удалось создать бронирование'
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["GET"])
def get_booking_stats(request):
    """Получить статистику бронирований (для админов)"""
    try:
        db = get_mongo_connection()
        bookings_collection = db['apartment_bookings']
        
        total_bookings = bookings_collection.count_documents({})
        pending_bookings = bookings_collection.count_documents({'status': 'pending'})
        contacted_bookings = bookings_collection.count_documents({'status': 'contacted'})
        booked_bookings = bookings_collection.count_documents({'status': 'booked'})
        cancelled_bookings = bookings_collection.count_documents({'status': 'cancelled'})
        
        # Получаем последние бронирования
        recent_bookings = list(bookings_collection.find().sort('created_at', -1).limit(10))
        
        formatted_recent = []
        for booking in recent_bookings:
            formatted_recent.append({
                '_id': str(booking['_id']),
                'client_name': booking.get('client_name', ''),
                'client_phone': booking.get('client_phone', ''),
                'complex_name': booking.get('complex_name', ''),
                'apartment_details': booking.get('apartment_details', {}),
                'status': booking.get('status', 'pending'),
                'created_at': booking.get('created_at', ''),
                'agent_name': booking.get('agent_name', '')
            })
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_bookings': total_bookings,
                'pending_bookings': pending_bookings,
                'contacted_bookings': contacted_bookings,
                'booked_bookings': booked_bookings,
                'cancelled_bookings': cancelled_bookings
            },
            'recent_bookings': formatted_recent
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_booking_status(request, booking_id):
    """Обновить статус бронирования (для админов)"""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        new_status = payload.get('status')
        
        if not new_status or new_status not in ['pending', 'contacted', 'booked', 'cancelled']:
            return JsonResponse({
                'success': False, 
                'error': 'Некорректный статус'
            }, status=400)
        
        db = get_mongo_connection()
        bookings_collection = db['apartment_bookings']
        
        update_data = {
            'status': new_status,
            'updated_at': datetime.utcnow()
        }
        
        # Добавляем специфичные поля для статусов
        if new_status == 'contacted':
            update_data['contacted_at'] = datetime.utcnow()
        elif new_status == 'booked':
            update_data['booked_at'] = datetime.utcnow()
        elif new_status == 'cancelled':
            update_data['cancelled_at'] = datetime.utcnow()
        
        result = bookings_collection.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return JsonResponse({
                'success': True,
                'message': f'Статус бронирования обновлен на {new_status}'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Бронирование не найдено'
            }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
