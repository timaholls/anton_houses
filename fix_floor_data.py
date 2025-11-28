#!/usr/bin/env python3
"""
Скрипт для исправления некорректных данных floorMin/floorMax.
Находит записи где в title есть "X этаж", но floorMin=1 (ошибка миграции)
и исправляет floorMin на правильное значение X.

Использование:
    python fix_floor_data.py              # Реальный запуск
    python fix_floor_data.py --dry-run    # Тестовый запуск без изменений
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import re
import argparse
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Загружаем переменные окружения
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def get_mongo_connection():
    """Получить подключение к MongoDB"""
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:Kfleirb_17@176.98.177.188:27017/admin")
    DB_NAME = os.getenv("DB_NAME", "houses")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db


def fix_floor_data(dry_run=False):
    """
    Исправляет некорректные данные floorMin/floorMax.
    
    Проблема: скрипт миграции интерпретировал "14 этаж" как диапазон (1, 14),
    хотя это конкретный 14 этаж, т.е. должно быть (14, 14).
    """
    db = get_mongo_connection()
    unified_col = db['unified_houses_3']

    total_checked = 0
    total_fixed = 0

    mode_text = "ТЕСТОВЫЙ РЕЖИМ (dry-run)" if dry_run else "РЕАЛЬНЫЙ РЕЖИМ"
    print(f"Исправление данных floorMin/floorMax... [{mode_text}]")
    print("-" * 60)

    for record in unified_col.find({}):
        complex_id = record.get('_id')

        # Определяем структуру записи
        is_new_structure = 'development' in record and 'avito' not in record

        # Получаем apartment_types
        if is_new_structure:
            apartment_types = record.get('apartment_types', {})
            base_path = 'apartment_types'
        else:
            apartment_types = record.get('avito', {}).get('apartment_types', {})
            base_path = 'avito.apartment_types'

        if not apartment_types:
            continue

        # Проходим по всем типам квартир
        for apt_type, apt_data in apartment_types.items():
            apartments = apt_data.get('apartments', [])

            for apt_index, apt in enumerate(apartments):
                total_checked += 1

                floor_min = apt.get('floorMin')
                floor_max = apt.get('floorMax')
                title = apt.get('title', '')

                # Проверяем проблемный случай: floorMin=1 но в title есть "X этаж" где X > 1
                if floor_min == 1 and floor_max is not None and floor_max > 1:
                    # Сначала проверяем, есть ли диапазон "X-Y этаж" - если да, это корректные данные
                    range_match = re.search(r'(\d+)-(\d+)\s*этаж', title)
                    if range_match:
                        # Это диапазон, проверяем что данные корректны
                        range_start = int(range_match.group(1))
                        range_end = int(range_match.group(2))
                        # Если диапазон в title соответствует floorMin/floorMax - данные правильные, пропускаем
                        if range_start == floor_min and range_end == floor_max:
                            continue

                    # Теперь проверяем одиночный этаж "X этаж"
                    match = re.search(r'(\d+)\s*этаж', title)
                    if match:
                        floor_in_title = int(match.group(1))
                        # Если в title указан конкретный этаж, и он равен floorMax
                        # значит это была ошибка миграции (1, X) вместо (X, X)
                        # НО: проверяем что перед этим числом нет дефиса (т.е. это не часть диапазона)
                        match_pos = match.start()
                        if match_pos > 0 and title[match_pos - 1] == '-':
                            # Это часть диапазона, пропускаем
                            continue
                        if floor_in_title == floor_max and floor_in_title > 1:
                            update_path = f"{base_path}.{apt_type}.apartments.{apt_index}.floorMin"

                            if dry_run:
                                print(f"[БУДЕТ ИСПРАВЛЕНО] ЖК {complex_id}")
                                print(f"  Title: {title[:70]}")
                                print(f"  Было: floorMin=1, floorMax={floor_max}")
                                print(f"  Будет: floorMin={floor_in_title}, floorMax={floor_max}")
                                print()
                            else:
                                # Исправляем floorMin
                                unified_col.update_one(
                                    {'_id': complex_id},
                                    {'$set': {update_path: floor_in_title}}
                                )

                            total_fixed += 1

                            if not dry_run and total_fixed % 100 == 0:
                                print(f"Исправлено записей: {total_fixed}")

    print("-" * 60)
    mode_text = "ТЕСТОВЫЙ РЕЖИМ" if dry_run else "РЕАЛЬНЫЙ РЕЖИМ"
    print(f"Исправление завершено! [{mode_text}]")
    print(f"Всего квартир проверено: {total_checked}")
    if dry_run:
        print(f"Квартир, которые БУДУТ исправлены: {total_fixed}")
    else:
        print(f"Квартир исправлено: {total_fixed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Исправление данных floorMin/floorMax')
    parser.add_argument('--dry-run', action='store_true',
                        help='Тестовый режим: показывает что будет исправлено без применения изменений')
    args = parser.parse_args()

    try:
        fix_floor_data(dry_run=args.dry_run)
    except Exception as e:
        print(f"Ошибка при выполнении: {e}")
        import traceback

        traceback.print_exc()
