"""Вспомогательные функции"""
import re
import requests
from .s3_service import PLACEHOLDER_IMAGE_URL


def extract_price_from_range(price_range):
    """Извлекает числовое значение цены из строки диапазона цен"""
    if not price_range:
        return 0
    
    # Ищем числа в строке (например, "от 2.5 млн ₽" -> 2.5)
    numbers = re.findall(r'(\d+\.?\d*)', str(price_range))
    if numbers:
        try:
            return float(numbers[0])
        except ValueError:
            return 0
    return 0


def get_video_thumbnail(video_url):
    """
    Получить URL превью для видео из YouTube или Rutube
    """
    if not video_url:
        return None
    
    # YouTube обработка
    if 'youtube.com/watch?v=' in video_url:
        video_id = video_url.split('watch?v=')[-1].split('&')[0]
        return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
    
    elif 'youtu.be/' in video_url:
        video_id = video_url.split('youtu.be/')[-1].split('?')[0]
        return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
    
    # Rutube обработка
    elif 'rutube.ru/video/' in video_url:
        rutube_match = re.search(r'rutube\.ru/video/([a-f0-9]+)', video_url)
        if rutube_match:
            video_id = rutube_match.group(1)
            try:
                api_url = f'https://rutube.ru/api/video/{video_id}/'
                response = requests.get(api_url, timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    thumbnail_url = data.get('thumbnail_url')
                    if thumbnail_url:
                        return thumbnail_url
            except:
                pass
            # Fallback на placeholder если API не работает
            return PLACEHOLDER_IMAGE_URL
    
    # Если не удалось определить тип видео
    return None

