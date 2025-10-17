from pymongo import MongoClient
from django.conf import settings
from main.s3_service import PLACEHOLDER_IMAGE_URL


def get_mongo_connection():
    """Получить подключение к MongoDB из настроек проекта."""
    uri = getattr(settings, 'MONGO_URI', 'mongodb://root:Kfleirb_17@176.98.177.188:27017/admin')
    db_name = getattr(settings, 'DB_NAME', 'houses')
    client = MongoClient(uri)
    return client[db_name]


def head_office(request):
    """Контекст-процессор для добавления головного офиса во все шаблоны"""
    try:
        db = get_mongo_connection()
        head_office = db['branch_offices'].find_one({'is_active': True, 'is_head_office': True})
        if head_office:
            # Преобразуем _id в строку для безопасного использования в шаблонах
            head_office['id'] = str(head_office.get('_id'))
        return {'head_office': head_office}
    except Exception as e:
        return {'head_office': None}


def s3_context(request):
    """Контекст-процессор для добавления констант S3 во все шаблоны"""
    return {
        'PLACEHOLDER_IMAGE_URL': PLACEHOLDER_IMAGE_URL,
    }
