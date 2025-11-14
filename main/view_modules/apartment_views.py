"""
Views для детальной страницы квартиры
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from bson import ObjectId
from datetime import datetime

from ..services.mongo_service import get_mongo_connection
from ..s3_service import PLACEHOLDER_IMAGE_URL


def apartment_detail(request, complex_id, apartment_id):
    """Детальная страница квартиры"""
    try:
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
            # Формируем название ЖК из доступных данных
            complex_name = complex_data.get('name', '')
            if not complex_name:
                city = complex_data.get('city', '')
                street = complex_data.get('street', '')
                if city and street:
                    complex_name = f"ЖК на {street}, {city}"
                elif city:
                    complex_name = f"ЖК в {city}"
                else:
                    complex_name = "Жилой комплекс"
            complex_images = complex_data.get('photos', [])
            
            # Формируем квартиры из apartment_types (используем ту же логику, что и в catalog_views.py)
            for apt_type, apt_data in apartment_types_data.items():
                apt_apartments = apt_data.get('apartments', [])
                
                for apt in apt_apartments:
                    # Получаем все фото планировки - это уже массив!
                    layout_photos = apt.get('image', [])
                    
                    # Если это не массив, а строка - преобразуем в массив
                    if isinstance(layout_photos, str):
                        layout_photos = [layout_photos] if layout_photos else []
                    
                    # Генерируем уникальный ID если его нет
                    apt_id = apt.get('_id')
                    if not apt_id:
                        apt_id = f"{apt_type}_{len(apartments)}"
                    
                    apartments.append({
                        'id': str(apt_id),  # Добавляем ID квартиры
                        'type': apt_type,
                        'title': apt.get('title', ''),
                        'price': apt.get('price', ''),
                        'price_per_square': apt.get('pricePerSquare', ''),
                        'completion_date': apt.get('completionDate', ''),
                        'image': layout_photos[0] if layout_photos else '',  # Первое фото для превью
                        'url': apt.get('url', ''),
                        'layout_photos': layout_photos,  # Все фото для галереи
                        '_id': apt.get('_id'),  # Сохраняем оригинальный _id
                        'rooms': apt.get('rooms', ''),
                        'totalArea': apt.get('totalArea', ''),
                        'floor': apt.get('floor', ''),
                        'pricePerSqm': apt.get('pricePerSqm', ''),
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
        if '_' in apartment_id:
            # Разбираем сгенерированный ID: {type}_{index}
            try:
                apt_type, index_str = apartment_id.split('_', 1)
                apartment_index = int(index_str)
                
                # Ищем квартиру по типу и индексу
                current_index = 0
                for apt in apartments:
                    if apt.get('type') == apt_type:
                        if current_index == apartment_index:
                            apartment_data = apt
                            break
                        current_index += 1
            except (ValueError, IndexError):
                pass
        else:
            # Обычный поиск по _id
            for apt in apartments:
                if str(apt.get('_id')) == str(apartment_id):
                    apartment_data = apt
                    break
        
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
            if str(apt.get('id')) != str(apartment_id):
                # Формируем данные для других квартир
                other_apt_title = apt.get('title', '')
                other_rooms = ''
                other_area = ''
                
                if other_apt_title:
                    # Извлекаем количество комнат
                    if '-к.' in other_apt_title:
                        other_rooms = other_apt_title.split('-к.')[0].strip()
                    
                    # Извлекаем площадь
                    import re
                    area_match = re.search(r'(\d+[,.]?\d*)\s*м²', other_apt_title)
                    if area_match:
                        other_area = area_match.group(1).replace(',', '.')
                
                other_apt_data = {
                    'id': apt.get('id'),
                    'rooms': other_rooms,
                    'area': other_area,
                    'price': apt.get('price', ''),
                    'photos': apt.get('image', []),
                    'title': other_apt_title
                }
                
                # Исправляем фотографии если это строка
                if isinstance(other_apt_data['photos'], str):
                    other_apt_data['photos'] = [other_apt_data['photos']]
                
                other_apartments.append(other_apt_data)
        
        # Парсим данные из title (например: "2-к. квартира, 63,9 м², 3/15 эт.)
        # ВАЖНО: Сначала проверяем поле area/totalArea, потом парсим из title
        title = apartment_data.get('title', '')
        rooms = ''
        area = ''
        floor = ''
        
        # Сначала пытаемся взять площадь из отдельного поля (из DomClick)
        area = apartment_data.get('area') or apartment_data.get('totalArea') or ''
        if area:
            # Преобразуем в строку, если это число
            if isinstance(area, (int, float)):
                area = str(area)
        
        if title:
            # Извлекаем количество комнат
            if '-к.' in title:
                rooms = title.split('-к.')[0].strip()
            
            # Извлекаем площадь из title только если не нашли в отдельном поле
            if not area:
                import re
                area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
                if area_match:
                    area = area_match.group(1).replace(',', '.')
            
            # Извлекаем этаж
            floor_match = re.search(r'(\d+)/(\d+)\s*эт', title)
            if floor_match:
                floor = f"{floor_match.group(1)}/{floor_match.group(2)}"
        
        # Форматируем данные квартиры
        apartment_info = {
            'id': apartment_id,  # Используем сгенерированный ID
            'rooms': rooms,
            'area': area,
            'floor': floor,
            'price': apartment_data.get('price', ''),
            'price_per_sqm': apartment_data.get('pricePerSquare', ''),
            'completion_date': apartment_data.get('completionDate', ''),
            'url': apartment_data.get('url', ''),
            'layout': '',  # Не доступно в данных
            'balcony': '',  # Не доступно в данных
            'loggia': '',  # Не доступно в данных
            'view': '',  # Не доступно в данных
            'condition': '',  # Не доступно в данных
            'furniture': '',  # Не доступно в данных
            'ceiling_height': '',  # Не доступно в данных
            'windows': '',  # Не доступно в данных
            'bathroom': '',  # Не доступно в данных
            'kitchen_area': '',  # Не доступно в данных
            'living_area': '',  # Не доступно в данных
            'bedroom_area': '',  # Не доступно в данных
            'photos': apartment_data.get('image', []),  # Используем поле image
            'description': '',  # Не доступно в данных
            'features': [],  # Не доступно в данных
        }
        
        # Отладочная информация для фотографий
        photos = apartment_data.get('image', [])
        if isinstance(photos, str):
            photos = [photos]  # Если это строка, делаем массив
        # print(f"Фотографии квартиры: {photos}")
        # print(f"Количество фотографий: {len(photos)}")
        
        # Обновляем photos в apartment_info
        apartment_info['photos'] = photos
        
        context = {
            'complex': {
                'id': str(complex_data.get('_id')),
                'name': complex_name,
                'images': complex_images,
                'district': complex_data.get('district', ''),
                'city': complex_data.get('city', ''),
                'street': complex_data.get('street', ''),
            },
            'apartment': apartment_info,
            'agent': agent_data,
            'other_apartments': other_apartments,
            'PLACEHOLDER_IMAGE_URL': PLACEHOLDER_IMAGE_URL,
        }
        
        return render(request, 'main/apartment_detail.html', context)
        
    except Exception as e:
        print(f"Ошибка загрузки квартиры: {e}")
        raise Http404("Ошибка загрузки данных квартиры")
