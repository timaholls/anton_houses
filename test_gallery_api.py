#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from django.test import RequestFactory
from main.admin import GalleryAdmin
from main.models import Gallery

def test_gallery_api():
    print("=== Тестирование API галереи ===")
    
    # Создаем тестовый запрос
    factory = RequestFactory()
    
    # Получаем админку
    admin = GalleryAdmin(Gallery, None)
    
    # Тестируем get_objects_view
    print("\n1. Тестирование get_objects_view:")
    request = factory.get('/admin/main/gallery/get-objects/?category=residential_video')
    response = admin.get_objects_view(request)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
    
    # Тестируем get_content_view для видео
    print("\n2. Тестирование get_content_view для видео:")
    request = factory.get('/admin/main/gallery/get-content/?category=residential_video&object_id=149&content_type=video')
    response = admin.get_content_view(request)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
    
    # Проверяем данные напрямую
    print("\n3. Прямая проверка данных:")
    videos = Gallery.objects.filter(
        category='residential_video',
        object_id=149,
        content_type='video'
    ).values('id', 'title', 'content_type', 'order', 'is_main', 'is_active', 'created_at', 'image', 'video_url', 'video_thumbnail', 'description')
    
    print(f"Найдено видео: {videos.count()}")
    for video in videos:
        print(f"Video: {video}")

if __name__ == '__main__':
    test_gallery_api()
