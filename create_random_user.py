#!/usr/bin/env python3
"""
Создать в MongoDB (коллекция users) случайного пользователя c безопасным Django-хешем пароля.
Запуск: python3 create_random_user.py

Использует переменные окружения (если заданы):
  MONGO_URI (например, mongodb://user:pass@host:27017/admin)
  DB_NAME   (по умолчанию 'houses')
"""

import os
import sys
import string
import secrets
from pymongo import MongoClient

# Инициализируем Django для генерации хеша пароля
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
try:
    import django  # type: ignore
    django.setup()
    from django.contrib.auth.hashers import make_password  # type: ignore
except Exception as e:
    print('[!] Не удалось инициализировать Django:', e)
    print('    Убедитесь, что запущено из корня проекта и активирован venv.')
    sys.exit(1)


def get_mongo_connection():
    uri = os.getenv('MONGO_URI', 'mongodb://root:Kfleirb_17@176.98.177.188:27017/admin')
    db_name = os.getenv('DB_NAME', 'houses')
    client = MongoClient(uri)
    return client[db_name]


def generate_credentials():
    # Логин как email: user_<8 random>@local.local
    alphabet = string.ascii_lowercase + string.digits
    suffix = ''.join(secrets.choice(alphabet) for _ in range(8))
    email = f'user_{suffix}@local.local'
    # Пароль: 16 символов (буквы, цифры)
    pw_alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(pw_alphabet) for _ in range(16))
    return email, password


def main():
    db = get_mongo_connection()
    users = db['users']

    email, password = generate_credentials()

    # Если внезапно существует — повторим пару раз
    for _ in range(5):
        if users.find_one({'email': email}):
            email, password = generate_credentials()
        else:
            break

    doc = {
        'email': email.lower(),
        'name': email.split('@')[0],
        'password_hash': make_password(password),
        'is_active': True,
        'created_at': __import__('datetime').datetime.utcnow(),
    }

    res = users.insert_one(doc)

    print('\n=== Пользователь создан ===')
    print('ID     :', str(res.inserted_id))
    print('Email  :', email)
    print('Пароль :', password)
    print('\nВход: /login/ (email + пароль)')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Ошибка:', e)
        sys.exit(1)


