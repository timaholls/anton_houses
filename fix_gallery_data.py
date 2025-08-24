#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from main.models import Gallery

def fix_gallery_data():
    print("=== Исправление данных в таблице Gallery ===")
    
    # 1. Находим видео записи с пустым video_url
    empty_video_urls = Gallery.objects.filter(
        content_type='video',
        video_url__isnull=True
    ) | Gallery.objects.filter(
        content_type='video',
        video_url=''
    )
    
    print(f"Найдено видео с пустым video_url: {empty_video_urls.count()}")
    
    for video in empty_video_urls:
        print(f"ID: {video.id}, Название: {video.title}")
        # Удаляем записи без video_url, так как они бесполезны
        video.delete()
        print(f"  -> Удалена запись {video.id}")
    
    # 2. Проверяем видео с iframe кодами
    iframe_videos = Gallery.objects.filter(
        content_type='video',
        video_url__contains='<iframe'
    )
    
    print(f"Найдено видео с iframe кодами: {iframe_videos.count()}")
    
    for video in iframe_videos:
        print(f"ID: {video.id}, Название: {video.title}")
        print(f"  Текущий video_url: {video.video_url[:100]}...")
        
        # Извлекаем src из iframe
        import re
        src_match = re.search(r'src=["\']([^"\']+)["\']', video.video_url)
        if src_match:
            new_url = src_match.group(1)
            video.video_url = new_url
            video.save()
            print(f"  -> Обновлен video_url: {new_url}")
        else:
            print(f"  -> Не удалось извлечь src из iframe")
    
    # 3. Финальная проверка
    print("\n=== Финальная проверка ===")
    videos = Gallery.objects.filter(content_type='video')
    print(f"Всего видео записей: {videos.count()}")
    
    for video in videos:
        print(f"ID: {video.id}")
        print(f"  Название: {video.title}")
        print(f"  Video URL: {video.video_url}")
        print(f"  Is Active: {video.is_active}")
        print("  ---")

if __name__ == '__main__':
    fix_gallery_data()
