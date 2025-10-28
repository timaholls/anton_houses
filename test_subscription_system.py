#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы подписок
Запуск: python3 test_subscription_system.py
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки
BASE_URL = "http://localhost:8000"  # Измените на ваш URL
TEST_EMAIL = "test@example.com"
TEST_NAME = "Тестовый пользователь"

# Настройки SMTP из переменных окружения
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@century21-ufa.ru')
APP_PASSWORD = os.getenv('APP_PASSWORD', '')

def test_subscription_api():
    """Тестирование API подписок"""
    print("🧪 Тестирование системы подписок...")
    
    # 1. Тест подписки
    print("\n1. Тестирование подписки...")
    subscribe_data = {
        "name": TEST_NAME,
        "email": TEST_EMAIL,
        "subscribe_to_projects": True,
        "subscribe_to_promotions": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/subscribe/",
            json=subscribe_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Подписка успешна:", result.get('message'))
            else:
                print("❌ Ошибка подписки:", result.get('error'))
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # 2. Тест статистики
    print("\n2. Тестирование статистики...")
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-stats/")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                stats = result.get('stats', {})
                print("✅ Статистика подписок:")
                print(f"   - Всего подписок: {stats.get('total_subscriptions', 0)}")
                print(f"   - Активных подписок: {stats.get('active_subscriptions', 0)}")
                print(f"   - Подписчиков на проекты: {stats.get('project_subscribers', 0)}")
                print(f"   - Подписчиков на акции: {stats.get('promotion_subscribers', 0)}")
            else:
                print("❌ Ошибка получения статистики:", result.get('error'))
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # 3. Тест отписки
    print("\n3. Тестирование отписки...")
    unsubscribe_data = {
        "email": TEST_EMAIL
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/unsubscribe/",
            json=unsubscribe_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Отписка успешна:", result.get('message'))
            else:
                print("❌ Ошибка отписки:", result.get('error'))
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")


def test_pages():
    """Тестирование страниц"""
    print("\n🌐 Тестирование страниц...")
    
    pages = [
        ("/", "Главная страница"),
        ("/unsubscribe/", "Страница отписки"),
    ]
    
    for url, name in pages:
        try:
            response = requests.get(f"{BASE_URL}{url}")
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Ошибка подключения - {e}")


def test_mongodb_connection():
    """Тестирование подключения к MongoDB"""
    print("\n🗄️ Тестирование подключения к MongoDB...")
    
    try:
        # Инициализируем Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
        import django
        django.setup()
        
        from main.services.mongo_service import get_mongo_connection
        
        db = get_mongo_connection()
        
        # Проверяем коллекцию subscriptions
        subscriptions = db['subscriptions']
        count = subscriptions.count_documents({})
        print(f"✅ Подключение к MongoDB: OK")
        print(f"   - Записей в коллекции subscriptions: {count}")
        
        # Показываем последние подписки
        recent = list(subscriptions.find().sort('created_at', -1).limit(3))
        if recent:
            print("   - Последние подписки:")
            for sub in recent:
                print(f"     * {sub.get('email', 'N/A')} - {sub.get('name', 'N/A')} ({'активна' if sub.get('is_active') else 'неактивна'})")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")


def main():
    """Основная функция"""
    print("🚀 Запуск тестирования системы подписок")
    print(f"📡 Базовый URL: {BASE_URL}")
    print(f"📧 Тестовый email: {TEST_EMAIL}")
    print("=" * 50)
    
    # Проверяем настройки SMTP
    print("📧 Проверка настроек SMTP:")
    print(f"   - SMTP Server: {SMTP_SERVER}")
    print(f"   - SMTP Port: {SMTP_PORT}")
    print(f"   - Sender Email: {SENDER_EMAIL}")
    print(f"   - App Password: {'✅ Настроен' if APP_PASSWORD else '❌ Не настроен'}")
    print("=" * 50)
    
    # Тестируем подключение к MongoDB
    test_mongodb_connection()
    
    # Тестируем страницы
    test_pages()
    
    # Тестируем API
    test_subscription_api()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")
    print("\n💡 Для полного тестирования:")
    print("1. Убедитесь, что сервер запущен")
    print("2. Создайте .env файл с настройками SMTP:")
    print("   SMTP_SERVER=smtp.gmail.com")
    print("   SMTP_PORT=587")
    print("   SENDER_EMAIL=your-email@domain.com")
    print("   APP_PASSWORD=your-app-password")
    print("3. Создайте новый проект через manual-matching")
    print("4. Создайте новую акцию через promotions API")
    print("5. Проверьте получение писем")
    print("\n📝 Пример .env файла:")
    print("SMTP_SERVER=smtp.gmail.com")
    print("SMTP_PORT=587")
    print("SENDER_EMAIL=noreply@century21-ufa.ru")
    print("APP_PASSWORD=your_gmail_app_password")


if __name__ == '__main__':
    main()
