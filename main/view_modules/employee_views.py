"""Views для сотрудников и команды"""
from django.shortcuts import render, redirect
from django.http import Http404
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime
from bson import ObjectId
from ..services.mongo_service import get_mongo_connection
from ..utils import get_video_thumbnail, extract_price_from_range
from ..s3_service import PLACEHOLDER_IMAGE_URL


def team(request):
    """Страница команды - читает из MongoDB"""
    db = get_mongo_connection()
    employees = list(db['employees'].find({'is_active': True}).sort('full_name', 1))
    # Преобразуем ObjectId в строку и кладем в поле id для шаблона
    for emp in employees:
        try:
            emp['id'] = str(emp.get('_id'))
        except Exception:
            emp['id'] = ''

    context = {
        'employees': employees,
        'PLACEHOLDER_IMAGE_URL': PLACEHOLDER_IMAGE_URL,
    }
    return render(request, 'main/team.html', context)


def agent_properties(request, employee_id):
    """Страница объектов агента - читает из MongoDB"""
    db = get_mongo_connection()
    
    try:
        employee = db['employees'].find_one({'_id': ObjectId(employee_id), 'is_active': True})
    except:
        employee = db['employees'].find_one({'is_active': True})
    
    if not employee:
        raise Http404("Сотрудник не найден")

    # Получаем параметры фильтрации и сортировки
    property_type = request.GET.get('property_type', '')
    sort_by = request.GET.get('sort_by', 'date-desc')

    # Получаем все объекты агента из MongoDB
    residential_complexes = []
    secondary_properties = []
    
    try:
        # Новостройки: unified_houses по agent_id
        rc_cursor = db['unified_houses'].find({'agent_id': ObjectId(employee_id)})
        for d in rc_cursor:
            development = d.get('development', {}) or {}
            item = {
                'id': str(d.get('_id')),
                'name': development.get('name') or d.get('name',''),
                'photo': '',
                'price': extract_price_from_range(development.get('price_range', '')) or d.get('price', 0),
                'city': development.get('address', '') or d.get('city', ''),
                'district': d.get('district', ''),
                'created_at': d.get('created_at', datetime.now())
            }
            # Фото из development.photos
            photos = development.get('photos') or d.get('photos') or []
            if isinstance(photos, list) and photos:
                item['photo'] = photos[0]
            residential_complexes.append(item)
    except Exception:
        residential_complexes = []
    
    try:
        # Вторичка: secondary_properties по agent_id
        sp_cursor = db['secondary_properties'].find({'agent_id': ObjectId(employee_id)})
        for d in sp_cursor:
            secondary_properties.append({
                'id': str(d.get('_id')),
                'name': d.get('name',''),
                'city': d.get('city',''),
                'district': d.get('district',''),
                'photo': (d.get('photos') or [''])[0] if (d.get('photos') or []) else '',
                'price': d.get('price', 0),
                'created_at': d.get('created_at', datetime.now())
            })
    except Exception:
        secondary_properties = []

    # Фильтрация по типу недвижимости
    if property_type == 'residential':
        secondary_properties = []
    elif property_type == 'secondary':
        residential_complexes = []

    # Объединяем все объекты
    all_properties = []

    # Добавляем новостройки
    for complex in residential_complexes:
        all_properties.append({
            'type': 'residential',
            'object': complex,
            'name': complex['name'],
            'price': complex.get('price', 0),
            'location': f"{complex.get('district', '') or complex.get('city', '')}",
            'image': complex.get('photo', ''),
            'url': f"/complex/{complex['id']}/",
            'created_at': complex.get('created_at', datetime.now()),
        })

    # Добавляем вторичную недвижимость
    for property in secondary_properties:
        all_properties.append({
            'type': 'secondary',
            'object': property,
            'name': property['name'],
            'price': property.get('price', 0),
            'location': f"{property.get('district', '') or property.get('city', '')}",
            'image': property.get('photo', ''),
            'url': f"/secondary/{property['id']}/",
            'created_at': property.get('created_at', datetime.now()),
        })

    # Применяем сортировку
    if sort_by == 'date-desc':
        all_properties.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == 'date-asc':
        all_properties.sort(key=lambda x: x['created_at'])
    elif sort_by == 'price-asc':
        all_properties.sort(key=lambda x: float(x['price']))
    elif sort_by == 'price-desc':
        all_properties.sort(key=lambda x: float(x['price']), reverse=True)
    elif sort_by == 'name-asc':
        all_properties.sort(key=lambda x: x['name'].lower())

    # Пагинация по 9 элементов
    paginator = Paginator(all_properties, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Добавляем id для шаблона
    employee['id'] = str(employee.get('_id'))
    
    # Считаем общее количество объектов
    total_residential_count = len([p for p in all_properties if p['type'] == 'residential'])
    total_secondary_count = len([p for p in all_properties if p['type'] == 'secondary'])
    
    context = {
        'employee': employee,
        'properties': page_obj,
        'page_obj': page_obj,
        'total_count': len(all_properties),
        'residential_count': total_residential_count,
        'secondary_count': total_secondary_count,
        'current_property_type': property_type,
        'current_sort': sort_by,
    }
    return render(request, 'main/agent_properties.html', context)


def employee_detail(request, employee_id):
    """Детальная страница сотрудника - читает из MongoDB"""
    db = get_mongo_connection()
    
    try:
        employee = db['employees'].find_one({'_id': ObjectId(employee_id), 'is_active': True})
    except:
        raise Http404("Сотрудник не найден")
    
    if not employee:
        raise Http404("Сотрудник не найден")

    # Получаем объекты агента из MongoDB (ограничиваем до 4 примеров)
    residential_complexes = []
    secondary_properties = []
    try:
        # Новостройки: unified_houses по agent_id (максимум 4)
        rc_cursor = db['unified_houses'].find({'agent_id': ObjectId(employee_id)}).limit(4)
        for d in rc_cursor:
            development = d.get('development', {}) or {}
            item = {
                'id': str(d.get('_id')),
                'name': development.get('name') or d.get('name',''),
                'photo': ''
            }
            # Фото из development.photos
            photos = development.get('photos') or d.get('photos') or []
            if isinstance(photos, list) and photos:
                item['photo'] = photos[0]
            residential_complexes.append(item)
    except Exception:
        residential_complexes = []
    try:
        # Вторичка: secondary_properties по agent_id (максимум 4)
        sp_cursor = db['secondary_properties'].find({'agent_id': ObjectId(employee_id)}).limit(4)
        for d in sp_cursor:
            secondary_properties.append({
                'id': str(d.get('_id')),
                'name': d.get('name',''),
                'city': d.get('city',''),
                'district': d.get('district',''),
                'photo': (d.get('photos') or [''])[0] if (d.get('photos') or []) else ''
            })
    except Exception:
        secondary_properties = []

    # Считаем общее количество объектов (реальное количество для кнопки)
    total_residential_count = 0
    total_secondary_count = 0
    try:
        total_residential_count = db['unified_houses'].count_documents({'agent_id': ObjectId(employee_id)})
    except Exception:
        pass
    try:
        total_secondary_count = db['secondary_properties'].count_documents({'agent_id': ObjectId(employee_id)})
    except Exception:
        pass
    
    total_properties_count = total_residential_count + total_secondary_count

    # Получаем опубликованные отзывы из MongoDB
    try:
        reviews_cursor = db['employee_reviews'].find({
            'employee_id': ObjectId(employee_id),
            'is_published': True
        }).sort('created_at', -1)
        reviews = list(reviews_cursor)
    except Exception:
        reviews = []

    # Обработка формы отзыва
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        rating = request.POST.get('rating', 5)
        text = request.POST.get('text', '').strip()

        if name and text and rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    # Создаем отзыв в MongoDB
                    review_data = {
                        'employee_id': ObjectId(employee_id),
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'rating': rating,
                        'text': text,
                        'is_published': False,  # На модерации
                        'created_at': datetime.now(),
                    }
                    db['employee_reviews'].insert_one(review_data)
                    messages.success(request, 'Спасибо! Ваш отзыв отправлен на модерацию.')
                    return redirect('main:employee_detail', employee_id=str(employee.get('_id')))
            except ValueError:
                pass

        messages.error(request, 'Пожалуйста, заполните все обязательные поля корректно.')

    # Добавляем id для шаблона
    employee['id'] = str(employee.get('_id'))
    
    # Обработка видео для отображения
    videos_with_thumbnails = []
    if employee.get('videos'):
        for video_url in employee.get('videos', []):
            if video_url.strip():
                videos_with_thumbnails.append({
                    'url': video_url.strip(),
                    'thumbnail': get_video_thumbnail(video_url.strip())
                })
    
    context = {
        'employee': employee,
        'residential_complexes': residential_complexes,
        'secondary_properties': secondary_properties,
        'reviews': reviews,
        'total_properties_count': total_properties_count,
        'videos': videos_with_thumbnails,
        'PLACEHOLDER_IMAGE_URL': PLACEHOLDER_IMAGE_URL,
    }
    return render(request, 'main/employee_detail.html', context)

