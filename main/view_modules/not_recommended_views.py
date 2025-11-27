"""
Views для страницы "Не рекомендуем" - объекты с низким рейтингом
"""

from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from bson import ObjectId

from ..services.mongo_service import get_mongo_connection


def not_recommended(request):
    """Страница с объектами, которые не рекомендуем (рейтинг < 3)"""
    return render(request, 'main/not_recommended.html', {
        'page_title': 'Не рекомендуем',
        'meta_title': 'Не рекомендуем - CENTURY 21',
        'meta_description': 'Объекты недвижимости с низким рейтингом, которые мы не рекомендуем к покупке'
    })


@require_http_methods(["GET"])
def not_recommended_detail(request, object_id):
    """Детальная страница объекта с низким рейтингом"""
    try:
        db = get_mongo_connection()
        col = db['unified_houses_3']
        
        # Получаем объект
        record = col.find_one({'_id': ObjectId(object_id)})
        if not record:
            raise Http404("Объект не найден")
        
        # Проверяем, что у объекта действительно низкий рейтинг
        rating = record.get('rating')
        if not rating or rating > 3:
            raise Http404("Объект не найден в списке не рекомендуемых")
        
        # Форматируем данные для отображения
        object_data = {
            '_id': str(record['_id']),
            'name': '',
            'address': '',
            'images': [],
            'rating': rating,
            'rating_description': record.get('rating_description', ''),
            'city': record.get('city', 'Уфа'),
            'district': record.get('district', ''),
            'street': record.get('street', ''),
            'latitude': record.get('latitude'),
            'longitude': record.get('longitude'),
            'rating_created_at': record.get('rating_created_at'),
            'rating_updated_at': record.get('rating_updated_at')
        }
        
        # Получаем основную информацию
        if 'development' in record and 'name' in record['development']:
            object_data['name'] = record['development']['name']
        elif 'domrf' in record and 'objCommercNm' in record['domrf']:
            object_data['name'] = record['domrf']['objCommercNm']
        elif 'avito' in record and 'name' in record['avito']:
            object_data['name'] = record['avito']['name']
        
        # Получаем адрес
        if 'development' in record and 'address' in record['development']:
            object_data['address'] = record['development']['address']
        elif 'domrf' in record and 'address' in record['domrf']:
            object_data['address'] = record['domrf']['address']
        elif 'avito' in record and 'address' in record['avito']:
            object_data['address'] = record['avito']['address']
        
        # Получаем изображения
        if 'development' in record and 'photos' in record['development']:
            object_data['images'] = record['development']['photos']
        elif 'domclick' in record and 'photos' in record['domclick']:
            object_data['images'] = record['domclick']['photos']
        
        # Получаем дополнительные данные для детальной страницы
        development_data = record.get('development', {})
        domrf_data = record.get('domrf', {})
        avito_data = record.get('avito', {})
        
        return render(request, 'main/not_recommended_detail.html', {
            'object': object_data,
            'development': development_data,
            'domrf': domrf_data,
            'avito': avito_data,
            'page_title': f'{object_data["name"]} - Не рекомендуем',
            'meta_title': f'{object_data["name"]} - Не рекомендуем - CENTURY 21',
            'meta_description': f'Объект {object_data["name"]} с низким рейтингом. Причины: {object_data["rating_description"]}'
        })
        
    except Exception as e:
        raise Http404("Ошибка загрузки объекта")
