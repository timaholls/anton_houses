"""
API функции для расширенного управления вторичной недвижимостью
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from bson import ObjectId
from datetime import datetime
import json
import os

from ..services.mongo_service import get_mongo_connection
from ..s3_service import s3_client


@require_http_methods(["GET"])
def secondary_list(request):
    """Список объектов вторичной недвижимости из Mongo."""
    try:
        db = get_mongo_connection()
        col = db['secondary_properties']
        docs = list(col.find({}).sort('created_at', -1))
        items = []
        for d in docs:
            items.append({
                '_id': str(d.get('_id')),
                'name': d.get('name',''),
                'price': d.get('price'),
                'city': d.get('city','Уфа'),
                'district': d.get('district',''),
                'street': d.get('street',''),
                'commute_time': d.get('commute_time',''),
                'house_type': d.get('house_type','apartment'),
                'area': d.get('area'),
                'rooms': d.get('rooms'),
                'description': d.get('description',''),
                'agent_id': str(d.get('agent_id')) if d.get('agent_id') else None,
                'photos': d.get('photos', [])
            })
        return JsonResponse({'success': True, 'data': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def secondary_create(request):
    """Создать объект вторички в Mongo c загрузкой фото в media/secondary_complexes/<slug>/."""
    try:
        # multipart/form-data: данные + файлы
        name = (request.POST.get('name') or '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Укажите название'}, status=400)

        # simple slug-like transliteration
        safe_slug = slugify(name) or f"secondary-{int(datetime.utcnow().timestamp())}"

        city = request.POST.get('city') or 'Уфа'
        district = request.POST.get('district') or ''
        street = request.POST.get('street') or ''
        commute_time = request.POST.get('commute_time') or ''
        house_type = request.POST.get('house_type') or 'apartment'
        area = request.POST.get('area')
        rooms = request.POST.get('rooms')
        price = request.POST.get('price')
        total_floors = request.POST.get('total_floors')
        finishing = request.POST.get('finishing') or ''
        description = request.POST.get('description') or ''

        # загрузка файлов в S3
        files = request.FILES.getlist('photos')
        saved_paths = []
        for f in files:
            filename = slugify(os.path.splitext(f.name)[0]) or 'photo'
            ext = os.path.splitext(f.name)[1].lower()
            final_name = f"{filename}-{int(datetime.utcnow().timestamp()*1000)}{ext}"
            s3_key = f"secondary_complexes/{safe_slug}/{final_name}"
            # Определяем тип контента
            content_type = f.content_type if hasattr(f, 'content_type') else 'image/jpeg'
            s3_url = s3_client.upload_fileobj(f, s3_key, content_type)
            saved_paths.append(s3_url)

        db = get_mongo_connection()
        col = db['secondary_properties']
        doc = {
            'name': name,
            'slug': safe_slug,  # Добавляем slug для удаления папки
            'price': float(price) if price else None,
            'city': city,
            'district': district,
            'street': street,
            'commute_time': commute_time,
            'house_type': house_type,
            'area': float(area) if area else None,
            'rooms': rooms,
            'total_floors': int(total_floors) if total_floors else None,
            'finishing': finishing,
            'description': description,
            'photos': saved_paths,
            'is_active': True,  # По умолчанию активна
            'created_at': datetime.utcnow()
        }
        inserted = col.insert_one(doc)
        return JsonResponse({'success': True, 'id': str(inserted.inserted_id), 'photos': saved_paths})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def secondary_api_toggle(request, secondary_id):
    """API: переключить статус объекта вторичной недвижимости (активен/неактивен)."""
    try:
        data = json.loads(request.body or '{}')
        is_active = data.get('is_active', True)
        
        db = get_mongo_connection()
        col = db['secondary_properties']
        result = col.update_one(
            {'_id': ObjectId(secondary_id)},
            {'$set': {'is_active': is_active}}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'Объект не найден'}, status=404)
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"]) 
def secondary_api_get(request, secondary_id: str):
    """API: получить объект вторички."""
    try:
        db = get_mongo_connection()
        col = db['secondary_properties']
        doc = col.find_one({'_id': ObjectId(secondary_id)})
        if not doc:
            return JsonResponse({'success': False, 'error': 'Объект не найден'}, status=404)
        doc['_id'] = str(doc['_id'])
        return JsonResponse({'success': True, 'item': doc})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"]) 
def secondary_api_update(request, secondary_id: str):
    """API: обновить произвольные поля вторички; фото и сложные операции будут отдельно."""
    try:
        db = get_mongo_connection()
        col = db['secondary_properties']
        payload = {}
        if request.content_type and 'application/json' in request.content_type:
            payload = json.loads(request.body or '{}')
        else:
            payload = {k: v for k, v in request.POST.items()}

        payload.pop('_id', None)
        # Преобразование типов
        for key in ('rooms', 'total_floors'):
            if key in payload and str(payload[key]).strip() != '':
                try: payload[key] = int(payload[key])
                except Exception: payload.pop(key, None)
        for key in ('area', 'area_from', 'area_to'):
            if key in payload and str(payload[key]).strip() != '':
                try: payload[key] = float(payload[key])
                except Exception: payload.pop(key, None)
        for key in ('price', 'price_from', 'price_to'):
            if key in payload and str(payload[key]).strip() != '':
                try: payload[key] = int(payload[key])
                except Exception: payload.pop(key, None)
        if 'is_active' in payload:
            payload['is_active'] = True if str(payload['is_active']).lower() in ('1','true','on') else False

        if not payload:
            return JsonResponse({'success': False, 'error': 'Нет полей для обновления'}, status=400)

        col.update_one({'_id': ObjectId(secondary_id)}, {'$set': payload})
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def secondary_api_delete(request, secondary_id):
    """API: удалить объект вторичной недвижимости и все его фотографии."""
    try:
        db = get_mongo_connection()
        col = db['secondary_properties']
        
        # Сначала получаем документ чтобы узнать пути к файлам
        doc = col.find_one({'_id': ObjectId(secondary_id)})
        if not doc:
            return JsonResponse({'success': False, 'error': 'Объект не найден'}, status=404)
        
        # Удаляем файлы фотографий
        # Удаляем фотографии из S3
        photos = doc.get('photos', [])
        for photo_url in photos:
            if photo_url:
                try:
                    s3_key = s3_client.extract_key_from_url(photo_url)
                    if s3_key:
                        s3_client.delete_object(s3_key)
                except:
                    pass  # Игнорируем ошибки удаления файлов
        
        # Удаляем документ из базы
        result = col.delete_one({'_id': ObjectId(secondary_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'Объект не найден'}, status=404)
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
