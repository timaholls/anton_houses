"""
API функции для обработки формы обратной связи с отслеживанием активности пользователя
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
def submit_feedback(request):
    """Обработка формы обратной связи с сохранением истории активности пользователя"""
    try:
        # Получаем данные из запроса
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            # Fallback для form-data
            data = {
                'name': request.POST.get('name', '').strip(),
                'phone': request.POST.get('phone', '').strip(),
                'user_activity': request.POST.get('user_activity', '{}')
            }
            try:
                data['user_activity'] = json.loads(data['user_activity'])
            except:
                data['user_activity'] = {}

        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        user_activity = data.get('user_activity', {})

        # Валидация
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Имя обязательно для заполнения'
            }, status=400)

        if not phone:
            return JsonResponse({
                'success': False,
                'error': 'Телефон обязателен для заполнения'
            }, status=400)

        # Нормализация телефона (убираем все нецифровые символы кроме +)
        phone_digits = re.sub(r'[^\d+]', '', phone)
        if phone_digits.startswith('+7'):
            phone_normalized = phone_digits
        elif phone_digits.startswith('8'):
            phone_normalized = '+7' + phone_digits[1:]
        elif phone_digits.startswith('7'):
            phone_normalized = '+' + phone_digits
        else:
            phone_normalized = '+7' + phone_digits

        # Проверка формата телефона (должно быть +7 и 10 цифр)
        if not re.match(r'^\+7\d{10}$', phone_normalized):
            return JsonResponse({
                'success': False,
                'error': 'Некорректный формат телефона'
            }, status=400)

        # Получаем историю действий
        actions = user_activity.get('actions', [])
        visited_pages = user_activity.get('visitedPages', [])
        activity_summary = user_activity.get('summary', '')

        # Если summary не передан, формируем его из действий
        if not activity_summary:
            activity_summary = generate_summary_from_actions(actions) if actions else 'Просматривал сайт'

        # Подключаемся к MongoDB
        db = get_mongo_connection()
        feedback_collection = db['feedback_requests']

        # Формируем документ для сохранения
        feedback_doc = {
            'name': name,
            'phone': phone_normalized,
            'phone_display': phone,  # Сохраняем оригинальный формат для отображения
            'user_activity': {
                'actions': actions,
                'visited_pages': visited_pages,
                'summary': activity_summary,
                'start_time': user_activity.get('startTime'),
                'total_actions': len(actions)
            },
            'status': 'new',  # new, contacted, closed
            'source': 'feedback_form',  # feedback_form, booking, vacancy_form
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'contacted_at': None,
            'notes': ''
        }

        # Сохраняем в MongoDB
        result = feedback_collection.insert_one(feedback_doc)
        feedback_id = str(result.inserted_id)

        return JsonResponse({
            'success': True,
            'message': 'Спасибо! Мы свяжемся с вами в ближайшее время.',
            'feedback_id': feedback_id
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


def generate_summary_from_actions(actions):
    """Генерирует текстовое описание активности из списка действий"""
    if not actions:
        return 'Просматривал сайт'

    parts = []
    page_types = set()
    complexes = []
    apartments = []
    mortgage_programs = []
    filters_info = []

    for action in actions:
        action_type = action.get('type', '')

        if action_type == 'view_page':
            page_type = action.get('page_type', '')
            if page_type == 'mortgage':
                page_types.add('ипотеку')
            elif page_type == 'catalog':
                page_types.add('каталог')
            elif page_type == 'future_complexes' or page_type == 'future_complex_detail':
                page_types.add('новостройки')
            elif page_type == 'complex_detail':
                page_types.add('новостройки')
                # Пытаемся получить название ЖК
                complex_name = action.get('data', {}).get('complex_name')
                if complex_name and complex_name not in complexes:
                    complexes.append(complex_name)

        elif action_type == 'view_complex':
            complex_name = action.get('complex_name')
            if complex_name and complex_name not in complexes:
                complexes.append(complex_name)

        elif action_type == 'view_apartment':
            complex_name = action.get('complex_name')
            if complex_name and complex_name not in complexes:
                complexes.append(complex_name)
            
            rooms = action.get('rooms')
            if rooms:
                room_text = get_room_text(rooms)
                if room_text and room_text not in apartments:
                    apartments.append(room_text)

        elif action_type == 'view_mortgage_program':
            program_name = action.get('program_name')
            if program_name and program_name not in mortgage_programs:
                mortgage_programs.append(program_name)

        elif action_type == 'filter_catalog':
            filters = action.get('filters', {})
            if filters.get('rooms'):
                rooms = filters['rooms']
                room_text = get_room_text(rooms, plural=True)
                if room_text and not any(f['text'] == room_text for f in filters_info):
                    filters_info.append({'type': 'rooms', 'text': room_text})

    # Формируем итоговый текст
    summary_parts = []

    if page_types:
        pages_list = ', '.join(sorted(page_types))
        summary_parts.append(f'Интересовался {pages_list}')

    if mortgage_programs:
        summary_parts.append(f'смотрел ипотечную программу "{mortgage_programs[0]}"')

    if complexes:
        summary_parts.append(f'просматривал ЖК "{complexes[0]}"')

    if apartments:
        summary_parts.append(f'смотрел {", ".join(apartments)} квартиры')
    elif filters_info:
        rooms_filter = next((f for f in filters_info if f['type'] == 'rooms'), None)
        if rooms_filter:
            summary_parts.append(f'смотрел {rooms_filter["text"]} квартиры')

    return ', '.join(summary_parts) if summary_parts else 'Просматривал сайт'


def get_room_text(rooms, plural=False):
    """Преобразует количество комнат в текст"""
    if rooms == 1:
        return 'однокомнатные' if plural else 'однокомнатную'
    elif rooms == 2:
        return 'двухкомнатные' if plural else 'двухкомнатную'
    elif rooms == 3:
        return 'трехкомнатные' if plural else 'трехкомнатную'
    elif rooms == 4:
        return 'четырехкомнатные' if plural else 'четырехкомнатную'
    else:
        return f'{rooms}-комнатные' if plural else f'{rooms}-комнатную'

