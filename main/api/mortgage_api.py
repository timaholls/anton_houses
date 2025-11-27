"""
API функции для управления ипотечными программами
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime

from ..services.mongo_service import get_mongo_connection


@require_http_methods(["GET"])
def mortgage_programs_list(request):
    """API: список ипотечных программ из MongoDB."""
    try:
        db = get_mongo_connection()
        col = db['mortgage_programs']
        items = []
        for doc in col.find({}).sort('rate', 1):
            items.append({
                '_id': str(doc.get('_id')),
                'name': doc.get('name', ''),
                'rate': float(doc.get('rate', 0)),
                'is_active': bool(doc.get('is_active', True)),
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
        if not name or not rate_raw:
            return JsonResponse({'success': False, 'error': 'Название и ставка обязательны'}, status=400)
        try:
            rate = float(rate_raw.replace(',', '.'))
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Неверный формат ставки'}, status=400)
        doc = {
            'name': name,
            'rate': rate,
            'is_active': request.POST.get('is_active', 'true') in ['true', 'on', '1'],
            'created_at': datetime.utcnow(),
        }
        res = col.insert_one(doc)
        return JsonResponse({'success': True, 'id': str(res.inserted_id)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mortgage_programs_update(request, program_id):
    """API: обновить ипотечную программу."""
    try:
        print(f"🔄 Обновление программы: {program_id}")
        print(f"📝 POST данные: {dict(request.POST)}")
        
        db = get_mongo_connection()
        col = db['mortgage_programs']
        update = {}
        
        if 'name' in request.POST:
            update['name'] = request.POST.get('name', '').strip()
        if 'rate' in request.POST:
            try:
                update['rate'] = float(request.POST.get('rate', '').strip().replace(',', '.'))
            except ValueError:
                pass
        if 'is_active' in request.POST:
            update['is_active'] = request.POST.get('is_active', 'true') in ['true', 'on', '1']
        if 'is_individual' in request.POST:
            update['is_individual'] = request.POST.get('is_individual', 'false') in ['true', 'on', '1']
        
        # Обновление связанных ЖК
        if 'complexes' in request.POST:
            complexes = request.POST.getlist('complexes')
            is_individual = update.get('is_individual', 
                col.find_one({'_id': ObjectId(program_id)}).get('is_individual', False))
            
            complex_ids = []
            if is_individual and complexes:
                unified_col = db['unified_houses_3']
                for complex_id in complexes:
                    try:
                        if unified_col.find_one({'_id': ObjectId(complex_id)}):
                            complex_ids.append(ObjectId(complex_id))
                    except Exception:
                        continue
            
            update['complexes'] = complex_ids
        
        print(f"📋 Обновления: {update}")
        
        if not update:
            return JsonResponse({'success': False, 'error': 'Нет данных для обновления'}, status=400)
        
        result = col.update_one({'_id': ObjectId(program_id)}, {'$set': update})
        print(f"✅ Результат обновления: {result.modified_count} документов изменено")
        
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"❌ Ошибка обновления: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def mortgage_programs_delete(request, program_id):
    """API: удалить ипотечную программу."""
    try:
        db = get_mongo_connection()
        col = db['mortgage_programs']
        col.delete_one({'_id': ObjectId(program_id)})
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
