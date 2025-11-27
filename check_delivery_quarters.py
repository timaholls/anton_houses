"""
Скрипт для проверки генерации кварталов и подсчета ЖК по каждому фильтру
"""
import os
import sys
import django

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from datetime import datetime, date
from main.services.mongo_service import get_mongo_connection

def get_all_delivery_dates_from_db():
    """Получает все уникальные сроки сдачи из базы данных"""
    db = get_mongo_connection()
    unified_col = db['unified_houses_3']
    all_records = list(unified_col.find({}))
    
    delivery_dates = set()
    
    for record in all_records:
        # Получаем срок сдачи из parameters
        completion_date_str = None
        
        if 'development' in record and 'avito' not in record:
            # Новая структура
            dev = record.get('development', {})
            parameters = dev.get('parameters', {})
            completion_date_str = parameters.get('Срок сдачи', '')
        else:
            # Старая структура
            avito_dev = record.get('avito', {}).get('development', {})
            if avito_dev:
                parameters = avito_dev.get('parameters', {})
                completion_date_str = parameters.get('Срок сдачи', '')
            
            if not completion_date_str:
                domrf_dev = record.get('domrf', {}).get('development', {})
                if domrf_dev:
                    parameters = domrf_dev.get('parameters', {})
                    completion_date_str = parameters.get('Срок сдачи', '')
        
        if completion_date_str:
            # Парсим срок сдачи и добавляем все кварталы из диапазона
            parsed_date = parse_completion_date(completion_date_str)
            if parsed_date:
                delivery_dates.add(parsed_date)
    
    return sorted(list(delivery_dates))


def get_delivery_quarters():
    """Генерирует список кварталов на основе реальных данных из базы"""
    print("=" * 80)
    print("ИНФОРМАЦИЯ О ТЕКУЩЕЙ ДАТЕ")
    print("=" * 80)
    current_date = datetime.now().date()
    current_year = current_date.year
    current_month = current_date.month
    current_quarter = (current_month - 1) // 3 + 1
    
    print(f"Текущая дата: {current_date}")
    print(f"Текущий год: {current_year}")
    print(f"Текущий месяц: {current_month}")
    print(f"Текущий квартал: Q{current_quarter}")
    print()
    
    print("=" * 80)
    print("ПОЛУЧЕНИЕ СРОКОВ СДАЧИ ИЗ БАЗЫ ДАННЫХ")
    print("=" * 80)
    
    # Получаем все уникальные сроки сдачи из базы
    all_delivery_dates = get_all_delivery_dates_from_db()
    
    print(f"Найдено уникальных сроков сдачи: {len(all_delivery_dates)}")
    print()
    
    # Создаем множество кварталов из всех дат
    quarters_set = set()
    
    for delivery_date in all_delivery_dates:
        # Пропускаем прошедшие даты
        if delivery_date < current_date:
            continue
        
        year = delivery_date.year
        month = delivery_date.month
        
        # Определяем квартал по месяцу
        if month <= 3:
            quarter = 1
        elif month <= 6:
            quarter = 2
        elif month <= 9:
            quarter = 3
        else:
            quarter = 4
        
        # Вычисляем последний день квартала
        if quarter == 1:
            end_date = date(year, 3, 31)
        elif quarter == 2:
            end_date = date(year, 6, 30)
        elif quarter == 3:
            end_date = date(year, 9, 30)
        else:  # quarter == 4
            end_date = date(year, 12, 31)
        
        quarters_set.add((year, quarter, end_date))
    
    # Преобразуем в список и сортируем
    quarters_list = []
    for year, quarter, end_date in sorted(quarters_set):
        value = f"Q{quarter}_{year}"
        label = f"До {quarter} квартала {year} года"
        
        quarters_list.append({
            'value': value,
            'label': label,
            'end_date': end_date,
            'year': year,
            'quarter': quarter
        })
    
    print(f"Сгенерировано уникальных кварталов: {len(quarters_list)}")
    print()
    
    return quarters_list


def parse_completion_date(completion_date_str):
    """Парсит строку срока сдачи вида '4 кв. 2017 — 2 кв. 2027' или '3 кв. 2024 – 3 кв. 2027'
    Возвращает максимальную дату (последний квартал)"""
    if not completion_date_str:
        return None
    
    import re
    # Ищем паттерны типа "4 кв. 2017" или "2 кв. 2027"
    # Может быть диапазон "4 кв. 2017 — 2 кв. 2027" или одно значение "3 кв. 2024"
    patterns = re.findall(r'(\d+)\s*кв\.\s*(\d{4})', completion_date_str)
    
    if not patterns:
        return None
    
    max_date = None
    for quarter_str, year_str in patterns:
        try:
            quarter = int(quarter_str)
            year = int(year_str)
            
            # Вычисляем последний день квартала
            if quarter == 1:
                end_date = date(year, 3, 31)
            elif quarter == 2:
                end_date = date(year, 6, 30)
            elif quarter == 3:
                end_date = date(year, 9, 30)
            elif quarter == 4:
                end_date = date(year, 12, 31)
            else:
                continue
            
            # Берем максимальную дату (последний квартал в диапазоне)
            if not max_date or end_date > max_date:
                max_date = end_date
        except (ValueError, TypeError):
            continue
    
    return max_date


def get_complexes_for_quarter(end_date):
    """Получает список ЖК, которые подходят под фильтр по кварталу"""
    db = get_mongo_connection()
    unified_col = db['unified_houses_3']
    
    # Получаем все записи
    all_records = list(unified_col.find({}))
    
    print(f"  Всего записей в базе: {len(all_records)}")
    
    matching_complexes = []
    records_without_date = 0
    records_with_date = 0
    
    for record in all_records:
        # Получаем срок сдачи из parameters (как в catalog_api)
        completion_date_str = None
        delivery_date = None
        delivery_date_source = None
        
        if 'development' in record and 'avito' not in record:
            # Новая структура
            dev = record.get('development', {})
            parameters = dev.get('parameters', {})
            completion_date_str = parameters.get('Срок сдачи', '')
            delivery_date_source = 'development.parameters.Срок сдачи'
        else:
            # Старая структура - проверяем разные источники
            avito_dev = record.get('avito', {}).get('development', {})
            if avito_dev:
                parameters = avito_dev.get('parameters', {})
                completion_date_str = parameters.get('Срок сдачи', '')
                if completion_date_str:
                    delivery_date_source = 'avito.development.parameters.Срок сдачи'
            
            if not completion_date_str:
                domrf_dev = record.get('domrf', {}).get('development', {})
                if domrf_dev:
                    parameters = domrf_dev.get('parameters', {})
                    completion_date_str = parameters.get('Срок сдачи', '')
                    if completion_date_str:
                        delivery_date_source = 'domrf.development.parameters.Срок сдачи'
        
        if not completion_date_str:
            records_without_date += 1
            continue
        
        # Парсим срок сдачи
        delivery_date = parse_completion_date(completion_date_str)
        
        if not delivery_date:
            records_without_date += 1
            continue
        
        records_with_date += 1
        
        # Фильтруем: показываем только ЖК со сроком сдачи до выбранного квартала
        if delivery_date and delivery_date <= end_date:
            complex_id = str(record.get('_id'))
            complex_name = 'Без названия'
            
            # Получаем название ЖК
            if 'development' in record and 'avito' not in record:
                complex_name = record.get('development', {}).get('name', 'Без названия')
            else:
                avito_dev = record.get('avito', {}).get('development', {})
                complex_name = avito_dev.get('name', 'Без названия')
                if not complex_name:
                    domrf_dev = record.get('domrf', {}).get('development', {})
                    complex_name = domrf_dev.get('name', 'Без названия')
            
            matching_complexes.append({
                'id': complex_id,
                'name': complex_name,
                'delivery_date': delivery_date,
                'completion_date_str': completion_date_str,
                'source': delivery_date_source
            })
    
    print(f"  Записей с delivery_date: {records_with_date}")
    print(f"  Записей без delivery_date: {records_without_date}")
    
    return matching_complexes


def main():
    print("\n" + "=" * 80)
    print("ПРОВЕРКА ГЕНЕРАЦИИ КВАРТАЛОВ И ПОДСЧЕТ ЖК")
    print("=" * 80)
    print()
    
    # 1. Генерируем список кварталов
    quarters = get_delivery_quarters()
    
    print("=" * 80)
    print("СПИСОК КВАРТАЛОВ ДЛЯ ВЫПАДАЮЩЕГО СПИСКА")
    print("=" * 80)
    print(f"Всего кварталов: {len(quarters)}")
    print()
    
    for i, quarter in enumerate(quarters, 1):
        print(f"{i}. {quarter['label']}")
        print(f"   Значение: {quarter['value']}")
        print(f"   Конечная дата: {quarter['end_date']}")
        print()
    
    print("=" * 80)
    print("ПОДСЧЕТ ЖК ПО КАЖДОМУ ФИЛЬТРУ (КВАРТАЛУ)")
    print("=" * 80)
    print()
    
    # 2. Для каждого квартала находим подходящие ЖК
    for quarter in quarters:
        print(f"Фильтр: {quarter['label']} (до {quarter['end_date']})")
        print("-" * 80)
        
        matching_complexes = get_complexes_for_quarter(quarter['end_date'])
        
        print(f"Количество ЖК: {len(matching_complexes)}")
        print()
        
        if matching_complexes:
            print("Список ЖК:")
            for comp in matching_complexes[:10]:  # Показываем первые 10
                print(f"  - ID: {comp['id']}")
                print(f"    Название: {comp['name']}")
                print(f"    Срок сдачи (строка): {comp.get('completion_date_str', 'N/A')}")
                print(f"    Срок сдачи (дата): {comp['delivery_date']}")
                print(f"    Источник: {comp.get('source', 'неизвестно')}")
                print()
            if len(matching_complexes) > 10:
                print(f"  ... и еще {len(matching_complexes) - 10} ЖК")
                print()
        else:
            print("  (ЖК не найдены)")
            print()
        
        print("=" * 80)
        print()
    
    # 3. Итоговая статистика
    print("=" * 80)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    
    all_complex_ids = set()
    for quarter in quarters:
        matching_complexes = get_complexes_for_quarter(quarter['end_date'])
        for comp in matching_complexes:
            all_complex_ids.add(comp['id'])
    
    print(f"Всего уникальных ЖК во всех фильтрах: {len(all_complex_ids)}")
    print()
    
    # Статистика по кварталам
    print("Количество ЖК по каждому кварталу:")
    for quarter in quarters:
        matching_complexes = get_complexes_for_quarter(quarter['end_date'])
        print(f"  {quarter['label']}: {len(matching_complexes)} ЖК")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()

