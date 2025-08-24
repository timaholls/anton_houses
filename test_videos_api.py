#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from django.test import RequestFactory
from main.views import videos_objects_api

def test_videos_api():
    print("=== Тестирование API видеообзоров ===")
    
    # Создаем тестовый запрос
    factory = RequestFactory()
    
    # Тестируем API для новостроек
    print("\n1. Тестирование API для новостроек:")
    request = factory.get('/api/videos/objects/?category=newbuild')
    response = videos_objects_api(request)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
    
    # Тестируем API для вторичной недвижимости
    print("\n2. Тестирование API для вторичной недвижимости:")
    request = factory.get('/api/videos/objects/?category=secondary')
    response = videos_objects_api(request)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
    
    # Тестируем API без категории
    print("\n3. Тестирование API без категории:")
    request = factory.get('/api/videos/objects/')
    response = videos_objects_api(request)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")

if __name__ == '__main__':
    test_videos_api()
