"""
API функции для управления вакансиями
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from bson import ObjectId
from datetime import datetime
import json

from ..services.mongo_service import get_mongo_connection


@require_http_methods(["GET"])
def vacancies_api_list(request):
    """API: список вакансий из Mongo для UI."""
    try:
        db = get_mongo_connection()
        col = db['vacancies']
        items = []
        # Для админки показываем все вакансии (с is_active)
        # Для публичного API фильтруем только активные
        show_all = request.GET.get('admin', 'false').lower() == 'true'
        filter_dict = {} if show_all else {'is_active': True}
        
        for d in col.find(filter_dict).sort('published_date', -1):
            items.append({
                '_id': str(d.get('_id')),
                'slug': d.get('slug') or (str(d.get('_id')) if d.get('_id') else None),
                'title': d.get('title', ''),
                'department': d.get('department', ''),
                'city': d.get('city', 'Уфа'),
                'employment_type': d.get('employment_type', 'fulltime'),
                'salary_from': d.get('salary_from'),
                'salary_to': d.get('salary_to'),
                'currency': d.get('currency', 'RUB'),
                'is_active': bool(d.get('is_active', True)),
                'published_date': (d.get('published_date') or d.get('created_at') or datetime.utcnow()).isoformat(),
            })
        return JsonResponse({'success': True, 'data': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"]) 
def vacancies_api_create(request):
    """API: создать вакансию в Mongo."""
    try:
        data = json.loads(request.body or '{}')
        title = (data.get('title') or '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'Не указано название'}, status=400)

        db = get_mongo_connection()
        col = db['vacancies']
        base_slug = slugify(title)
        slug_val = base_slug
        # ensure unique
        i = 1
        while col.find_one({'slug': slug_val}):
            slug_val = f"{base_slug}-{i}"
            i += 1

        doc = {
            'title': title,
            'slug': slug_val,
            'department': data.get('department') or '',
            'city': data.get('city') or 'Уфа',
            'employment_type': data.get('employment_type') or 'fulltime',
            'salary_from': data.get('salary_from'),
            'salary_to': data.get('salary_to'),
            'currency': data.get('currency') or 'RUB',
            'description': data.get('description') or '',
            'responsibilities': data.get('responsibilities') or '',
            'requirements': data.get('requirements') or '',
            'benefits': data.get('benefits') or '',
            'contact_email': data.get('contact_email') or 'hr@antonhaus.ru',
            'is_active': bool(data.get('is_active', True)),
            'created_at': datetime.utcnow(),
            'published_date': datetime.utcnow(),
            'updated_date': datetime.utcnow(),
        }
        res = col.insert_one(doc)
        return JsonResponse({'success': True, 'id': str(res.inserted_id), 'slug': slug_val})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vacancies_api_toggle(request, vacancy_id):
    """API: переключить статус вакансии (активна/неактивна)."""
    try:
        data = json.loads(request.body or '{}')
        is_active = data.get('is_active', True)
        
        db = get_mongo_connection()
        col = db['vacancies']
        result = col.update_one(
            {'_id': ObjectId(vacancy_id)},
            {'$set': {'is_active': is_active, 'updated_date': datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'Вакансия не найдена'}, status=404)
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def vacancies_api_delete(request, vacancy_id):
    """API: удалить вакансию."""
    try:
        db = get_mongo_connection()
        col = db['vacancies']
        result = col.delete_one({'_id': ObjectId(vacancy_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'Вакансия не найдена'}, status=404)
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
