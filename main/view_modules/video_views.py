"""Views для видеообзоров"""
import re
from django.shortcuts import render
from django.http import Http404
from django.core.paginator import Paginator
from datetime import datetime
from bson import ObjectId
from ..services.mongo_service import get_mongo_connection
from ..utils import get_video_thumbnail


def videos(request):
    """Видеообзоры из Mongo `residential_videos`"""
    category = request.GET.get('category', '')
    complex_id = request.GET.get('complex', '')
    db = get_mongo_connection()
    videos_col = db['residential_videos']
    unified = db['unified_houses']

    q = {'is_active': True}
    if complex_id:
        try:
            q['complex_id'] = ObjectId(str(complex_id))
        except Exception:
            q['complex_id'] = None

    docs = list(videos_col.find(q).sort('created_at', -1))

    adapted = []
    for d in docs:
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
        adapted.append(type('V', (), {
            'id': str(d.get('_id')),
            'title': d.get('title', ''),
            'video_url': d.get('url', ''),
            'thumbnail_url': get_video_thumbnail(d.get('url', '')),
            'residential_complex_name': comp_name,
            'created_at': d.get('created_at') or datetime.utcnow()
        }))

    page = int(request.GET.get('page', 1))
    per_page = 12
    total = len(adapted)
    start = (page - 1) * per_page
    end = start + per_page
    page_slice = adapted[start:end]

    paginator = Paginator(range(total), per_page)
    page_obj = paginator.get_page(page)

    categories = [
        {'value': 'newbuild', 'name': 'Новостройки'},
        {'value': 'secondary', 'name': 'Вторичная недвижимость'},
    ]

    return render(request, 'main/videos.html', {
        'videos': page_slice,
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
        'filters': {'category': category, 'complex': complex_id},
        'no_videos_for_complex': bool(complex_id and total == 0)
    })


def video_detail(request, video_id):
    """Детальная страница видеообзора (Mongo)"""
    db = get_mongo_connection()
    videos_col = db['residential_videos']
    unified = db['unified_houses']
    d = videos_col.find_one({'_id': ObjectId(str(video_id))})
    if not d:
        raise Http404("Видео не найдено")

    # Формируем embed URL
    video_embed_url = None
    url = (d.get('url') or '').strip()
    if url:

        # Проверяем, является ли это iframe кодом
        if url.startswith('<iframe'):
            # Извлекаем src из iframe
            src_match = re.search(r'src=["\']([^"\']+)["\']', url)
            if src_match:
                video_embed_url = src_match.group(1)
            else:
                video_embed_url = url
        # YouTube обработка
        elif 'youtu.be/' in url:
            vid = url.split('youtu.be/')[-1].split('?')[0]
            video_embed_url = f'https://www.youtube.com/embed/{vid}'
        elif 'watch?v=' in url:
            vid = url.split('watch?v=')[-1].split('&')[0]
            video_embed_url = f'https://www.youtube.com/embed/{vid}'
        # Rutube обработка
        elif 'rutube.ru' in url:
            # Если это уже embed URL
            if '/play/embed/' in url:
                video_embed_url = url
            else:
                # Если это обычная ссылка, пытаемся извлечь ID
                rutube_match = re.search(r'rutube\.ru/video/([a-f0-9]+)', url)
                if rutube_match:
                    rvid = rutube_match.group(1)
                    video_embed_url = f'https://rutube.ru/play/embed/{rvid}/'
                else:
                    video_embed_url = url
        else:
            video_embed_url = url

    # ЖК имя и другие видео этого же ЖК
    comp_name = ''
    same_complex_videos = []
    if d.get('complex_id'):
        comp = unified.find_one({'_id': d.get('complex_id')}) if isinstance(d.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(d.get('complex_id')))})
        if comp:
            if 'development' in comp and 'avito' not in comp:
                comp_name = (comp.get('development', {}) or {}).get('name', '')
            else:
                comp_name = (comp.get('avito', {}) or {}).get('development', {}) .get('name') or (comp.get('domclick', {}) or {}).get('development', {}) .get('complex_name', '')
        for sd in videos_col.find({'complex_id': d.get('complex_id'), '_id': {'$ne': d['_id']}, 'is_active': True}).limit(5):
            video_url = sd.get('url', '')
            thumbnail_url = get_video_thumbnail(video_url)
            same_complex_videos.append(type('V', (), {
                'id': str(sd.get('_id')), 
                'title': sd.get('title',''),
                'thumbnail_url': thumbnail_url,
                'created_at': sd.get('created_at')
            }))

    # Похожие видео (из других объектов того же города)
    similar_videos = []

    video_obj = type('V', (), {
        'id': str(d.get('_id')),
        'title': d.get('title',''),
        'description': d.get('description',''),
        'residential_complex_name': comp_name,
        'created_at': d.get('created_at')
    })

    # Создаем объект residential_complex для шаблона
    residential_complex_obj = None
    if d.get('complex_id'):
        residential_complex_obj = type('ResidentialComplex', (), {
            'id': str(d.get('complex_id')),
            'name': comp_name or 'Неизвестный ЖК'
    })

    context = {
        'video': video_obj,
        'video_embed_url': video_embed_url,
        'residential_complex': residential_complex_obj,
        'same_complex_videos': same_complex_videos,
        'similar_videos': similar_videos,
        'object_type': 'ЖК',
    }
    return render(request, 'main/video_detail.html', context)

