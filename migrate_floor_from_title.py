#!/usr/bin/env python3
"""
Скрипт для миграции этажей из title в отдельные поля floorMin/floorMax
Проходит по всем квартирам в unified_houses_3 и заполняет этаж из title, если его нет в отдельных полях

Использование:
    python migrate_floor_from_title.py              # Реальный запуск
    python migrate_floor_from_title.py --dry-run     # Тестовый запуск без изменений
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
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


def parse_floor_from_title(title: str) -> Optional[Tuple[int, int]]:
    """
    Парсит этаж из title
    Форматы: "1-комн, 35.16 м², 3-6 этаж", "14/27 эт", "2-12 этаж", "5 этаж"
    Возвращает: (floorMin, floorMax) или None если не найдено
    """
    if not title:
        return None
    
    # Паттерн 1: "X/Y эт" или "X/Y" (этаж/всего этажей)
    match = re.search(r'(\d+)/(\d+)\s*эт', title)
    if match:
        try:
            floor_min = int(match.group(1))
            floor_max = int(match.group(2))
            # Если вторая цифра намного больше первой, это "этаж X из Y"
            # Используем только этаж квартиры (первая цифра)
            if floor_max > floor_min * 2:
                return (floor_min, floor_min)
            else:
                # Это может быть диапазон
                return (floor_min, floor_max)
        except ValueError:
            pass
    
    # Паттерн 2: "X-Y этаж" (всегда диапазон этажей в контексте title)
    # Например: "5-21 этаж" означает этажи от 5 до 21
    match = re.search(r'(\d+)-(\d+)\s*этаж', title)
    if match:
        try:
            first_num = int(match.group(1))
            second_num = int(match.group(2))
            # В формате "X-Y этаж" это всегда диапазон этажей
            return (first_num, second_num)
        except ValueError:
            pass
    
    # Паттерн 3: "X этаж" (одно число) - это конкретный этаж квартиры
    # Например: "14 этаж" означает квартира на 14 этаже
    match = re.search(r'(\d+)\s*этаж', title)
    if match:
        try:
            floor_num = int(match.group(1))
            # Одиночный этаж - конкретная квартира на этом этаже
            return (floor_num, floor_num)
        except ValueError:
            pass
    
    # Паттерн 4: "X из Y этаж" или "X из Y"
    match = re.search(r'(\d+)\s+из\s+(\d+)', title)
    if match:
        try:
            floor_min = int(match.group(1))
            floor_max = int(match.group(2))
            # Используем только этаж квартиры
            return (floor_min, floor_min)
        except ValueError:
            pass
    
    return None


def migrate_floors(dry_run=False):
    """
    Основная функция миграции
    
    Args:
        dry_run: Если True, только показывает что будет изменено, без применения изменений
    """
    db = get_mongo_connection()
    unified_col = db['unified_houses_3']
    
    total_complexes = 0
    total_apartments_processed = 0
    total_apartments_updated = 0
    total_apartments_with_title = 0
    total_apartments_without_floor = 0
    
    mode_text = "ТЕСТОВЫЙ РЕЖИМ (dry-run)" if dry_run else "РЕАЛЬНЫЙ РЕЖИМ"
    print(f"Начинаем миграцию этажей из title... [{mode_text}]")
    print("-" * 60)
    
    # Проходим по всем ЖК
    for complex_record in unified_col.find({}):
        total_complexes += 1
        complex_id = complex_record.get('_id')
        
        # Определяем структуру записи
        is_new_structure = 'development' in complex_record and 'avito' not in complex_record
        
        # Получаем apartment_types
        if is_new_structure:
            apartment_types = complex_record.get('apartment_types', {})
        else:
            apartment_types = complex_record.get('avito', {}).get('apartment_types', {})
        
        if not apartment_types:
            continue
        
        updated = False
        
        # Проходим по всем типам квартир
        for apt_type, apt_data in apartment_types.items():
            apartments = apt_data.get('apartments', [])
            
            for apt_index, apt in enumerate(apartments):
                total_apartments_processed += 1
                
                # Проверяем, есть ли уже этаж в отдельных полях
                floor = apt.get('floor') or apt.get('floor_number')
                floor_min = apt.get('floorMin')
                floor_max = apt.get('floorMax')
                
                # Если этаж уже есть в отдельных полях, пропускаем
                if floor or floor_min is not None or floor_max is not None:
                    continue
                
                total_apartments_without_floor += 1
                
                # Пытаемся извлечь этаж из title
                title = apt.get('title', '')
                if not title:
                    continue
                
                total_apartments_with_title += 1
                
                floor_info = parse_floor_from_title(title)
                if floor_info:
                    floor_min_new, floor_max_new = floor_info
                    
                    # Формируем информацию для вывода
                    apartment_id = apt.get('id', f'{apt_type}_{apt_index}')
                    update_path = f"apartment_types.{apt_type}.apartments.{apt_index}"
                    
                    if dry_run:
                        # В тестовом режиме только выводим информацию
                        print(f"  [БУДЕТ ОБНОВЛЕНО] ЖК {complex_id}, квартира {apartment_id}")
                        print(f"    Title: {title[:80]}...")
                        print(f"    Будет добавлено: floorMin={floor_min_new}, floorMax={floor_max_new}")
                        print()
                    else:
                        # В реальном режиме обновляем запись
                        update_query = {
                            f"{update_path}.floorMin": floor_min_new,
                            f"{update_path}.floorMax": floor_max_new
                        }
                        
                        unified_col.update_one(
                            {'_id': complex_id},
                            {'$set': update_query}
                        )
                    
                    total_apartments_updated += 1
                    updated = True
                    
                    if not dry_run and total_apartments_updated % 100 == 0:
                        print(f"Обновлено квартир: {total_apartments_updated}")
        
        if updated:
            print(f"ЖК {complex_id}: обновлены этажи")
    
    print("-" * 60)
    mode_text = "ТЕСТОВЫЙ РЕЖИМ" if dry_run else "РЕАЛЬНЫЙ РЕЖИМ"
    print(f"Миграция завершена! [{mode_text}]")
    print(f"Всего ЖК обработано: {total_complexes}")
    print(f"Всего квартир обработано: {total_apartments_processed}")
    print(f"Квартир без этажа в отдельных полях: {total_apartments_without_floor}")
    print(f"Квартир с title: {total_apartments_with_title}")
    if dry_run:
        print(f"Квартир, которые БУДУТ обновлены: {total_apartments_updated}")
    else:
        print(f"Всего квартир обновлено: {total_apartments_updated}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Миграция этажей из title в отдельные поля')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Тестовый режим: показывает что будет изменено без применения изменений')
    args = parser.parse_args()
    
    try:
        migrate_floors(dry_run=args.dry_run)
    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        import traceback
        traceback.print_exc()

