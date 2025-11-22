"""
API функции для обработки заявок из чат-бота
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
import re

from ..services.mongo_service import get_mongo_connection


@csrf_exempt
@require_http_methods(["POST"])
def submit_chat_request(request):
    """Обработка заявки из чат-бота"""
    try:
        # Получаем данные из запроса
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            return JsonResponse({
                'success': False,
                'error': 'Некорректный формат запроса'
            }, status=400)

        request_type = data.get('type')  # 'sell', 'buy', 'question'
        phone = data.get('phone', '').strip()
        property_type = data.get('propertyType')  # 'apartment', 'house'
        rooms = data.get('rooms')  # 'studio', '1', '2', '3', '4+'
        question = data.get('question', '').strip()

        # Валидация
        if not phone:
            return JsonResponse({
                'success': False,
                'error': 'Телефон обязателен для заполнения'
            }, status=400)

        if request_type not in ['sell', 'buy', 'question']:
            return JsonResponse({
                'success': False,
                'error': 'Некорректный тип заявки'
            }, status=400)

        if request_type == 'question' and not question:
            return JsonResponse({
                'success': False,
                'error': 'Вопрос обязателен для заполнения'
            }, status=400)

        # Нормализация телефона
        phone_digits = re.sub(r'[^\d+]', '', phone)
        if phone_digits.startswith('+7'):
            phone_normalized = phone_digits
        elif phone_digits.startswith('8'):
            phone_normalized = '+7' + phone_digits[1:]
        elif phone_digits.startswith('7'):
            phone_normalized = '+' + phone_digits
        else:
            phone_normalized = '+7' + phone_digits

        # Проверка формата телефона
        if not re.match(r'^\+7\d{10}$', phone_normalized):
            return JsonResponse({
                'success': False,
                'error': 'Некорректный формат телефона'
            }, status=400)

        # Формируем описание заявки
        description_parts = []
        
        if request_type == 'sell':
            description_parts.append('Хочет продать')
            if property_type == 'apartment':
                description_parts.append('квартиру')
                if rooms:
                    rooms_text = {
                        'studio': 'Студию',
                        '1': '1-комнатную',
                        '2': '2-комнатную',
                        '3': '3-комнатную',
                        '4+': '4+ комнатную'
                    }.get(rooms, rooms)
                    description_parts.append(rooms_text)
            elif property_type == 'house':
                description_parts.append('дом')
        
        elif request_type == 'buy':
            description_parts.append('Хочет купить')
            if property_type == 'apartment':
                description_parts.append('квартиру')
                if rooms:
                    rooms_text = {
                        'studio': 'Студию',
                        '1': '1-комнатную',
                        '2': '2-комнатную',
                        '3': '3-комнатную',
                        '4+': '4+ комнатную'
                    }.get(rooms, rooms)
                    description_parts.append(rooms_text)
            elif property_type == 'house':
                description_parts.append('дом')
        
        elif request_type == 'question':
            description_parts.append('Задал вопрос')
            if question:
                # Обрезаем вопрос, если слишком длинный
                question_short = question[:200] + '...' if len(question) > 200 else question
                description_parts.append(f': {question_short}')

        description = ' '.join(description_parts)

        # Подключаемся к MongoDB
        db = get_mongo_connection()
        chat_requests_collection = db['chat_requests']

        # Формируем документ для сохранения
        chat_doc = {
            'type': request_type,
            'phone': phone_normalized,
            'phone_display': phone,
            'property_type': property_type,
            'rooms': rooms,
            'question': question if request_type == 'question' else None,
            'description': description,
            'status': 'new',  # new, contacted, closed
            'source': 'chat_bot',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'contacted_at': None,
            'notes': ''
        }

        # Сохраняем в MongoDB
        result = chat_requests_collection.insert_one(chat_doc)
        request_id = str(result.inserted_id)

        return JsonResponse({
            'success': True,
            'message': 'Спасибо за вашу заявку! Мы свяжемся с вами в ближайшее время.',
            'request_id': request_id
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Ошибка обработки данных'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Произошла ошибка: {str(e)}'
        }, status=500)

