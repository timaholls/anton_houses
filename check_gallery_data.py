#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from main.models import Gallery

def check_gallery_data():
    print("=== Проверка данных в таблице Gallery ===")
    
    # Получаем все записи
    all_gallery = Gallery.objects.all()
    print(f"Всего записей в Gallery: {all_gallery.count()}")
    
    # Проверяем видео
    videos = Gallery.objects.filter(content_type='video')
    print(f"Видео записей: {videos.count()}")
    
    for video in videos:
        print(f"ID: {video.id}")
        print(f"  Название: {video.title}")
        print(f"  Категория: {video.category}")
        print(f"  Object ID: {video.object_id}")
        print(f"  Video URL: {video.video_url}")
        print(f"  Video Thumbnail: {video.video_thumbnail}")
        print(f"  Is Active: {video.is_active}")
        print(f"  Created: {video.created_at}")
        print("  ---")
    
    # Проверяем изображения
    images = Gallery.objects.filter(content_type='image')
    print(f"Изображений: {images.count()}")
    
    # Проверяем записи с video_file (если есть)
    try:
        # Попробуем получить поле video_file (может не существовать)
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(main_gallery)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'video_file' in columns:
                print("⚠️  Поле video_file все еще существует в базе данных!")
                cursor.execute("SELECT COUNT(*) FROM main_gallery WHERE video_file IS NOT NULL AND video_file != ''")
                count = cursor.fetchone()[0]
                print(f"Записей с video_file: {count}")
            else:
                print("✅ Поле video_file удалено из базы данных")
    except Exception as e:
        print(f"Ошибка при проверке структуры таблицы: {e}")

if __name__ == '__main__':
    check_gallery_data()
