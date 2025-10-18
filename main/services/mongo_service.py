"""Сервис для работы с MongoDB"""
import os
from datetime import datetime
from pymongo import MongoClient


def get_mongo_connection():
    """Получить подключение к MongoDB"""
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:Kfleirb_17@176.98.177.188:27017/admin")
    DB_NAME = os.getenv("DB_NAME", "houses")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db


def get_mongo_user(email: str):
    """Получить пользователя из Mongo по email."""
    try:
        db = get_mongo_connection()
        return db['users'].find_one({'email': email.lower()})
    except Exception:
        return None


def get_residential_complexes_from_mongo(filters=None, sort_by=None, limit=None, random=False):
    """Получить ЖК из MongoDB"""
    try:
        db = get_mongo_connection()
        collection = db['residential_complexes']
        
        # Базовый фильтр
        mongo_filter = {'status': {'$ne': 'deleted'}}
        
        # Применяем дополнительные фильтры
        if filters:
            if filters.get('status'):
                mongo_filter['status'] = filters['status']
            if filters.get('house_class'):
                mongo_filter['development.parameters.Класс жилья'] = filters['house_class']
            if filters.get('city'):
                mongo_filter['address.city'] = {'$regex': filters['city'], '$options': 'i'}
            if filters.get('district'):
                mongo_filter['address.district'] = {'$regex': filters['district'], '$options': 'i'}
            if filters.get('finishing'):
                mongo_filter['development.parameters.Отделка'] = filters['finishing']
            if filters.get('is_featured') is not None:
                mongo_filter['is_featured'] = filters['is_featured']
        
        # Выполняем запрос
        if random:
            # Для случайной выборки используем $sample
            cursor = collection.aggregate([
                {'$match': mongo_filter},
                {'$sample': {'size': limit or 10}}
            ])
            complexes = list(cursor)
        else:
            # Обычная сортировка
            sort_dict = {}
            if sort_by:
                if sort_by == 'price_asc':
                    sort_dict['price.min'] = 1
                elif sort_by == 'price_desc':
                    sort_dict['price.min'] = -1
                elif sort_by == 'delivery_date_asc':
                    sort_dict['development.delivery_date'] = 1
                elif sort_by == 'delivery_date_desc':
                    sort_dict['development.delivery_date'] = -1
                elif sort_by == 'name_asc':
                    sort_dict['name'] = 1
                else:
                    sort_dict['name'] = 1
            else:
                sort_dict['name'] = 1
            
            cursor = collection.find(mongo_filter).sort(list(sort_dict.items()))
            
            if limit:
                cursor = cursor.limit(limit)
            
            complexes = list(cursor)
        
        # Преобразуем _id в строку и добавляем как поле id для использования в шаблонах
        for complex_item in complexes:
            if '_id' in complex_item:
                complex_item['id'] = str(complex_item['_id'])
        
        return complexes
    except Exception as e:
        print(f"Ошибка получения ЖК из MongoDB: {e}")
        return []


def get_special_offers_from_mongo(limit=None):
    """Получить акции из MongoDB"""
    try:
        db = get_mongo_connection()
        collection = db['promotions']
        
        # Фильтр активных акций
        mongo_filter = {
            'is_active': True,
            '$or': [
                {'expires_at': {'$exists': False}},
                {'expires_at': None},
                {'expires_at': {'$gt': datetime.now()}}
            ]
        }
        
        cursor = collection.find(mongo_filter).sort('created_at', -1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    except Exception as e:
        print(f"Ошибка получения акций из MongoDB: {e}")
        return []


def get_future_complexes_from_mongo(filters=None, sort_by=None, limit=None):
    """Получить будущие ЖК из MongoDB"""
    try:
        db = get_mongo_connection()
        collection = db['future_complexes']
        
        # Базовый фильтр
        mongo_filter = {'is_active': True}
        
        # Применяем дополнительные фильтры
        if filters:
            if filters.get('city'):
                mongo_filter['city'] = {'$regex': filters['city'], '$options': 'i'}
            if filters.get('district'):
                mongo_filter['district'] = {'$regex': filters['district'], '$options': 'i'}
            if filters.get('price_from'):
                mongo_filter['price_from'] = {'$gte': float(filters['price_from'])}
            if filters.get('price_to'):
                mongo_filter['price_from'] = {'$lte': float(filters['price_to'])}
            if filters.get('delivery_date'):
                mongo_filter['delivery_date'] = {'$lte': filters['delivery_date']}
        
        # Сортировка
        sort_dict = {}
        if sort_by:
            if sort_by == 'delivery_date_asc':
                sort_dict['delivery_date'] = 1
            elif sort_by == 'delivery_date_desc':
                sort_dict['delivery_date'] = -1
            elif sort_by == 'price_asc':
                sort_dict['price_from'] = 1
            elif sort_by == 'price_desc':
                sort_dict['price_from'] = -1
            elif sort_by == 'name_asc':
                sort_dict['name'] = 1
            else:
                sort_dict['delivery_date'] = 1
        else:
            sort_dict['delivery_date'] = 1
        
        # Выполняем запрос
        cursor = collection.find(mongo_filter).sort(list(sort_dict.items()))
        
        if limit:
            cursor = cursor.limit(limit)
        
        # Преобразуем _id в строку и добавляем как поле id для использования в шаблонах
        complexes = list(cursor)
        for complex_item in complexes:
            if '_id' in complex_item:
                complex_item['id'] = str(complex_item['_id'])
            
            # Отладочная информация для фотографий
            if complex_item.get('name'):
                gallery_photos = complex_item.get('gallery_photos', [])
                print(f"🔍 DEBUG: ЖК '{complex_item['name']}' - gallery_photos: {len(gallery_photos)} шт.")
                if gallery_photos:
                    print(f"🔍 DEBUG: Первое фото: {gallery_photos[0]}")
        
        print(f"🔍 DEBUG: Всего найдено {len(complexes)} будущих ЖК")
        return complexes
    except Exception as e:
        print(f"Ошибка получения будущих ЖК из MongoDB: {e}")
        return []

