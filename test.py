import logging
import pandas as pd
import re
import csv
from typing import Iterable, List, Optional, Sequence, Union, Dict, Any


logger = logging.getLogger(__name__)


SAMPLE_DATA: List[Dict[str, Any]] = [
    {
        "Категория": "Квартиры",
        "Название Avito": "1-к. квартира, 32,5 м², 4/12 эт.",
        "Название DomClick": "1-комн. квартира, 32.8 м², 4/12 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "2-к. квартира, 54,2 м², 5/16 эт.",
        "Название DomClick": "2-комн. квартира, 54.0 м², 5/16 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "3-к. квартира, 78,9 м², 12/25 эт.",
        "Название DomClick": "3-комн. квартира, 79.3 м², 12/25 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "4-к. квартира, 110,0 м², 7/14 эт.",
        "Название DomClick": "4-комн. квартира, 109.5 м², 7/14 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "1-к. квартира, 28,4 м², 2/9 эт.",
        "Название DomClick": "1-комн. студия, 28.0 м², 2/9 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "2-к. квартира, 65,1 м², 9/17 эт.",
        "Название DomClick": "2-комн. квартира, 65.4 м², 9/17 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "3-к. квартира, 90,3 м², 15/24 эт.",
        "Название DomClick": "3-комн. квартира, 89.9 м², 15/24 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "2-к. квартира, 47,0 м², 3/10 эт.",
        "Название DomClick": "2-комн. квартира, 46.7 м², 3/10 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "1-к. квартира, 40,6 м², 6/19 эт.",
        "Название DomClick": "1-комн. квартира, 40.2 м², 6/19 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "3-к. квартира, 72,4 м², 8/12 эт.",
        "Название DomClick": "3-комн. квартира, 72.0 м², 8/12 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "2-к. квартира, 51,8 м², 14/22 эт.",
        "Название DomClick": "2-комн. квартира, 52.1 м², 14/22 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "1-к. квартира, 36,7 м², 11/17 эт.",
        "Название DomClick": "1-комн. квартира, 37.0 м², 11/17 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "4-к. квартира, 135,2 м², 10/18 эт.",
        "Название DomClick": "4-комн. квартира, 134.6 м², 10/18 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "2-к. квартира, 58,3 м², 4/6 эт.",
        "Название DomClick": "2-комн. квартира, 58.7 м², 4/6 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "3-к. квартира, 84,5 м², 19/25 эт.",
        "Название DomClick": "3-комн. квартира, 84.1 м², 19/25 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "1-к. квартира, 29,9 м², 1/5 эт.",
        "Название DomClick": "1-комн. квартира, 30.2 м², 1/5 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "2-к. квартира, 60,0 м², 6/15 эт.",
        "Название DomClick": "2-комн. квартира, 60.4 м², 6/15 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "3-к. квартира, 95,8 м², 20/25 эт.",
        "Название DomClick": "3-комн. квартира, 96.5 м², 20/25 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "4-к. квартира, 142,0 м², 13/17 эт.",
        "Название DomClick": "4-комн. квартира, 141.5 м², 13/17 эт.",
    },
    {
        "Категория": "Квартиры",
        "Название Avito": "1-к. квартира, 34,1 м², 7/9 эт.",
        "Название DomClick": "1-комн. квартира, 34.4 м², 7/9 эт.",
    },
]


def parse_listing(text):
    """Извлекает ключевые параметры из текста объявления"""
    if pd.isna(text) or not isinstance(text, str):
        return (None, None, None, None)

    # Количество комнат (1-к., 1-комн. и т.д.)
    room_match = re.search(r'(\d+)\s*[-]?\s*(?:к\.|комн\.)', text)
    rooms = int(room_match.group(1)) if room_match else None

    # Площадь (22,8м², 57,5 м² и т.д.)
    area_match = re.search(r'(\d+[.,]?\d*)\s*м²', text)
    area = None
    if area_match:
        area_str = area_match.group(1).replace(',', '.')
        try:
            area = float(area_str)
        except:
            area = None

    # Этаж/общее количество этажей (1/27эт., 1/28 эт. и т.д.)
    floor_match = re.search(r'(\d+)/(\d+)\s*эт\.?', text)
    floor = total_floors = None
    if floor_match:
        try:
            floor = int(floor_match.group(1))
            total_floors = int(floor_match.group(2))
        except:
            pass

    return rooms, area, floor, total_floors


def _load_dataframe(input_data: Union[str, pd.DataFrame, Sequence[Dict[str, Any]]]) -> pd.DataFrame:
    if isinstance(input_data, str):
        logger.info("Чтение входного CSV-файла: %s", input_data)
        try:
            df = pd.read_csv(input_data, encoding='utf-8', on_bad_lines='skip')
        except Exception:
            logger.exception("Не удалось прочитать файл %s", input_data)
            raise
        logger.info("Прочитано %d строк", len(df))
        return df

    if isinstance(input_data, pd.DataFrame):
        logger.info("Получен DataFrame с %d строками", len(input_data))
        return input_data.copy()

    if isinstance(input_data, Sequence):
        df = pd.DataFrame(input_data)
        logger.info("Сформирован DataFrame из списка с %d строками", len(df))
        return df

    raise TypeError("input_data должен быть путём к файлу, DataFrame или списком словарей.")


def match_listings(
    input_data: Union[str, pd.DataFrame, Sequence[Dict[str, Any]]],
    output_file: Optional[str] = None,
) -> List[List[Optional[str]]]:
    """
    Сопоставляет объявления Avito и DomClick.
    :param input_data: путь к CSV, DataFrame или список словарей с данными.
    :param output_file: опциональный путь к CSV-файлу с результатами.
    :return: список результатов сопоставления.
    """

    df = _load_dataframe(input_data)

    # Проверка наличия нужных колонок
    required_cols = ['Категория', 'Название Avito', 'Название DomClick']
    if not all(col in df.columns for col in required_cols):
        logger.error("Во входных данных отсутствуют необходимые столбцы. Ожидались: %s", required_cols)
        raise ValueError(f"Данные должны содержать колонки: {required_cols}")

    # Парсинг данных
    logger.debug("Начало парсинга колонок объявлений")
    df['avito_parsed'] = df['Название Avito'].apply(parse_listing)
    df['domclick_parsed'] = df['Название DomClick'].apply(parse_listing)
    logger.debug("Парсинг завершён")

    # Список для результатов
    results = []

    # Сравнение каждого объявления Avito со всеми объявлениями DomClick
    for _, avito_row in df.iterrows():
        avito_name = avito_row['Название Avito']
        a_rooms, a_area, a_floor, a_total = avito_row['avito_parsed']

        best_match = None
        best_score = float('inf')

        for _, dc_row in df.iterrows():
            dc_name = dc_row['Название DomClick']
            d_rooms, d_area, d_floor, d_total = dc_row['domclick_parsed']

            # Пропускаем, если нет данных или не совпадает количество комнат
            if a_rooms is None or d_rooms is None or a_rooms != d_rooms:
                continue

            # Рассчитываем разницу по площади
            area_diff = abs(a_area - d_area) if a_area and d_area else float('inf')
            # Рассчитываем разницу по этажу
            floor_diff = abs(a_floor - d_floor) if a_floor and d_floor else float('inf')

            # Пропускаем, если параметры не извлечены
            if area_diff == float('inf') or floor_diff == float('inf'):
                continue

            # Оценка совпадения (меньше = лучше)
            score = area_diff * 0.5 + floor_diff * 1.0

            if score < best_score:
                best_score = score
                best_match = dc_name

        if best_match is None:
            logger.debug("Не найдено совпадение для объявления: %s", avito_name)
        else:
            logger.debug(
                "Лучшее совпадение для %s -> %s (оценка %.4f)",
                avito_name,
                best_match,
                best_score,
            )

        best_score_str = f"{best_score:.2f}" if best_score != float('inf') else "inf"
        results.append([avito_name, best_match, best_score_str])

    if output_file:
        logger.info("Запись результатов в файл: %s", output_file)
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Название Avito', 'Название DomClick (сопоставленное)', 'Оценка совпадения'])
            writer.writerows(results)
        logger.info("Результаты записаны")

    return results

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger.info("Запуск сопоставления объявлений на примере данных")
    match_results = match_listings(SAMPLE_DATA)
    for avito_name, matched_name, score in match_results:
        logger.info("Результат: %s -> %s (оценка %s)", avito_name, matched_name, score)
    logger.info("Сопоставление завершено")