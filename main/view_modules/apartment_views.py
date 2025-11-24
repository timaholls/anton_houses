"""
Views для детальной страницы квартиры
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from bson import ObjectId
from datetime import datetime
import re
import json

from ..services.mongo_service import get_mongo_connection
from ..s3_service import PLACEHOLDER_IMAGE_URL


def format_price(price):
    """Форматирует цену: убирает лишние ₽, форматирует число с пробелами, добавляет один ₽"""
    if not price:
        return ''
    
    # Преобразуем в строку
    price_str = str(price).strip()
    
    # Убираем все символы ₽
    price_str = price_str.replace('₽', '').replace('руб', '').replace('руб.', '').strip()
    
    # Убираем пробелы и запятые для парсинга
    price_clean = price_str.replace(' ', '').replace(',', '').replace('.', '').strip()
    
    # Проверяем, является ли это числом
    if not price_clean.isdigit():
        return price_str  # Возвращаем как есть, если не число
    
    try:
        # Преобразуем в число
        price_num = float(price_str.replace(' ', '').replace(',', '.').strip())
        
        if price_num <= 0:
            return ''
        
        # Форматируем с разделителями тысяч
        formatted = f"{price_num:,.0f}".replace(',', ' ')
        
        # Добавляем ₽
        return f"{formatted} ₽"
    except (ValueError, TypeError):
        return price_str


def apartment_detail(request, complex_id, apartment_id):
    """Детальная страница квартиры"""
    try:
        # Преобразуем apartment_id в строку сразу в начале функции для безопасной работы
        # Важно: Django передает параметры URL как строки, но на всякий случай преобразуем
        if apartment_id is None:
            apartment_id_str = ''
        else:
            apartment_id_str = str(apartment_id)
        
        db = get_mongo_connection()
        
        # Получаем данные ЖК
        complex_collection = db['unified_houses']
        complex_data = complex_collection.find_one({'_id': ObjectId(complex_id)})
        
        if not complex_data:
            raise Http404("ЖК не найден")
        
        # Определяем структуру данных и получаем информацию о ЖК
        complex_name = ''
        complex_images = []
        apartments = []
        agent_data = None
        
        # Используем ту же логику формирования квартир, что и в catalog_views.py
        apartments = []
        complex_name = ''
        complex_images = []
        
        # Проверяем, есть ли поле apartment_types
        if 'apartment_types' in complex_data:
            apartment_types_data = complex_data.get('apartment_types', {})
            # Формируем название ЖК из доступных данных (проверяем все возможные места)
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
            complex_images = complex_data.get('photos', []) or development.get('photos', [])
            
            # Формируем квартиры из apartment_types (используем ту же логику, что и в catalog_views.py)
            for apt_type, apt_data in apartment_types_data.items():
                apt_apartments = apt_data.get('apartments', [])
                
                # Используем enumerate для правильной генерации ID (как в get_client_catalog_apartments)
                for apt_index, apt in enumerate(apt_apartments):
                    # Получаем все фото планировки - это уже массив!
                    # Проверяем разные возможные поля для фотографий
                    layout_photos = None
                    
                    # Приоритет 1: images_apartment (используется в новой структуре)
                    if 'images_apartment' in apt:
                        layout_photos = apt.get('images_apartment', [])
                    
                    # Приоритет 2: image
                    if not layout_photos:
                        layout_photos = apt.get('image', [])
                    
                    # Приоритет 3: photos
                    if not layout_photos:
                        layout_photos = apt.get('photos', [])
                    
                    # Если это не массив, а строка - преобразуем в массив
                    if isinstance(layout_photos, str):
                        layout_photos = [layout_photos] if layout_photos else []
                    elif not isinstance(layout_photos, list):
                        layout_photos = [] if layout_photos is None else []
                    
                    # Если все еще пусто, пробуем layout, plan, photo, layout_image
                    if not layout_photos:
                        for field in ['layout', 'plan', 'photo', 'layout_image']:
                            photo = apt.get(field)
                            if photo:
                                layout_photos = [photo] if isinstance(photo, str) else (photo if isinstance(photo, list) else [])
                                break
                    
                    # Генерируем уникальный ID если его нет (формат: {complex_id}_{apt_type}_{apt_index})
                    apt_id = apt.get('_id')
                    if not apt_id:
                        apt_id = f"{complex_id}_{apt_type}_{apt_index}"
                    else:
                        apt_id = str(apt_id)
                    
                    # Парсим данные из title, если их нет в отдельных полях
                    title = apt.get('title', '')
                    rooms = apt.get('rooms', '')
                    floor = apt.get('floor', '')
                    
                    if title and not rooms:
                        # Извлекаем количество комнат из title
                        if '-комн' in title:
                            rooms = title.split('-комн')[0].strip()
                        elif '-к.' in title:
                            rooms = title.split('-к.')[0].strip()
                        elif ' ком.' in title:
                            rooms = title.split(' ком.')[0].strip()
                        elif re.search(r'^(\d+)-комн', title):
                            match = re.search(r'^(\d+)-комн', title)
                            rooms = match.group(1)
                    
                    if title and not floor:
                        # Извлекаем этаж из title
                        floor_range_match = re.search(r'(\d+)-(\d+)\s*этаж', title)
                        if floor_range_match:
                            floor = f"{floor_range_match.group(1)}-{floor_range_match.group(2)}"
                        else:
                            floor_match = re.search(r'(\d+)/(\d+)\s*эт', title)
                            if floor_match:
                                floor = f"{floor_match.group(1)}/{floor_match.group(2)}"
                    
                    # Вычисляем цену за м², если она не указана
                    price = apt.get('price', '')
                    total_area = apt.get('totalArea', '') or apt.get('area', '')
                    price_per_sqm = apt.get('pricePerSqm', '') or apt.get('pricePerSquare', '')
                    
                    # Если цена за м² не указана, но есть цена и площадь, вычисляем
                    if not price_per_sqm and price and total_area:
                        try:
                            # Извлекаем числовое значение цены
                            price_str = str(price).replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').strip()
                            area_str = str(total_area).replace(',', '.').strip()
                            if price_str and area_str:
                                price_num = float(price_str)
                                area_num = float(area_str)
                                if area_num > 0:
                                    price_per_sqm = price_num / area_num
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass
                    
                    apartments.append({
                        'id': str(apt_id),  # Добавляем ID квартиры
                        'type': apt_type,
                        'title': title,
                        'price': price,
                        'price_per_square': price_per_sqm,
                        'pricePerSqm': price_per_sqm,
                        'completion_date': apt.get('completionDate', ''),
                        'image': layout_photos[0] if layout_photos else '',  # Первое фото для превью
                        'url': apt.get('url', ''),
                        'layout_photos': layout_photos,  # Все фото для галереи
                        '_id': apt.get('_id'),  # Сохраняем оригинальный _id
                        'rooms': rooms,
                        'totalArea': total_area,
                        'area': total_area,
                        'floor': floor,
                        'layout': apt.get('layout', ''),
                        'balcony': apt.get('balcony', ''),
                        'loggia': apt.get('loggia', ''),
                        'view': apt.get('view', ''),
                        'condition': apt.get('condition', ''),
                        'furniture': apt.get('furniture', ''),
                        'ceilingHeight': apt.get('ceilingHeight', ''),
                        'windows': apt.get('windows', ''),
                        'bathroom': apt.get('bathroom', ''),
                        'kitchenArea': apt.get('kitchenArea', ''),
                        'livingArea': apt.get('livingArea', ''),
                        'bedroomArea': apt.get('bedroomArea', ''),
                        'photos': apt.get('photos', []),
                        'description': apt.get('description', ''),
                        'features': apt.get('features', [])
                    })
            
        elif 'development' in complex_data and 'avito' not in complex_data:
            # Структура с development
            development = complex_data.get('development', {})
            complex_name = development.get('name', 'Неизвестный ЖК')
            complex_images = development.get('photos', [])
            apartments = development.get('apartments', [])
            print(f"Используем структуру development, квартир: {len(apartments)}")
        else:
            # Структура с avito/domclick
            avito_data = complex_data.get('avito', {})
            domclick_data = complex_data.get('domclick', {})
            
            
            if avito_data and avito_data.get('development'):
                complex_name = avito_data['development'].get('name', 'Неизвестный ЖК')
                complex_images = avito_data['development'].get('photos', [])
                apartments = avito_data.get('apartments', [])
            elif domclick_data and domclick_data.get('development'):
                complex_name = domclick_data['development'].get('complex_name', 'Неизвестный ЖК')
                complex_images = domclick_data['development'].get('photos', [])
                apartments = domclick_data.get('apartments', [])
            else:
                complex_name = 'Неизвестный ЖК'
                apartments = []
        
        # Ищем конкретную квартиру
        apartment_data = None
        apartment_index = None
        
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
                else:
                    # Не совпадает с complex_id, пробуем как {type}_{index}
                    apt_type = apt_id_parts[0]
                    try:
                        apartment_index = int(apt_id_parts[1])
                    except (ValueError, IndexError):
                        apt_type = None
            else:
                # Формат: {type}_{index}
                try:
                    apt_type = apt_id_parts[0]
                    apartment_index = int(apt_id_parts[1])
                except (ValueError, IndexError):
                    apt_type = None
            
            # Ищем квартиру по типу и индексу в сформированном списке apartments
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
                apt_id = apt.get('id') or apt.get('_id')
                if apt_id and (str(apt_id) == apartment_id_str):
                    apartment_data = apt
                    break
        
        if not apartment_data:
            # Если не нашли в сформированном списке, пробуем найти напрямую в apartment_types
            if 'apartment_types' in complex_data:
                apartment_types_data = complex_data.get('apartment_types', {})
                if '_' in apartment_id_str:
                    apt_id_parts = apartment_id_str.split('_')
                    if len(apt_id_parts) >= 2:
                        # Пробуем найти по типу и индексу напрямую в исходных данных
                        try:
                            apt_type = apt_id_parts[-2] if len(apt_id_parts) >= 2 else apt_id_parts[0]
                            apt_index = int(apt_id_parts[-1])
                            if apt_type in apartment_types_data:
                                apt_list = apartment_types_data[apt_type].get('apartments', [])
                                if apt_index < len(apt_list):
                                    apt = apt_list[apt_index]
                                    # Формируем данные квартиры так же, как при первом проходе
                                    # Проверяем разные возможные поля для фотографий
                                    layout_photos = None
                                    
                                    # Приоритет 1: images_apartment (используется в новой структуре)
                                    if 'images_apartment' in apt:
                                        layout_photos = apt.get('images_apartment', [])
                                    
                                    # Приоритет 2: image
                                    if not layout_photos:
                                        layout_photos = apt.get('image', [])
                                    
                                    # Приоритет 3: photos
                                    if not layout_photos:
                                        layout_photos = apt.get('photos', [])
                                    
                                    # Если это не массив, а строка - преобразуем в массив
                                    if isinstance(layout_photos, str):
                                        layout_photos = [layout_photos] if layout_photos else []
                                    elif not isinstance(layout_photos, list):
                                        layout_photos = [] if layout_photos is None else []
                                    
                                    # Если все еще пусто, пробуем layout, plan, photo, layout_image
                                    if not layout_photos:
                                        for field in ['layout', 'plan', 'photo', 'layout_image']:
                                            photo = apt.get(field)
                                            if photo:
                                                layout_photos = [photo] if isinstance(photo, str) else (photo if isinstance(photo, list) else [])
                                                break
                                    
                                    title = apt.get('title', '')
                                    rooms = apt.get('rooms', '')
                                    if title and not rooms:
                                        if '-комн' in title:
                                            rooms = title.split('-комн')[0].strip()
                                    
                                    floor = apt.get('floor', '')
                                    if title and not floor:
                                        floor_range_match = re.search(r'(\d+)-(\d+)\s*этаж', title)
                                        if floor_range_match:
                                            floor = f"{floor_range_match.group(1)}-{floor_range_match.group(2)}"
                                    
                                    price = apt.get('price', '')
                                    total_area = apt.get('totalArea', '') or apt.get('area', '')
                                    price_per_sqm = apt.get('pricePerSqm', '') or apt.get('pricePerSquare', '')
                                    
                                    if not price_per_sqm and price and total_area:
                                        try:
                                            price_str = str(price).replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').strip()
                                            area_str = str(total_area).replace(',', '.').strip()
                                            if price_str and area_str:
                                                price_num = float(price_str)
                                                area_num = float(area_str)
                                                if area_num > 0:
                                                    price_per_sqm = price_num / area_num
                                        except (ValueError, TypeError, ZeroDivisionError):
                                            pass
                                    
                                    apartment_data = {
                                        'id': apartment_id_str,
                                        'type': apt_type,
                                        'title': title,
                                        'price': price,
                                        'price_per_square': price_per_sqm,
                                        'pricePerSqm': price_per_sqm,
                                        'completion_date': apt.get('completionDate', ''),
                                        'image': layout_photos[0] if layout_photos else '',
                                        'url': apt.get('url', ''),
                                        'layout_photos': layout_photos,
                                        '_id': apt.get('_id'),
                                        'rooms': rooms,
                                        'totalArea': total_area,
                                        'area': total_area,
                                        'floor': floor,
                                        'layout': apt.get('layout', ''),
                                        'balcony': apt.get('balcony', ''),
                                        'loggia': apt.get('loggia', ''),
                                        'view': apt.get('view', ''),
                                        'condition': apt.get('condition', ''),
                                        'furniture': apt.get('furniture', ''),
                                        'ceilingHeight': apt.get('ceilingHeight', ''),
                                        'windows': apt.get('windows', ''),
                                        'bathroom': apt.get('bathroom', ''),
                                        'kitchenArea': apt.get('kitchenArea', ''),
                                        'livingArea': apt.get('livingArea', ''),
                                        'bedroomArea': apt.get('bedroomArea', ''),
                                        'photos': apt.get('photos', []),
                                        'description': apt.get('description', ''),
                                        'features': apt.get('features', [])
                                    }
                        except (ValueError, IndexError, KeyError):
                            pass
        
        if not apartment_data:
            raise Http404("Квартира не найдена")
        
        # Получаем информацию об агенте
        if complex_data.get('agent_id'):
            agents_collection = db['employees']
            agent_data = agents_collection.find_one({'_id': ObjectId(complex_data['agent_id'])})
            if agent_data:
                agent_data['id'] = str(agent_data.get('_id'))
        
        # Получаем другие квартиры в этом ЖК для рекомендаций
        other_apartments = []
        for apt in apartments[:6]:  # Показываем до 6 других квартир
            if str(apt.get('id')) != apartment_id_str:
                # Формируем данные для других квартир
                other_apt_title = apt.get('title', '')
                other_rooms = ''
                other_area = ''
                
                # Используем уже извлеченное количество комнат из apt, если есть
                other_rooms = apt.get('rooms', '')
                
                if other_apt_title:
                    # Извлекаем количество комнат из title, если не нашли в отдельном поле
                    if not other_rooms:
                        if '-комн' in other_apt_title:
                            other_rooms = other_apt_title.split('-комн')[0].strip()
                        elif '-к.' in other_apt_title:
                            other_rooms = other_apt_title.split('-к.')[0].strip()
                        elif ' ком.' in other_apt_title:
                            other_rooms = other_apt_title.split(' ком.')[0].strip()
                        elif re.search(r'^(\d+)-комн', other_apt_title):
                            match = re.search(r'^(\d+)-комн', other_apt_title)
                            other_rooms = match.group(1)
                    
                    # Извлекаем площадь
                    other_area = apt.get('totalArea', '') or apt.get('area', '')
                    if not other_area:
                        area_match = re.search(r'(\d+[,.]?\d*)\s*м²', other_apt_title)
                        if area_match:
                            other_area = area_match.group(1).replace(',', '.')
                    else:
                        # Преобразуем в строку, если это число
                        if isinstance(other_area, (int, float)):
                            other_area = str(other_area)
                else:
                    other_area = apt.get('totalArea', '') or apt.get('area', '')
                    if isinstance(other_area, (int, float)):
                        other_area = str(other_area)
                
                # Формируем title с количеством комнат, если его нет
                if other_apt_title and not other_rooms:
                    # Если title есть, но комнат нет, пытаемся извлечь из type
                    apt_type = apt.get('type', '')
                    if apt_type and apt_type.isdigit():
                        other_rooms = apt_type
                
                # Формируем правильный title для отображения
                display_title = other_apt_title
                # Преобразуем other_rooms в строку для безопасной проверки
                other_rooms_str = str(other_rooms) if other_rooms else ''
                if not display_title or (other_rooms_str and other_rooms_str not in display_title):
                    # Если title пустой или не содержит количество комнат, формируем новый
                    if other_rooms:
                        display_title = f"{other_rooms}-комнатная квартира"
                        if other_area:
                            display_title += f", {other_area} м²"
                    elif other_area:
                        display_title = f"Квартира, {other_area} м²"
                    else:
                        display_title = "Квартира"
                
                # Форматируем цену
                other_price_raw = apt.get('price', '')
                other_price_formatted = format_price(other_price_raw) if other_price_raw else ''
                
                other_apt_data = {
                    'id': apt.get('id'),
                    'rooms': other_rooms,
                    'area': other_area,
                    'price': other_price_formatted,
                    'photos': apt.get('image', []),
                    'title': display_title
                }
                
                # Исправляем фотографии если это строка
                if isinstance(other_apt_data['photos'], str):
                    other_apt_data['photos'] = [other_apt_data['photos']]
                
                other_apartments.append(other_apt_data)
        
        # Парсим данные из title (например: "1-комн, 30.05 м², 2-25 этаж" или "2-к. квартира, 63,9 м², 3/15 эт.)
        # ВАЖНО: Сначала проверяем поле area/totalArea, потом парсим из title
        title = apartment_data.get('title', '')
        rooms = apartment_data.get('rooms', '')  # Используем уже извлеченное значение
        area = ''
        floor = apartment_data.get('floor', '')  # Используем уже извлеченное значение
        
        # Сначала пытаемся взять площадь из отдельного поля (из DomClick)
        area = apartment_data.get('area') or apartment_data.get('totalArea') or ''
        if area:
            # Преобразуем в строку, если это число
            if isinstance(area, (int, float)):
                area = str(area)
        
        if title:
            # Извлекаем количество комнат (поддерживаем разные форматы: "1-комн", "1-к.", "1 ком.")
            if not rooms:
                # Пробуем разные варианты
                if '-комн' in title:
                    rooms = title.split('-комн')[0].strip()
                elif '-к.' in title:
                    rooms = title.split('-к.')[0].strip()
                elif ' ком.' in title:
                    rooms = title.split(' ком.')[0].strip()
                elif re.search(r'^(\d+)-комн', title):
                    match = re.search(r'^(\d+)-комн', title)
                    rooms = match.group(1)
            
            # Извлекаем площадь из title только если не нашли в отдельном поле
            if not area:
                area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                if area_match:
                    area = area_match.group(1).replace(',', '.')
            
            # Извлекаем этаж (поддерживаем форматы: "2-25 этаж", "3/15 эт.")
            if not floor:
                # Формат "2-25 этаж"
                floor_range_match = re.search(r'(\d+)-(\d+)\s*этаж', title)
                if floor_range_match:
                    floor = f"{floor_range_match.group(1)}-{floor_range_match.group(2)}"
                else:
                    # Формат "3/15 эт."
                    floor_match = re.search(r'(\d+)/(\d+)\s*эт', title)
                    if floor_match:
                        floor = f"{floor_match.group(1)}/{floor_match.group(2)}"
        
        # Форматируем данные квартиры, используя данные из apartment_data
        # Преобразуем цену за м² в число и форматируем с разделителями тысяч
        # Проверяем разные варианты имен полей (из базы и из нашего списка)
        price_per_sqm_raw = (apartment_data.get('pricePerSquare', '') or 
                             apartment_data.get('pricePerSqm', '') or
                             apartment_data.get('price_per_square', '') or
                             apartment_data.get('price_per_sqm', ''))
        
        # Если price_per_sqm не найден, но есть цена и площадь, вычисляем
        if not price_per_sqm_raw:
            price_raw = apartment_data.get('price', '')
            area_raw = apartment_data.get('area') or apartment_data.get('totalArea', '')
            if price_raw and area_raw:
                try:
                    price_str = str(price_raw).replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').strip()
                    area_str = str(area_raw).replace(',', '.').strip()
                    if price_str and area_str:
                        price_num = float(price_str)
                        area_num = float(area_str)
                        if area_num > 0:
                            price_per_sqm_raw = price_num / area_num
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
        
        price_per_sqm = None
        price_per_sqm_formatted = ''
        if price_per_sqm_raw:
            try:
                # Если это уже число, используем его напрямую
                if isinstance(price_per_sqm_raw, (int, float)):
                    price_per_sqm = float(price_per_sqm_raw)
                else:
                    # Преобразуем строку в число (убираем пробелы, заменяем запятую на точку)
                    price_per_sqm_str = str(price_per_sqm_raw).replace(',', '.').replace(' ', '').replace('₽', '').replace('руб', '').strip()
                    if price_per_sqm_str:
                        price_per_sqm = float(price_per_sqm_str)
                
                if price_per_sqm:
                    # Форматируем с разделителями тысяч
                    price_per_sqm_formatted = f"{price_per_sqm:,.0f}".replace(',', ' ')
            except (ValueError, TypeError) as e:
                price_per_sqm = None
                price_per_sqm_formatted = ''
                print(f"Ошибка форматирования price_per_sqm: {e}, значение: {price_per_sqm_raw}, тип: {type(price_per_sqm_raw)}")
        
        # Получаем срок сдачи (проверяем разные варианты имен полей)
        completion_date = (apartment_data.get('completionDate', '') or 
                          apartment_data.get('completion_date', ''))
        
        # Форматируем цену
        price_raw = apartment_data.get('price', '')
        price_formatted = format_price(price_raw) if price_raw else ''
        
        apartment_info = {
            'id': apartment_id_str,  # Используем сгенерированный ID
            'rooms': rooms,
            'area': area,
            'floor': floor,
            'price': price_formatted,
            'price_per_sqm': price_per_sqm,
            'price_per_sqm_formatted': price_per_sqm_formatted,
            'completion_date': completion_date,
            'url': apartment_data.get('url', ''),
            'layout': apartment_data.get('layout', ''),
            'balcony': apartment_data.get('balcony', ''),
            'loggia': apartment_data.get('loggia', ''),
            'view': apartment_data.get('view', ''),
            'condition': apartment_data.get('condition', ''),
            'furniture': apartment_data.get('furniture', ''),
            'ceiling_height': apartment_data.get('ceilingHeight', ''),
            'windows': apartment_data.get('windows', ''),
            'bathroom': apartment_data.get('bathroom', ''),
            'kitchen_area': apartment_data.get('kitchenArea', ''),
            'living_area': apartment_data.get('livingArea', ''),
            'bedroom_area': apartment_data.get('bedroomArea', ''),
            'photos': apartment_data.get('image', []),  # Временно, будет обновлено ниже
            'description': apartment_data.get('description', ''),
            'features': apartment_data.get('features', []),
        }
        
        # Получаем фотографии из разных возможных полей
        # Приоритет: layout_photos > image > photos
        photos = None
        
        # Сначала проверяем layout_photos (используется в сформированном списке apartments)
        layout_photos = apartment_data.get('layout_photos')
        if layout_photos:
            photos = layout_photos
        
        # Если нет layout_photos, проверяем image
        if not photos:
            image_data = apartment_data.get('image')
            if image_data:
                photos = image_data
        
        # Если нет image, проверяем photos
        if not photos:
            photos_data = apartment_data.get('photos')
            if photos_data:
                photos = photos_data
        
        # Если это строка, преобразуем в массив
        if isinstance(photos, str):
            photos = [photos] if photos else []
        # Если это не список, делаем пустым списком
        elif not isinstance(photos, list):
            photos = []
        
        # Фильтруем пустые значения
        photos = [p for p in photos if p]
        
        # Обновляем photos в apartment_info
        apartment_info['photos'] = photos
        
        # Убеждаемся, что название ЖК не пустое
        if not complex_name:
            # Пробуем получить из development для всех структур
            development = complex_data.get('development', {})
            if development:
                complex_name = development.get('name', '')
            
            # Если все еще пустое, формируем из города и улицы
            if not complex_name:
                city = complex_data.get('city', '') or development.get('city', '')
                street = complex_data.get('street', '') or development.get('street', '')
                if city and street:
                    complex_name = f"ЖК на {street}, {city}"
                elif city:
                    complex_name = f"ЖК в {city}"
                else:
                    complex_name = "Жилой комплекс"
        
        context = {
            'complex': {
                'id': str(complex_data.get('_id')),
                'name': complex_name,
                'images': complex_images,
                'district': complex_data.get('district', '') or complex_data.get('development', {}).get('district', ''),
                'city': complex_data.get('city', '') or complex_data.get('development', {}).get('city', ''),
                'street': complex_data.get('street', '') or complex_data.get('development', {}).get('street', ''),
            },
            'apartment': apartment_info,
            'agent': agent_data,
            'other_apartments': other_apartments,
            'PLACEHOLDER_IMAGE_URL': PLACEHOLDER_IMAGE_URL,
        }
        
        return render(request, 'main/apartment_detail.html', context)
        
    except Exception as e:
        import traceback
        print(f"Ошибка загрузки квартиры: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        print(f"apartment_id type: {type(apartment_id)}, value: {apartment_id}")
        raise Http404("Ошибка загрузки данных квартиры")
