# План миграции на новый формат данных unified_houses

## Анализ новой структуры данных

### Структура записи:
```json
{
  "_id": ObjectId,
  "name": "ЖК «8 NEBO»",
  "city": "Уфа",
  "district": "Октябрьский район",
  "street": "Лесотехникума",
  "address_full": "г. Уфа, р-он Октябрьский район, ул. Лесотехникума",
  "development": {
    "name": "ЖК «8 NEBO»",
    "address": "...",
    "photos": [...],
    "parameters": {...}
  },
  "apartment_types": {
    "2": {
      "apartments": [
        {
          "title": "2-комн. квартира, 57,03 м²в ЖК «8 NEBO»",
          "rooms": 2,  // int
          "floorMin": 12,  // int
          "floorMax": 32,  // int
          "area": "57.03",  // str
          "totalArea": 57.03,  // float
          "livingArea": "15.7 м²",  // str
          "kitchenArea": "22.7 м²",  // str
          "price": "10 864 200 ₽",  // str
          "url": "...",
          "images_apartment": [...],
          "houseStatus": "Не сдан",
          "decorationType": "Предчистовая",
          "housingType": "Новостройка",
          "ceilingHeight": "2,7 м",
          "houseType": "Монолитно-кирпичный",
          "dealType": "Свободная продажа",
          "decoration": {...}
        }
      ]
    }
  }
}
```

### Ключевые изменения:
1. **Квартиры хранятся в `apartment_types`** - словарь, где ключ = количество комнат (строка "1", "2", "3", "4")
2. **Поля квартиры**:
   - `rooms`: int (вместо строки)
   - `floorMin`, `floorMax`: int (вместо строки "2-25 этаж")
   - `area`: str (например, "57.03")
   - `totalArea`: float (57.03)
   - `livingArea`: str (например, "15.7 м²")
   - `kitchenArea`: str (например, "22.7 м²")
   - `price`: str (например, "10 864 200 ₽")
   - `images_apartment`: массив (вместо `image`)

---

## План замены по файлам

### 1. Backend API endpoints

#### 1.1. `main/api/manual_matching_api.py`

**Функция: `get_client_catalog_apartments` (строки 3687-3944)**

**Текущее состояние**: Частично поддерживает новую структуру, но:
- Извлекает `rooms` из `title` вместо использования поля `rooms` (int)
- Не использует `floorMin`/`floorMax`, парсит из `title`
- Не использует `totalArea` (float), парсит из `title`
- Не использует `images_apartment`, использует `image`

**Изменения**:
```python
# Вместо парсинга из title:
rooms = apt.get('rooms', '')  # Уже int, преобразуем в строку
if isinstance(rooms, int):
    rooms = str(rooms)

# Используем floorMin/floorMax:
floor_min = apt.get('floorMin')
floor_max = apt.get('floorMax')
if floor_min is not None and floor_max is not None:
    floor = f"{floor_min}-{floor_max}"
elif floor_min is not None:
    floor = str(floor_min)
else:
    floor = apt.get('floor', '')  # Fallback

# Используем totalArea:
area = apt.get('totalArea') or apt.get('area', '')
if isinstance(area, (int, float)):
    area = str(area)

# Используем images_apartment:
layout_photos = apt.get('images_apartment', []) or apt.get('image', [])
```

**Функция: `get_complex_by_id` (строки 4133-4200)**

**Текущее состояние**: Уже поддерживает новую структуру, но нужно убедиться, что возвращает правильные данные.

**Изменения**: Минимальные, возможно добавить дополнительные поля из новой структуры.

---

#### 1.2. `main/views.py`

**Функция: `apartments_api` (строки 785-1146)**

**Текущее состояние**: Частично поддерживает новую структуру, но:
- Фильтрация по комнатам использует `apt_type` (ключ словаря), что правильно
- Не использует `rooms` (int) из объекта квартиры
- Не использует `floorMin`/`floorMax` для фильтрации по этажам
- Не использует `totalArea` (float) для фильтрации по площади
- Парсит цену из строки вместо использования числового значения

**Изменения**:
```python
# Фильтрация по комнатам - уже правильно использует apt_type
# Но можно добавить проверку rooms (int) как fallback:
if rooms:
    selected_rooms = [r.strip() for r in rooms.split(',') if r.strip()]
    apt_rooms = apt.get('rooms')
    if isinstance(apt_rooms, int):
        apt_rooms_str = str(apt_rooms)
    else:
        apt_rooms_str = str(apt_rooms) if apt_rooms else ''
    
    # Проверяем и по типу, и по полю rooms
    if apt_type not in selected_rooms and apt_rooms_str not in selected_rooms:
        continue

# Фильтрация по площади - используем totalArea:
area = apt.get('totalArea') or apt.get('area', '')
if isinstance(area, str):
    # Парсим строку "57.03" или "57,03 м²"
    area = area.replace(' м²', '').replace(',', '.').strip()
try:
    area_val = float(area) if area else 0
except (ValueError, TypeError):
    area_val = 0

# Фильтрация по цене - парсим из строки "10 864 200 ₽":
price = apt.get('price', '')
price_num = None
if price:
    # Убираем пробелы, ₽, руб
    price_clean = str(price).replace(' ', '').replace('₽', '').replace('руб', '').strip()
    try:
        price_num = float(price_clean)
    except (ValueError, TypeError):
        pass
```

**Добавить фильтрацию по этажам** (если нужно):
```python
floor_from = request.GET.get('floor_from', '').strip()
floor_to = request.GET.get('floor_to', '').strip()

if floor_from or floor_to:
    floor_min = apt.get('floorMin')
    floor_max = apt.get('floorMax')
    if floor_min is None or floor_max is None:
        continue  # Пропускаем, если нет данных об этажах
    
    if floor_from:
        try:
            if floor_max < int(floor_from):
                continue
        except (ValueError, TypeError):
            pass
    
    if floor_to:
        try:
            if floor_min > int(floor_to):
                continue
        except (ValueError, TypeError):
            pass
```

---

#### 1.3. `main/view_modules/apartment_views.py`

**Функция: `apartment_detail` (строки 50-610)**

**Текущее состояние**: Частично поддерживает новую структуру, но:
- Парсит `rooms` из `title` вместо использования поля `rooms` (int)
- Парсит `floor` из `title` вместо использования `floorMin`/`floorMax`
- Парсит `area` из `title` вместо использования `totalArea`
- Использует `image` вместо `images_apartment`

**Изменения**:
```python
# Используем rooms (int):
rooms = apt.get('rooms', '')
if isinstance(rooms, int):
    rooms = str(rooms)
elif not rooms and title:
    # Fallback: парсим из title
    if '-комн' in title:
        rooms = title.split('-комн')[0].strip()

# Используем floorMin/floorMax:
floor_min = apt.get('floorMin')
floor_max = apt.get('floorMax')
if floor_min is not None and floor_max is not None:
    if floor_min == floor_max:
        floor = str(floor_min)
    else:
        floor = f"{floor_min}-{floor_max}"
elif floor_min is not None:
    floor = str(floor_min)
else:
    floor = apt.get('floor', '')
    if not floor and title:
        # Fallback: парсим из title
        floor_range_match = re.search(r'(\d+)-(\d+)\s*этаж', title)
        if floor_range_match:
            floor = f"{floor_range_match.group(1)}-{floor_range_match.group(2)}"

# Используем totalArea:
total_area = apt.get('totalArea') or apt.get('area', '')
if isinstance(total_area, (int, float)):
    total_area = str(total_area)
elif not total_area and title:
    # Fallback: парсим из title
    area_match = re.search(r'(\d+[,.]?\d*)\s*м²', title)
    if area_match:
        total_area = area_match.group(1).replace(',', '.')

# Используем images_apartment:
layout_photos = apt.get('images_apartment', []) or apt.get('image', [])
if isinstance(layout_photos, str):
    layout_photos = [layout_photos] if layout_photos else []

# Используем livingArea и kitchenArea:
living_area = apt.get('livingArea', '')
kitchen_area = apt.get('kitchenArea', '')
```

---

#### 1.4. `main/view_modules/catalog_views.py`

**Функция: `detail` (строки 476-955)**

**Текущее состояние**: Нужно проверить, правильно ли обрабатывает новую структуру.

**Изменения**: Аналогично `apartment_views.py` - использовать прямые поля вместо парсинга из title.

---

### 2. Frontend JavaScript

#### 2.1. `templates/main/client_catalog.html`

**Текущее состояние**: Фильтрация работает на клиенте, использует данные из API.

**Изменения**:
- Убедиться, что API возвращает правильные данные (см. раздел 1.1)
- Обновить функцию `applyFilters` для работы с новыми полями:
  ```javascript
  // rooms уже приходит как число или строка из API
  // Проверяем оба варианта
  const aptRooms = apt.rooms;
  const roomsStr = typeof aptRooms === 'number' ? String(aptRooms) : String(aptRooms || '');
  
  // area используем totalArea или area
  const area = apt.totalArea || apt.area || '';
  const areaNum = parseFloat(String(area).replace(/[^\d.,]/g, '').replace(',', '.')) || 0;
  
  // price парсим из строки "10 864 200 ₽"
  const priceStr = apt.price || '';
  const priceNum = parseFloat(priceStr.replace(/\s/g, '').replace(/₽/g, '').replace(/руб/g, '').replace(/,/g, '')) || 0;
  ```

---

#### 2.2. `templates/main/favorites.html`

**Текущее состояние**: Использует `normalizeRooms` для извлечения комнат из title.

**Изменения**:
- Обновить `normalizeRooms` для использования поля `rooms` (int):
  ```javascript
  function normalizeRooms(apt) {
      // Сначала проверяем поле rooms (int)
      let rooms = apt.rooms;
      if (typeof rooms === 'number') {
          return String(rooms);
      }
      
      // Fallback: парсим из title
      const title = apt.title || '';
      if (title.includes('-комн')) {
          rooms = title.split('-комн')[0].trim();
      } else if (title.includes('-к.')) {
          rooms = title.split('-к.')[0].trim();
      } else if (title.includes(' ком.')) {
          rooms = title.split(' ком.')[0].trim();
      } else {
          const match = title.match(/^(\d+)/);
          if (match) {
              rooms = match[1];
          }
      }
      
      const roomsMatch = String(rooms).match(/^(\d+)/);
      return roomsMatch ? roomsMatch[1] : '';
  }
  ```

- Обновить фильтрацию по площади и цене аналогично `client_catalog.html`

---

### 3. Дополнительные улучшения

#### 3.1. Добавить фильтрацию по новым полям

**В `apartments_api` и `get_client_catalog_apartments`**:
- Фильтрация по `floorMin`/`floorMax` (диапазон этажей)
- Фильтрация по `kitchenArea` (площадь кухни)
- Фильтрация по `livingArea` (жилая площадь)
- Фильтрация по `decorationType` (тип отделки)
- Фильтрация по `houseType` (тип дома)

**Пример для API**:
```python
# В apartments_api добавить параметры:
kitchen_area_from = request.GET.get('kitchen_area_from', '').strip()
kitchen_area_to = request.GET.get('kitchen_area_to', '').strip()
living_area_from = request.GET.get('living_area_from', '').strip()
living_area_to = request.GET.get('living_area_to', '').strip()
decoration_type = request.GET.get('decoration_type', '').strip()
house_type = request.GET.get('house_type', '').strip()

# Фильтрация:
if kitchen_area_from or kitchen_area_to:
    kitchen_area_str = apt.get('kitchenArea', '').replace(' м²', '').replace(',', '.').strip()
    try:
        kitchen_area_val = float(kitchen_area_str) if kitchen_area_str else 0
        if kitchen_area_from and kitchen_area_val < float(kitchen_area_from):
            continue
        if kitchen_area_to and kitchen_area_val > float(kitchen_area_to):
            continue
    except (ValueError, TypeError):
        pass

if living_area_from or living_area_to:
    living_area_str = apt.get('livingArea', '').replace(' м²', '').replace(',', '.').strip()
    try:
        living_area_val = float(living_area_str) if living_area_str else 0
        if living_area_from and living_area_val < float(living_area_from):
            continue
        if living_area_to and living_area_val > float(living_area_to):
            continue
    except (ValueError, TypeError):
        pass

if decoration_type:
    apt_decoration = apt.get('decorationType', '')
    if apt_decoration != decoration_type:
        continue

if house_type:
    apt_house_type = apt.get('houseType', '')
    if apt_house_type != house_type:
        continue
```

---

#### 3.2. Обновить отображение данных

**В шаблонах** (`apartment_detail.html`, `client_catalog.html`, `favorites.html`):
- Отображать `livingArea` и `kitchenArea` отдельно
- Отображать `floorMin`-`floorMax` вместо парсинга из title
- Отображать `decorationType`, `houseType`, `ceilingHeight` и другие поля

---

### 4. Порядок выполнения миграции

1. **Этап 1: Backend API** (приоритет: высокий)
   - Обновить `get_client_catalog_apartments` в `main/api/manual_matching_api.py`
   - Обновить `apartments_api` в `main/views.py`
   - Обновить `apartment_detail` в `main/view_modules/apartment_views.py`
   - Обновить `get_complex_by_id` в `main/api/manual_matching_api.py` (если нужно)

2. **Этап 2: Frontend JavaScript** (приоритет: высокий)
   - Обновить `client_catalog.html` - функции фильтрации
   - Обновить `favorites.html` - функции фильтрации и `normalizeRooms`

3. **Этап 3: Дополнительные фильтры** (приоритет: средний)
   - Добавить фильтрацию по `floorMin`/`floorMax`
   - Добавить фильтрацию по `kitchenArea` и `livingArea`
   - Добавить фильтрацию по `decorationType` и `houseType`

4. **Этап 4: Обновление отображения** (приоритет: низкий)
   - Обновить шаблоны для отображения новых полей
   - Добавить UI для новых фильтров (если нужно)

5. **Этап 5: Тестирование** (приоритет: высокий)
   - Протестировать все API endpoints
   - Протестировать фильтрацию на клиенте
   - Протестировать отображение данных

---

### 5. Важные замечания

1. **Обратная совместимость**: Код должен работать как со старым, так и с новым форматом (проверка `is_new_structure`).

2. **Парсинг из title**: Оставить как fallback на случай, если в новой структуре нет нужных полей.

3. **Типы данных**: 
   - `rooms`: может быть int или str - обрабатывать оба случая
   - `area`/`totalArea`: может быть str или float - обрабатывать оба случая
   - `price`: всегда str в формате "10 864 200 ₽" - парсить

4. **Поля изображений**: 
   - Старое: `image` (строка или массив)
   - Новое: `images_apartment` (массив)
   - Использовать: `apt.get('images_apartment', []) or apt.get('image', [])`

5. **Поля этажей**:
   - Старое: `floor` (строка "2-25 этаж" или "3/15 эт.")
   - Новое: `floorMin` (int), `floorMax` (int)
   - Использовать новые поля, fallback на парсинг из `floor` или `title`

---

### 6. Файлы для изменения

**Backend**:
- `main/api/manual_matching_api.py` (2 функции)
- `main/views.py` (1 функция)
- `main/view_modules/apartment_views.py` (1 функция)
- `main/view_modules/catalog_views.py` (1 функция, проверить)

**Frontend**:
- `templates/main/client_catalog.html` (JavaScript)
- `templates/main/favorites.html` (JavaScript)
- `templates/main/apartment_detail.html` (HTML, если нужно добавить новые поля)

---

## Резюме

Основная задача - заменить парсинг данных из `title` на использование прямых полей из новой структуры:
- `rooms` (int) вместо парсинга из title
- `floorMin`/`floorMax` (int) вместо парсинга из title
- `totalArea` (float) вместо парсинга из title
- `images_apartment` (массив) вместо `image`
- `livingArea`, `kitchenArea` (str) - новые поля

Все изменения должны сохранять обратную совместимость со старым форматом.

