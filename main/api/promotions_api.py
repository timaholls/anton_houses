"""
API функции для управления акциями и спецпредложениями
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime
import json

from ..services.mongo_service import get_mongo_connection
from .subscription_api import notify_new_promotion


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
        
        # Отправляем уведомления подписчикам
        try:
            notify_new_promotion(doc)
        except Exception as e:
            print(f"Ошибка отправки уведомлений о новой акции: {e}")
        
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
@require_http_methods(["POST", "PATCH"]) 
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
