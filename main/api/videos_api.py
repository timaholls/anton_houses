"""
API функции для управления видеообзорами
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime
import json
import re

from ..services.mongo_service import get_mongo_connection
from ..utils import get_video_thumbnail


@require_http_methods(["GET"])
def videos_objects_api(request):
    """API: список объектов для фильтра (Mongo версия для newbuild)."""
    category = request.GET.get('category', '')
    objects = []
    if category == 'newbuild':
        db = get_mongo_connection()
        unified = db['unified_houses']
        # Берём первые 1000 для селекта
        for r in unified.find({}, {'development.name': 1}).limit(1000):
            name = (r.get('development', {}) or {}).get('name') or (r.get('avito', {}) or {}).get('development', {}) .get('name') or (r.get('domclick', {}) or {}).get('development', {}) .get('complex_name') or 'ЖК'
            objects.append({'id': str(r.get('_id')), 'name': name})
    return JsonResponse({'success': True, 'objects': objects})


@csrf_exempt
@require_http_methods(["POST"]) 
def videos_create(request):
    """Создать видеообзор (residential_videos)."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        complex_id = payload.get('complex_id')
        url = (payload.get('url') or '').strip()
        title = (payload.get('title') or '').strip()
        description = (payload.get('description') or '').strip()
        is_active = bool(payload.get('is_active', True))
        if not complex_id or not url or not title:
            return JsonResponse({'success': False, 'error': 'complex_id, url и title обязательны'}, status=400)

        db = get_mongo_connection()
        videos_col = db['residential_videos']
        doc = {
            'complex_id': ObjectId(str(complex_id)),
            'url': url,
            'title': title[:200],
            'description': description[:2000],
            'is_active': is_active,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        res = videos_col.insert_one(doc)
        return JsonResponse({'success': True, 'id': str(res.inserted_id)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"]) 
def videos_list(request):
    """Список видеообзоров (для админ-UI/страницы)."""
    try:
        active = request.GET.get('active')
        db = get_mongo_connection()
        videos_col = db['residential_videos']
        unified = db['unified_houses']
        q = {}
        if active in ('1', 'true', 'True'):
            q['is_active'] = True
        items = []
        for d in videos_col.find(q).sort('created_at', -1):
            comp_name = ''
            try:
                comp = unified.find_one({'_id': d.get('complex_id')}) if isinstance(d.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(d.get('complex_id')))})
                if comp:
                    if 'development' in comp and 'avito' not in comp:
                        comp_name = (comp.get('development', {}) or {}).get('name', '')
                    else:
                        comp_name = (comp.get('avito', {}) or {}).get('development', {}) .get('name') or (comp.get('domclick', {}) or {}).get('development', {}) .get('complex_name', '')
            except Exception:
                comp_name = ''
            video_url = d.get('url', '')
            thumbnail_url = get_video_thumbnail(video_url)
            items.append({
                '_id': str(d.get('_id')),
                'complex_id': str(d.get('complex_id')) if d.get('complex_id') else None,
                'complex_name': comp_name,
                'title': d.get('title'),
                'description': d.get('description'),
                'is_active': d.get('is_active', True),
                'created_at': d.get('created_at').isoformat() if d.get('created_at') else None,
                'thumbnail_url': thumbnail_url,
            })
        return JsonResponse({'success': True, 'data': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"]) 
def videos_by_complex(request, complex_id):
    """Видео по конкретному ЖК для детальной страницы."""
    try:
        db = get_mongo_connection()
        videos_col = db['residential_videos']
        vids = []
        q = {'is_active': True}
        try:
            q['complex_id'] = ObjectId(str(complex_id))
        except Exception:
            return JsonResponse({'success': True, 'data': []})
        for d in videos_col.find(q).sort('created_at', -1):
            url = (d.get('url') or '').strip()
            embed = None
            if url.startswith('<iframe'):
                m = re.search(r'src=["\']([^"\']+)["\']', url)
                embed = m.group(1) if m else url
            elif 'youtu.be/' in url:
                vid = url.split('youtu.be/')[-1].split('?')[0]
                embed = f'https://www.youtube.com/embed/{vid}'
            elif 'watch?v=' in url:
                vid = url.split('watch?v=')[-1].split('&')[0]
                embed = f'https://www.youtube.com/embed/{vid}'
            elif 'rutube.ru' in url:
                if '/play/embed/' in url:
                    embed = url
                else:
                    rm = re.search(r'rutube\.ru/video/([a-f0-9]+)', url)
                    embed = f'https://rutube.ru/play/embed/{rm.group(1)}/' if rm else url
            else:
                embed = url
            vids.append({'id': str(d.get('_id')), 'title': d.get('title',''), 'video_url': embed})
        return JsonResponse({'success': True, 'data': vids})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"]) 
def videos_toggle(request, video_id):
    try:
        db = get_mongo_connection()
        videos_col = db['residential_videos']
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        if 'is_active' in payload:
            new_val = bool(payload.get('is_active'))
        else:
            doc = videos_col.find_one({'_id': ObjectId(video_id)})
            current = bool(doc.get('is_active', True)) if doc else True
            new_val = not current
        videos_col.update_one({'_id': ObjectId(video_id)}, {'$set': {'is_active': new_val, 'updated_at': datetime.utcnow()}})
        return JsonResponse({'success': True, 'is_active': new_val})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def videos_api_delete(request, video_id):
    """API: удалить видеообзор."""
    try:
        db = get_mongo_connection()
        col = db['residential_videos']
        result = col.delete_one({'_id': ObjectId(video_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'Видеообзор не найден'}, status=404)
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
