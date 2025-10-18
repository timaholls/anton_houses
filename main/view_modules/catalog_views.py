"""Views для каталога жилых комплексов и недвижимости"""
import json
from django.shortcuts import render
from django.http import Http404, JsonResponse
from django.core.paginator import Paginator
from bson import ObjectId
from ..services.mongo_service import get_mongo_connection, get_residential_complexes_from_mongo
from ..utils import get_video_thumbnail
from ..s3_service import PLACEHOLDER_IMAGE_URL


def catalog(request):
    """Каталог ЖК - данные из MongoDB"""
    page = request.GET.get('page', 1)

    # Получаем параметры фильтрации
    rooms = request.GET.get('rooms', '')
    city = request.GET.get('city', '')
    district = request.GET.get('district', '')
    street = request.GET.get('street', '')
    area_from = request.GET.get('area_from', '')
    area_to = request.GET.get('area_to', '')
    price_from = request.GET.get('price_from', '')
    price_to = request.GET.get('price_to', '')
    delivery_date = request.GET.get('delivery_date', '')
    has_offers = request.GET.get('has_offers', '')
    sort = request.GET.get('sort', 'price_asc')

    # Собираем фильтры для MongoDB
    filters = {}
    if city:
        filters['city'] = city
    if district:
        filters['district'] = district

    # Получаем данные из MongoDB
    complexes = get_residential_complexes_from_mongo(filters=filters, sort_by=sort)

    # Применяем дополнительные фильтры
    filters_applied = False
    if rooms or city or district or street or area_from or area_to or price_from or price_to or delivery_date or has_offers:
        filters_applied = True

        filtered_complexes = []
        for complex_data in complexes:
            # Фильтр по цене
            if price_from and complex_data.get('price', {}).get('min'):
                if float(complex_data['price']['min']) < float(price_from):
                    continue
            if price_to and complex_data.get('price', {}).get('min'):
                if float(complex_data['price']['min']) > float(price_to):
                    continue
            
            # Фильтр по комнатам
            if rooms and complex_data.get('apartment_types'):
                has_matching_rooms = False
                for apt_type in complex_data['apartment_types'].values():
                    if apt_type.get('rooms') == rooms:
                        has_matching_rooms = True
                        break
                if not has_matching_rooms:
                    continue
            
            filtered_complexes.append(complex_data)
        
        complexes = filtered_complexes

    # Пагинация по 9 элементов
    paginator = Paginator(complexes, 9)
    page_obj = paginator.get_page(page)

    # Получаем уникальные города для фильтра из MongoDB
    cities = []
    try:
        db = get_mongo_connection()
        collection = db['residential_complexes']
        cities = collection.distinct('address.city')
    except Exception:
        cities = []

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': cities,
        'rooms_choices': [('1', '1-комнатная'), ('2', '2-комнатная'), ('3', '3-комнатная'), ('4', '4-комнатная'), ('5+', '5+ комнат')],
        'filters': {
            'rooms': rooms,
            'city': city,
            'district': district,
            'street': street,
            'area_from': area_from,
            'area_to': area_to,
            'price_from': price_from,
            'price_to': price_to,
            'delivery_date': delivery_date,
            'has_offers': has_offers,
            'sort': sort,
        },
        'filters_applied': filters_applied,
        'dataset_type': 'newbuild'
    }
    return render(request, 'main/catalog.html', context)


def detail(request, complex_id):
    """Детальная страница ЖК (MongoDB или SQL)"""
    
    # Получаем ипотечные программы из MongoDB (унифицировано)
    def get_mortgage_programs_from_mongo():
        try:
            db = get_mongo_connection()
            docs = list(db['mortgage_programs'].find({'is_active': True}).sort('rate', 1))
            class P:
                def __init__(self, name, rate):
                    self.name, self.rate = name, rate
            return [P(d.get('name',''), float(d.get('rate', 0))) for d in docs]
        except Exception:
            return []
    mortgage_programs = get_mortgage_programs_from_mongo()
    
    # Проверяем, является ли ID MongoDB ObjectId (24 hex символа)
    is_mongodb_id = len(str(complex_id)) == 24 and all(c in '0123456789abcdef' for c in str(complex_id).lower())
    
    if is_mongodb_id:
        # ============ MONGODB VERSION ============
        try:
            db = get_mongo_connection()
            unified_col = db['unified_houses']
            
            # Получаем запись по ID
            record = unified_col.find_one({'_id': ObjectId(complex_id)})
            
            if not record:
                raise Http404("ЖК не найден")
            
            # Проверяем структуру: старая (с вложенностью) или новая (упрощенная)
            is_new_structure = 'development' in record and 'avito' not in record
            
            # Инициализируем переменные для обеих структур
            avito_data = {}
            domclick_data = {}
            
            if is_new_structure:
                # === НОВАЯ УПРОЩЕННАЯ СТРУКТУРА ===
                development = record.get('development', {})
                
                # Основные данные
                name = development.get('name', 'Без названия')
                address = development.get('address', '').split('/')[0].strip()
                price_range = development.get('price_range', '')
                
                # Фото ЖК
                photos = development.get('photos', [])
                
                # Координаты напрямую в корне
                latitude = record.get('latitude')
                longitude = record.get('longitude')
                
                # Параметры ЖК
                parameters = development.get('parameters', {})
                korpuses = development.get('korpuses', [])
                
                # Типы квартир уже в упрощенной структуре
                apartment_types_data = record.get('apartment_types', {})
                
            else:
                # === СТАРАЯ СТРУКТУРА (для обратной совместимости) ===
                avito_data = record.get('avito', {})
                domclick_data = record.get('domclick', {})
                domrf_data = record.get('domrf', {})
                
                avito_dev = avito_data.get('development', {}) if avito_data else {}
                domclick_dev = domclick_data.get('development', {}) if domclick_data else {}
                
                # Основные данные
                name = avito_dev.get('name') or domclick_dev.get('complex_name') or domrf_data.get('name', 'Без названия')
                address = avito_dev.get('address', '').split('/')[0].strip() if avito_dev.get('address') else ''
                price_range = avito_dev.get('price_range', '')
                
                # Фото ЖК из domclick
                photos = domclick_dev.get('photos', [])
                
                # Координаты
                latitude = domrf_data.get('latitude')
                longitude = domrf_data.get('longitude')
                
                # Параметры ЖК
                parameters = avito_dev.get('parameters', {})
                korpuses = avito_dev.get('korpuses', [])
            
            # Обработка типов квартир в зависимости от структуры
            apartment_variants = []
            apartment_types_list = []
            
            if is_new_structure:
                # === НОВАЯ СТРУКТУРА: данные уже объединены ===
                print(f"🔍 DEBUG: Processing NEW structure for complex {complex_id}")
                print(f"🔍 DEBUG: apartment_types_data keys = {list(apartment_types_data.keys())}")
                
                for apt_type, apt_data in apartment_types_data.items():
                    apartments = apt_data.get('apartments', [])
                    print(f"🔍 DEBUG: Processing apt_type={apt_type}, apartments count={len(apartments)}")
                    
                    if apartments:
                        apartment_types_list.append(apt_type)
                        
                        for apt in apartments:
                            # Получаем все фото планировки - это уже массив!
                            layout_photos = apt.get('image', [])
                            print(f"🔍 DEBUG: apt_type={apt_type}, apt_data={apt}")
                            print(f"🔍 DEBUG: layout_photos from apt.get('image') = {layout_photos}")
                            print(f"🔍 DEBUG: layout_photos type = {type(layout_photos)}")
                            
                            # Если это не массив, а строка - преобразуем в массив
                            if isinstance(layout_photos, str):
                                layout_photos = [layout_photos] if layout_photos else []
                                print(f"🔍 DEBUG: converted string to list: {layout_photos}")
                            
                            apartment_variants.append({
                                'type': apt_type,
                                'title': apt.get('title', ''),
                                'price': apt.get('price', ''),
                                'price_per_square': apt.get('pricePerSquare', ''),
                                'completion_date': apt.get('completionDate', ''),
                                'image': layout_photos[0] if layout_photos else '',  # Первое фото для превью
                                'url': apt.get('url', ''),
                                'layout_photos': layout_photos  # Все фото для галереи
                            })
                            print(f"🔍 DEBUG: final layout_photos = {layout_photos}")
            
            else:
                # === СТАРАЯ СТРУКТУРА: нужно объединять данные ===
                print(f"🔍 DEBUG: Processing OLD structure for complex {complex_id}")
                print(f"🔍 DEBUG: This complex has OLD structure - should be updated by script!")
                avito_apartment_types = avito_data.get('apartment_types', {})
                domclick_apartment_types = domclick_data.get('apartment_types', {})
                
                for apt_type, apt_data in avito_apartment_types.items():
                    apartments = apt_data.get('apartments', [])
                    
                    # Добавляем тип в список если есть квартиры
                    if apartments and apt_type not in apartment_types_list:
                        apartment_types_list.append(apt_type)
                    
                    # Ищем фото планировок из domclick для этого типа
                    domclick_photos = []
                    if apt_type in domclick_apartment_types:
                        dc_apartments = domclick_apartment_types[apt_type].get('apartments', [])
                        for dc_apt in dc_apartments:
                            domclick_photos.extend(dc_apt.get('photos', []))
                    
                    for apt in apartments:
                        apartment_variants.append({
                            'type': apt_type,
                            'title': apt.get('title', ''),
                            'price': apt.get('price', ''),
                            'price_per_square': apt.get('pricePerSquare', ''),
                            'completion_date': apt.get('completionDate', ''),
                            'image': apt.get('image', {}).get('128x96', ''),
                            'url': apt.get('urlPath', ''),
                            'layout_photos': domclick_photos[:5]  # Первые 5 фото планировок
                        })
            
            # Формируем контекст для MongoDB версии
            # Получаем акции для этого ЖК
            complex_offers = []
            try:
                promotions_col = db['promotions']
                offers_data = list(promotions_col.find({
                    'complex_id': ObjectId(complex_id),
                    'is_active': True
                }).sort('created_at', -1))
                
                # Создаем адаптеры для совместимости с шаблонами
                for offer_data in offers_data:
                    class _Img: pass
                    class _MainImg: pass
                    class _RC: pass
                    class _Offer: pass
                    
                    offer = _Offer()
                    offer.id = str(offer_data.get('_id'))
                    offer.title = offer_data.get('title', 'Акция')
                    # Убираем описание
                    offer.description = ''
                    offer.expires_at = offer_data.get('expires_at')
                    
                    # residential_complex.name
                    rc = _RC()
                    rc.name = name  # Используем название ЖК из записи
                    offer.residential_complex = rc
                    
                    # get_main_image.image.url - используем изображение из ЖК
                    main = _MainImg()
                    img = _Img()
                    # Берем первое фото из ЖК для акции
                    if photos:
                        img.url = photos[0]
                    else:
                        img.url = PLACEHOLDER_IMAGE_URL
                    main.image = img
                    offer.get_main_image = main
                    
                    complex_offers.append(offer)
            except Exception as e:
                print(f"Ошибка получения акций: {e}")
                complex_offers = []
            
            # Получаем видеообзоры для этого ЖК
            videos = []
            try:
                videos_col = db['residential_videos']
                videos_data = list(videos_col.find({
                    'complex_id': ObjectId(complex_id)
                }).sort('created_at', -1))
                
                # Создаем адаптеры для совместимости с шаблонами
                for video_data in videos_data:
                    class _Video: pass
                    video = _Video()
                    video.id = str(video_data.get('_id'))
                    video.title = video_data.get('title', '')
                    video.video_url = video_data.get('url', '')
                    video.created_at = video_data.get('created_at')
                    # Добавляем превью для видео
                    video.thumbnail_url = get_video_thumbnail(video_data.get('url', ''))
                    videos.append(video)
            except Exception as e:
                print(f"Ошибка получения видео: {e}")
                videos = []

            context = {
                'complex': {
                    'id': str(record['_id']),
                    'name': name,
                    'address': address,
                    'city': 'Уфа',
                    'price_range': price_range,
                    'photos': photos,
                    'photos_json': json.dumps(photos),
                    'latitude': latitude,
                    'longitude': longitude,
                    'parameters': parameters,
                    'korpuses': korpuses,
                    'apartment_variants': apartment_variants,
                    'apartment_variants_json': json.dumps(apartment_variants),
                    'apartment_types': apartment_types_list,
                    'total_apartments': avito_data.get('total_apartments', 0),
                    'avito_url': avito_data.get('url', ''),
                    'domclick_url': domclick_data.get('url', ''),
                    # Ход строительства из объединенной записи (скопирован из DomClick)
                    'construction_progress': record.get('construction_progress', {}),
                },
                'complex_offers': complex_offers,
                'videos': videos,
                'mortgage_programs': mortgage_programs,
                'is_mongodb': True,
                'is_secondary': False,
            }
            
            # Подтягиваем данные агента, если закреплен
            agent = None
            if record.get('agent_id'):
                try:
                    agent = db['employees'].find_one({'_id': record['agent_id'], 'is_active': True})
                    if agent:
                        agent['id'] = str(agent.get('_id'))
                except Exception:
                    agent = None
            context['agent'] = agent
            return render(request, 'main/detail.html', context)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Http404(f"Ошибка загрузки ЖК: {str(e)}")
    
    else:
        # Для числовых ID возвращаем 404, так как все данные теперь в MongoDB
        raise Http404("ЖК не найден. Используйте MongoDB ID.")


def secondary_detail_mongo(request, complex_id: str):
    """Детальная страница объекта вторичной недвижимости из MongoDB"""
    try:
        from bson import ObjectId
        
        # Подключение к MongoDB
        db = get_mongo_connection()
        collection = db['secondary_properties']
        
        # Получаем объект по ID
        obj_id = ObjectId(complex_id)
        doc = collection.find_one({'_id': obj_id})
        
        if not doc:
            raise Http404("Объект не найден")
        
        # Подтягиваем агента, если закреплен
        agent = None
        if doc.get('agent_id'):
            try:
                agent = db['employees'].find_one({'_id': doc['agent_id'], 'is_active': True})
            except Exception:
                agent = None

        # Создаем адаптер для совместимости с шаблоном
        class SecondaryAdapter:
            def __init__(self, data):
                self._data = data
                self.name = data.get('name', '')
                self.price_from = data.get('price', 0)
                self.city = data.get('city', '')
                self.district = data.get('district', '')
                self.street = data.get('street', '')
                self.commute_time = data.get('commute_time', '')
                self.area_from = data.get('area', 0)
                self.area_to = data.get('area', 0)
                self.developer = 'Собственник'
                self.total_apartments = 1  # Для совместимости с шаблоном
                self.completion_start = ''
                self.completion_end = ''
                self.has_completed = True
                self.get_house_class_display = lambda: ''
                self.get_house_type_display = lambda: self._get_house_type_display()
                self.get_finishing_display = lambda: self._get_finishing_display()
                self.description = data.get('description', '')
                self.photos = data.get('photos', [])
                self.rooms = data.get('rooms', '')
                self.total_floors = data.get('total_floors', '')
                self.finishing = data.get('finishing', '')
                
            def _get_house_type_display(self):
                house_type = self._data.get('house_type', '')
                house_types = {
                    'apartment': 'Квартира',
                    'house': 'Дом',
                    'cottage': 'Коттедж',
                    'townhouse': 'Таунхаус',
                    'commercial': 'Коммерческое помещение',
                    'room': 'Комната',
                    'studio': 'Студия'
                }
                return house_types.get(house_type, house_type)
            
            def _get_finishing_display(self):
                finishing = self._data.get('finishing', '')
                finishing_types = {
                    'without': 'Без отделки',
                    'rough': 'Черновая отделка',
                    'white_box': 'Белая коробка',
                    'full': 'Полная отделка',
                    'designer': 'Дизайнерская отделка'
                }
                return finishing_types.get(finishing, finishing)
            
            def get_main_image(self):
                if self.photos:
                    class ImageAdapter:
                        def __init__(self, photo_path):
                            self.image = type('obj', (object,), {'url': photo_path})()
                    return ImageAdapter(self.photos[0])
                return None
            
            def get_all_images(self):
                return self.photos
            
            def get_catalog_images(self):
                # Возвращаем адаптеры для всех фото для совместимости с шаблоном
                if not self.photos:
                    return []
                
                class CatalogImageAdapter:
                    def __init__(self, photo_path):
                        self.image = type('obj', (object,), {'url': photo_path})()
                
                return [CatalogImageAdapter(photo) for photo in self.photos]
            
            def get_videos(self):
                return []  # Вторичка не имеет видео
        
        complex_obj = SecondaryAdapter(doc)
        
        # Получаем похожие объекты (первые 3 из той же категории)
        similar_filter = {}
        if doc.get('rooms'):
            similar_filter['rooms'] = doc['rooms']
        if doc.get('city'):
            similar_filter['city'] = doc['city']
        
        similar_cursor = collection.find(similar_filter).limit(3)
        similar_objects = []
        for similar_doc in similar_cursor:
            if str(similar_doc['_id']) != complex_id:  # Исключаем текущий объект
                similar_objects.append(SecondaryAdapter(similar_doc))

        return render(request, 'main/detail.html', {
            'complex': complex_obj,
            'similar_complexes': similar_objects,
        'is_secondary': True,
        'mortgage_programs': [],
            'videos': [],
            'agent': agent,
        })
    except Exception as e:
        raise Http404(f"Ошибка загрузки объекта: {str(e)}")


def secondary_detail(request, pk: int):
    """Legacy функция - перенаправляет на MongoDB версию"""
    raise Http404("Используйте MongoDB ID для просмотра объектов вторичной недвижимости")


# Быстрые ссылки каталога
def catalog_completed(request):
    """Сданные ЖК - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'status': 'completed'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Сданные ЖК',
        'page_description': 'Готовые к заселению жилые комплексы'
    }
    return render(request, 'main/catalog.html', context)


def catalog_construction(request):
    """Строящиеся ЖК - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'status': 'construction'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Строящиеся ЖК',
        'page_description': 'Жилые комплексы в стадии строительства'
    }
    return render(request, 'main/catalog.html', context)


def catalog_economy(request):
    """Эконом-класс - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'house_class': 'economy'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Эконом-класс',
        'page_description': 'Доступное жилье эконом-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_comfort(request):
    """Комфорт-класс - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'house_class': 'comfort'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Комфорт-класс',
        'page_description': 'Жилые комплексы комфорт-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_premium(request):
    """Премиум-класс - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'house_class': 'premium'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Премиум-класс',
        'page_description': 'Жилые комплексы премиум-класса'
    }
    return render(request, 'main/catalog.html', context)


def catalog_finished(request):
    """С отделкой - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'finishing': 'finished'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'С отделкой',
        'page_description': 'Квартиры с готовой отделкой'
    }
    return render(request, 'main/catalog.html', context)


def catalog_unfinished(request):
    """Без отделки - данные из MongoDB"""
    page = request.GET.get('page', 1)
    
    # Получаем данные из MongoDB
    filters = {'finishing': 'unfinished'}
    complexes = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(complexes, 10)
    page_obj = paginator.get_page(page)

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'projects': [],  # Можно получить из MongoDB если нужно
        'house_types': [],  # Можно получить из MongoDB если нужно
        'filters': {},
        'filters_applied': True,
        'page_title': 'Без отделки',
        'page_description': 'Квартиры без отделки'
    }
    return render(request, 'main/catalog.html', context)


def catalog_landing(request, slug):
    db = get_mongo_connection()
    landing = db['catalog_landings'].find_one({'slug': slug, 'is_active': True})
    
    if not landing:
        raise Http404("Страница не найдена")

    # Базовый queryset в зависимости от типа
    if landing['kind'] == 'secondary':
        queryset = []
    else:
        # Для новостроек получаем данные из MongoDB
        filters = {'status': 'construction'}
        queryset = get_residential_complexes_from_mongo(filters=filters)

    # Категории
    category_map = {
        'apartment': 'apartment',
        'house': 'house',
        'cottage': 'cottage',
        'townhouse': 'townhouse',
        'commercial': None,
        'all': None,
    }
    house_type = category_map.get(landing['category'])
    if house_type:
        if landing['kind'] == 'secondary':
            pass
        else:
            queryset = queryset.filter(house_type=house_type)

    paginator = Paginator(queryset, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    categories = list(db['catalog_landings'].find({'kind': landing['kind'], 'is_active': True}).sort('name', 1))

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': [],  # Можно получить из MongoDB если нужно
        'rooms_choices': [('1', '1-комнатная'), ('2', '2-комнатная'), ('3', '3-комнатная'), ('4', '4-комнатная'), ('5+', '5+ комнат')],
        'filters': {},
        'filters_applied': True,
        'page_title': landing.get('name', ''),
        'page_description': landing.get('meta_description') or landing.get('name', ''),
        'landing': landing,
        'landing_categories': categories,
        'dataset_type': 'secondary' if landing.get('kind') == 'secondary' else 'newbuild',
    }

    return render(request, 'main/catalog.html', context)


def _catalog_fallback(request, kind: str, title: str):
    """Рендер каталога без необходимости иметь запись CatalogLanding.
    kind: 'newbuild'|'secondary'
    """
    if kind == 'secondary':
        queryset = []
    else:
        # Для новостроек получаем данные из MongoDB
        filters = {'status': 'construction'}
        queryset = get_residential_complexes_from_mongo(filters=filters)

    paginator = Paginator(queryset, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Получаем города из MongoDB для новостроек
    cities = []
    if kind == 'newbuild':
        try:
            db = get_mongo_connection()
            collection = db['residential_complexes']
            cities = collection.distinct('address.city')
        except Exception:
            cities = []

    context = {
        'complexes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': cities,
        'rooms_choices': [('1', '1-комнатная'), ('2', '2-комнатная'), ('3', '3-комнатная'), ('4', '4-комнатная'), ('5+', '5+ комнат')],
        'filters': ({'stype': request.GET.get('stype', '')} if kind == 'secondary' else {}),
        'filters_applied': True,
        'page_title': title,
        'page_description': title,
        'landing': None,
        'landing_categories': [],
        'dataset_type': kind,
    }
    return render(request, 'main/catalog.html', context)


def newbuild_index(request):
    # Стартовая страница новостроек - читает из MongoDB
    db = get_mongo_connection()
    landing = db['catalog_landings'].find_one({'kind': 'newbuild', 'category': 'all', 'is_active': True})
    if landing:
        return catalog_landing(request, slug=landing['slug'])
    return _catalog_fallback(request, kind='newbuild', title='Новостройки')


def secondary_index(request):
    # Стартовая страница вторички - читает из MongoDB
    db = get_mongo_connection()
    landing = db['catalog_landings'].find_one({'kind': 'secondary', 'category': 'all', 'is_active': True})
    if landing:
        return catalog_landing(request, slug=landing['slug'])
    return _catalog_fallback(request, kind='secondary', title='Вторичная недвижимость')

