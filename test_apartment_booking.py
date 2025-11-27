#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы бронирования квартир
Запуск: python3 test_apartment_booking.py
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
TEST_PHONE = "+7 (999) 123-45-67"

def test_apartment_booking_api():
    """Тестирование API бронирования квартир"""
    print("🏠 Тестирование системы бронирования квартир...")
    
    # Тестовые данные для бронирования
    booking_data = {
        'apartment_id': '507f1f77bcf86cd799439011',  # Замените на реальный ID квартиры
        'complex_id': '507f1f77bcf86cd799439012',   # Замените на реальный ID ЖК
        'client_name': TEST_NAME,
        'client_phone': TEST_PHONE
    }
    
    try:
        # Тест создания бронирования
        print("📝 Тестирование создания бронирования...")
        response = requests.post(
            f"{BASE_URL}/api/book-apartment/",
            json=booking_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Бронирование создано успешно: {result.get('message')}")
                booking_id = result.get('booking_id')
                
                # Тест получения статистики
                print("📊 Тестирование получения статистики бронирований...")
                stats_response = requests.get(f"{BASE_URL}/api/booking-stats/")
                
                if stats_response.status_code == 200:
                    stats_result = stats_response.json()
                    if stats_result.get('success'):
                        stats = stats_result.get('stats', {})
                        print(f"✅ Статистика получена:")
                        print(f"   - Всего бронирований: {stats.get('total_bookings', 0)}")
                        print(f"   - Ожидают звонка: {stats.get('pending_bookings', 0)}")
                        print(f"   - Связались: {stats.get('contacted_bookings', 0)}")
                        print(f"   - Забронированы: {stats.get('booked_bookings', 0)}")
                        print(f"   - Отменены: {stats.get('cancelled_bookings', 0)}")
                        
                        recent_bookings = stats_result.get('recent_bookings', [])
                        if recent_bookings:
                            print(f"📋 Последние бронирования:")
                            for booking in recent_bookings[:3]:
                                print(f"   - {booking.get('client_name')} ({booking.get('client_phone')}) - {booking.get('complex_name')}")
                    else:
                        print(f"❌ Ошибка получения статистики: {stats_result.get('error')}")
                else:
                    print(f"❌ Ошибка HTTP при получении статистики: {stats_response.status_code}")
                
                # Тест обновления статуса (если есть booking_id)
                if booking_id:
                    print("🔄 Тестирование обновления статуса бронирования...")
                    update_data = {'status': 'contacted'}
                    update_response = requests.post(
                        f"{BASE_URL}/api/booking/{booking_id}/update-status/",
                        json=update_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if update_response.status_code == 200:
                        update_result = update_response.json()
                        if update_result.get('success'):
                            print(f"✅ Статус обновлен: {update_result.get('message')}")
                        else:
                            print(f"❌ Ошибка обновления статуса: {update_result.get('error')}")
                    else:
                        print(f"❌ Ошибка HTTP при обновлении статуса: {update_response.status_code}")
            else:
                print(f"❌ Ошибка создания бронирования: {result.get('error')}")
        else:
            print(f"❌ Ошибка HTTP при создании бронирования: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к серверу. Убедитесь, что сервер запущен.")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")


def test_apartment_detail_page():
    """Тестирование доступа к детальной странице квартиры"""
    print("\n🏠 Тестирование доступа к детальной странице квартиры...")
    
    # Тестовые ID (замените на реальные)
    test_complex_id = "507f1f77bcf86cd799439012"
    test_apartment_id = "507f1f77bcf86cd799439011"
    
    try:
        response = requests.get(f"{BASE_URL}/apartment/{test_complex_id}/{test_apartment_id}/")
        
        if response.status_code == 200:
            print("✅ Детальная страница квартиры доступна")
            
            # Проверяем наличие ключевых элементов в HTML
            html_content = response.text
            if 'apartment-detail-section' in html_content:
                print("✅ Найден основной контейнер страницы")
            if 'booking-modal' in html_content:
                print("✅ Найдено модальное окно бронирования")
            if 'book-apartment-btn' in html_content:
                print("✅ Найдена кнопка бронирования")
            if 'apartment-gallery' in html_content:
                print("✅ Найдена галерея изображений")
            if 'apartment-characteristics' in html_content:
                print("✅ Найдены характеристики квартиры")
                
        elif response.status_code == 404:
            print("⚠️ Страница не найдена (404). Проверьте ID квартиры и ЖК.")
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к серверу. Убедитесь, что сервер запущен.")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")


def test_mongodb_connection():
    """Тестирование подключения к MongoDB"""
    print("\n🗄️ Тестирование подключения к MongoDB...")
    
    try:
        from pymongo import MongoClient
        
        # Получаем настройки из переменных окружения
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://root:Kfleirb_17@176.98.177.188:27017/admin')
        db_name = os.getenv('DB_NAME', 'houses')
        
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        # Проверяем подключение
        client.admin.command('ping')
        print("✅ Подключение к MongoDB успешно")
        
        # Проверяем коллекцию бронирований
        bookings_collection = db['apartment_bookings']
        total_bookings = bookings_collection.count_documents({})
        print(f"📊 Всего бронирований в базе: {total_bookings}")
        
        # Проверяем коллекцию ЖК
        complexes_collection = db['unified_houses_3']
        total_complexes = complexes_collection.count_documents({})
        print(f"🏢 Всего ЖК в базе: {total_complexes}")
        
        # Проверяем коллекцию сотрудников
        employees_collection = db['employees']
        total_employees = employees_collection.count_documents({})
        print(f"👥 Всего сотрудников в базе: {total_employees}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")


def main():
    """Основная функция"""
    print("🚀 Запуск тестирования системы бронирования квартир")
    print(f"📡 Базовый URL: {BASE_URL}")
    print(f"👤 Тестовый клиент: {TEST_NAME} ({TEST_PHONE})")
    print("=" * 60)
    
    # Тестируем подключение к MongoDB
    test_mongodb_connection()
    
    # Тестируем API бронирования
    test_apartment_booking_api()
    
    # Тестируем детальную страницу квартиры
    test_apartment_detail_page()
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    print("\n💡 Для полного тестирования:")
    print("1. Убедитесь, что сервер запущен")
    print("2. Замените тестовые ID квартир и ЖК на реальные")
    print("3. Откройте детальную страницу ЖК в браузере")
    print("4. Кликните на карточку квартиры")
    print("5. Нажмите кнопку 'Забронировать'")
    print("6. Заполните форму и отправьте")
    print("7. Проверьте создание записи в MongoDB")
    print("\n📝 Структура коллекции apartment_bookings:")
    print("- apartment_id: ObjectId квартиры")
    print("- complex_id: ObjectId ЖК")
    print("- complex_name: Название ЖК")
    print("- client_name: Имя клиента")
    print("- client_phone: Телефон клиента")
    print("- apartment_details: Детали квартиры")
    print("- agent_name: Имя агента")
    print("- status: Статус (pending, contacted, booked, cancelled)")
    print("- created_at: Дата создания")
    print("- updated_at: Дата обновления")


if __name__ == '__main__':
    main()
