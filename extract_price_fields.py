#!/usr/bin/env python
"""
Скрипт для извлечения min_price и max_price из price_range
и сохранения их в отдельные поля в базе данных.

Использование:
    python extract_price_fields.py              # Реальный запуск
    python extract_price_fields.py --dry-run    # Тестовый запуск без изменений
"""

import os
import sys
import re
from typing import Optional, Tuple

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
import django
django.setup()

from main.services.mongo_service import get_mongo_connection


def parse_price_range(price_range: str) -> Optional[Tuple[float, float]]:
    """
    Парсит строку price_range и извлекает минимальную и максимальную цену.
    
    Формат: "От 6,29 до 14,97 млн ₽" или "От 3,37 до 12,68 млн"
    
    Returns:
        Tuple[float, float] или None: (min_price, max_price) в миллионах рублей
    """
    if not price_range:
        return None
    
    # Приводим к нижнему регистру для унификации
    price_lower = price_range.lower()
    
    # Ищем паттерн "от X до Y млн"
    # Поддерживаем разные варианты: "от 6,29 до 14,97 млн", "от 3.37 до 12.68 млн" и т.д.
    pattern = r'от\s+([\d,\.]+)\s+до\s+([\d,\.]+)\s+млн'
    match = re.search(pattern, price_lower)
    
    if match:
        try:
            min_price_str = match.group(1).replace(',', '.')
            max_price_str = match.group(2).replace(',', '.')
            
            min_price = float(min_price_str)
            max_price = float(max_price_str)
            
            # Проверяем, что min <= max
            if min_price > max_price:
                print(f"  ⚠️  Предупреждение: min_price ({min_price}) > max_price ({max_price}), меняем местами")
                min_price, max_price = max_price, min_price
            
            return (min_price, max_price)
        except (ValueError, TypeError) as e:
            print(f"  ❌ Ошибка парсинга чисел: {e}")
            return None
    
    # Если не нашли полный паттерн, пробуем найти только "от X"
    pattern_from = r'от\s+([\d,\.]+)\s+млн'
    match_from = re.search(pattern_from, price_lower)
    
    if match_from:
        try:
            min_price_str = match_from.group(1).replace(',', '.')
            min_price = float(min_price_str)
            # Если есть только "от", используем его как min и max
            return (min_price, min_price)
        except (ValueError, TypeError) as e:
            print(f"  ❌ Ошибка парсинга числа 'от': {e}")
            return None
    
    return None


def extract_price_from_record(record: dict) -> Optional[Tuple[float, float]]:
    """
    Извлекает price_range из записи (поддержка новой и старой структуры).
    
    Returns:
        Tuple[float, float] или None: (min_price, max_price) в миллионах рублей
    """
    # Определяем структуру записи
    is_new_structure = 'development' in record and 'avito' not in record
    
    price_range = ''
    if is_new_structure:
        # Новая структура
        development = record.get('development', {})
        price_range = development.get('price_range', '')
    else:
        # Старая структура
        avito_dev = record.get('avito', {}).get('development', {}) if record.get('avito') else {}
        price_range = avito_dev.get('price_range', '')
    
    if not price_range:
        return None
    
    return parse_price_range(price_range)


def update_price_fields(dry_run: bool = False):
    """
    Проходит по всем ЖК в unified_houses_3 и добавляет поля min_price и max_price.
    
    Args:
        dry_run: Если True, только показывает что будет сделано, без изменений в БД
    """
    print("=" * 80)
    print("📊 Извлечение цен из price_range и сохранение в min_price/max_price")
    print("=" * 80)
    
    if dry_run:
        print("🔍 РЕЖИМ ТЕСТИРОВАНИЯ (dry-run) - изменения не будут сохранены")
    else:
        print("💾 РЕЖИМ РЕАЛЬНОГО ОБНОВЛЕНИЯ - изменения будут сохранены в БД")
    print()
    
    try:
        db = get_mongo_connection()
        unified_col = db['unified_houses_3']
        
        # Получаем все записи
        total_records = unified_col.count_documents({})
        print(f"📦 Всего записей в unified_houses_3: {total_records}")
        print()
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        # Проходим по всем записям
        for record in unified_col.find({}):
            record_id = record.get('_id')
            record_name = ''
            
            # Получаем название для вывода
            if 'development' in record and 'avito' not in record:
                record_name = record.get('development', {}).get('name', 'Без названия')
            else:
                avito_dev = record.get('avito', {}).get('development', {}) if record.get('avito') else {}
                record_name = avito_dev.get('name', 'Без названия')
            
            print(f"🔍 Обработка: {record_name} (ID: {record_id})")
            
            # Извлекаем цены
            prices = extract_price_from_record(record)
            
            if prices is None:
                print(f"  ⏭️  Пропущено: price_range не найден или не распарсен")
                skipped_count += 1
                print()
                continue
            
            min_price, max_price = prices
            
            # Проверяем, нужно ли обновлять (если поля уже есть и совпадают, пропускаем)
            current_min = record.get('min_price')
            current_max = record.get('max_price')
            
            if current_min == min_price and current_max == max_price:
                print(f"  ✅ Уже обновлено: min_price={min_price}, max_price={max_price}")
                print()
                continue
            
            print(f"  💰 Найдены цены: min={min_price} млн, max={max_price} млн")
            
            if not dry_run:
                # Обновляем запись
                try:
                    result = unified_col.update_one(
                        {'_id': record_id},
                        {
                            '$set': {
                                'min_price': min_price,
                                'max_price': max_price
                            }
                        }
                    )
                    
                    if result.modified_count > 0:
                        print(f"  ✅ Обновлено в БД")
                        updated_count += 1
                    else:
                        print(f"  ⚠️  Запись не была изменена (возможно, поля уже были установлены)")
                        skipped_count += 1
                except Exception as e:
                    print(f"  ❌ Ошибка обновления: {e}")
                    error_count += 1
            else:
                print(f"  🔍 [DRY-RUN] Будет установлено: min_price={min_price}, max_price={max_price}")
                updated_count += 1
            
            print()
        
        # Итоговая статистика
        print("=" * 80)
        print("📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"  ✅ Обновлено: {updated_count}")
        print(f"  ⏭️  Пропущено: {skipped_count}")
        print(f"  ❌ Ошибок: {error_count}")
        print(f"  📦 Всего обработано: {updated_count + skipped_count + error_count}")
        print("=" * 80)
        
        if dry_run:
            print("\n💡 Для реального обновления запустите скрипт без флага --dry-run")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    update_price_fields(dry_run=dry_run)
