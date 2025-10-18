"""
API функции для управления компанией (информация, офисы, сотрудники, отзывы)
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime

from ..services.mongo_service import get_mongo_connection
from ..s3_service import s3_client


@require_http_methods(["GET"])
def employee_reviews_api(request):
    """API: получить отзывы сотрудников для модерации."""
    try:
        db = get_mongo_connection()
        col = db['employee_reviews']
        employees_col = db['employees']
        
        # Получаем все отзывы, отсортированные по дате
        reviews = list(col.find().sort('created_at', -1))
        
        # Преобразуем ObjectId в строки и добавляем информацию о сотруднике
        for review in reviews:
            review['_id'] = str(review['_id'])
            review['employee_id'] = str(review['employee_id'])
            
            # Получаем информацию о сотруднике
            try:
                employee = employees_col.find_one({'_id': ObjectId(review['employee_id'])})
                if employee:
                    review['employee_name'] = employee.get('full_name', 'Неизвестный сотрудник')
                    review['employee_position'] = employee.get('position', '')
                else:
                    review['employee_name'] = 'Сотрудник удален'
                    review['employee_position'] = ''
            except:
                review['employee_name'] = 'Ошибка загрузки'
                review['employee_position'] = ''
        
        return JsonResponse({'success': True, 'reviews': reviews})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def employee_review_toggle(request, review_id):
    """API: переключить статус публикации отзыва."""
    try:
        db = get_mongo_connection()
        col = db['employee_reviews']
        
        # Получаем текущий статус
        review = col.find_one({'_id': ObjectId(review_id)})
        if not review:
            return JsonResponse({'success': False, 'error': 'Отзыв не найден'}, status=404)
        
        current_status = review.get('is_published', False)
        new_status = not current_status
        
        col.update_one(
            {'_id': ObjectId(review_id)},
            {'$set': {'is_published': new_status}}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Отзыв {"опубликован" if new_status else "скрыт"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def employee_review_update(request, review_id):
    """API: обновить отзыв."""
    try:
        db = get_mongo_connection()
        col = db['employee_reviews']
        
        # Проверяем существование отзыва
        review = col.find_one({'_id': ObjectId(review_id)})
        if not review:
            return JsonResponse({'success': False, 'error': 'Отзыв не найден'}, status=404)
        
        # Обновляем данные
        update_data = {
            'name': request.POST.get('name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'rating': int(request.POST.get('rating', 5)),
            'text': request.POST.get('text', '').strip(),
            'is_published': request.POST.get('is_published') == 'on',
        }
        
        # Валидация
        if not update_data['name'] or not update_data['text']:
            return JsonResponse({'success': False, 'error': 'Имя и текст отзыва обязательны'}, status=400)
        
        if not (1 <= update_data['rating'] <= 5):
            return JsonResponse({'success': False, 'error': 'Рейтинг должен быть от 1 до 5'}, status=400)
        
        col.update_one(
            {'_id': ObjectId(review_id)},
            {'$set': update_data}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Отзыв обновлен'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def employee_review_delete(request, review_id):
    """API: удалить отзыв."""
    try:
        db = get_mongo_connection()
        col = db['employee_reviews']
        
        result = col.delete_one({'_id': ObjectId(review_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'Отзыв не найден'}, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Отзыв удален'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== COMPANY INFO API ==========
@require_http_methods(["GET"])
def company_info_api_list(request):
    """API: получить список информации о компании."""
    try:
        db = get_mongo_connection()
        col = db['company_info']
        
        is_admin = request.GET.get('admin') == 'true'
        query = {} if is_admin else {'is_active': True}
        
        companies = list(col.find(query).sort('created_at', -1))
        
        items = []
        for company in companies:
            items.append({
                '_id': str(company['_id']),
                'founder_name': company.get('founder_name', ''),
                'founder_position': company.get('founder_position', ''),
                'company_name': company.get('company_name', ''),
                'quote': company.get('quote', ''),
                'description': company.get('description', ''),
                'main_image': company.get('main_image', ''),
                'images': company.get('images', []),
                'is_active': company.get('is_active', True),
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def company_info_api_create(request):
    """API: создать информацию о компании с загрузкой фото в S3."""
    try:
        db = get_mongo_connection()
        col = db['company_info']
        
        founder_name = request.POST.get('founder_name', '').strip()
        company_name = request.POST.get('company_name', '').strip()
        
        if not founder_name or not company_name:
            return JsonResponse({'success': False, 'error': 'Имя основателя и название компании обязательны'}, status=400)
        
        # Создаем slug для компании
        slug = slugify(company_name, allow_unicode=True)
        
        # Загрузка главного изображения в S3
        main_image_url = ''
        if 'main_image' in request.FILES:
            main_image = request.FILES['main_image']
            main_image_filename = f"main_{main_image.name}"
            s3_key = f"company/{slug}/{main_image_filename}"
            
            try:
                # Загружаем в S3
                main_image_url = s3_client.upload_fileobj(
                    main_image,
                    s3_key,
                    content_type=main_image.content_type or 'image/jpeg'
                )
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Ошибка загрузки главного изображения: {str(e)}'}, status=500)
        
        # Загрузка дополнительных изображений в S3
        images_urls = []
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            for idx, img in enumerate(images):
                img_filename = f"{idx+1}_{img.name}"
                s3_key = f"company/{slug}/{img_filename}"
                
                try:
                    # Загружаем в S3
                    s3_url = s3_client.upload_fileobj(
                        img,
                        s3_key,
                        content_type=img.content_type or 'image/jpeg'
                    )
                    images_urls.append(s3_url)
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Ошибка загрузки изображения {idx+1}: {str(e)}'}, status=500)
        
        company_data = {
            'founder_name': founder_name,
            'founder_position': request.POST.get('founder_position', 'Основатель компании').strip(),
            'company_name': company_name,
            'quote': request.POST.get('quote', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'main_image': main_image_url,
            'images': images_urls,
            'is_active': True,
            'created_at': datetime.now(),
        }
        
        result = col.insert_one(company_data)
        
        return JsonResponse({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'Информация о компании успешно создана'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def company_info_api_toggle(request, company_id):
    """API: переключить активность информации о компании."""
    try:
        db = get_mongo_connection()
        col = db['company_info']
        
        # Получаем текущий статус
        company = col.find_one({'_id': ObjectId(company_id)})
        if not company:
            return JsonResponse({'success': False, 'error': 'Информация не найдена'}, status=404)
        
        current_status = company.get('is_active', True)
        new_status = not current_status
        
        result = col.update_one(
            {'_id': ObjectId(company_id)},
            {'$set': {'is_active': new_status}}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'Информация не найдена'}, status=404)
        
        return JsonResponse({
            'success': True,
            'message': f'Информация {"активирована" if new_status else "деактивирована"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def company_info_api_detail(request, company_id):
    """API: получить данные компании по id."""
    try:
        db = get_mongo_connection()
        col = db['company_info']
        company = col.find_one({'_id': ObjectId(company_id)})
        if not company:
            return JsonResponse({'success': False, 'error': 'Информация не найдена'}, status=404)
        company['_id'] = str(company['_id'])
        return JsonResponse({'success': True, 'item': company})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def company_info_api_update(request, company_id):
    """API: обновить информацию о компании."""
    try:
        db = get_mongo_connection()
        col = db['company_info']
        
        company = col.find_one({'_id': ObjectId(company_id)})
        if not company:
            return JsonResponse({'success': False, 'error': 'Информация не найдена'}, status=404)
        
        update = {
            'founder_name': request.POST.get('founder_name', '').strip(),
            'founder_position': request.POST.get('founder_position', '').strip(),
            'company_name': request.POST.get('company_name', '').strip(),
            'quote': request.POST.get('quote', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'is_active': request.POST.get('is_active') == 'on',
        }
        
        # Получаем slug для загрузки файлов
        slug = slugify(update['company_name'] or company['company_name'], allow_unicode=True)
        
        # Загрузка главного изображения в S3
        if 'main_image' in request.FILES:
            main_image = request.FILES['main_image']
            main_image_filename = f"main_{main_image.name}"
            s3_key = f"company/{slug}/{main_image_filename}"
            
            try:
                # Загружаем в S3
                s3_url = s3_client.upload_fileobj(
                    main_image,
                    s3_key,
                    content_type=main_image.content_type or 'image/jpeg'
                )
                update['main_image'] = s3_url
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Ошибка загрузки главного изображения: {str(e)}'}, status=500)
        
        # Загрузка дополнительных изображений в S3
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            if images:
                images_urls = []
                
                for idx, img in enumerate(images):
                    img_filename = f"{idx+1}_{img.name}"
                    s3_key = f"company/{slug}/{img_filename}"
                    
                    try:
                        # Загружаем в S3
                        s3_url = s3_client.upload_fileobj(
                            img,
                            s3_key,
                            content_type=img.content_type or 'image/jpeg'
                        )
                        images_urls.append(s3_url)
                    except Exception as e:
                        return JsonResponse({'success': False, 'error': f'Ошибка загрузки изображения {idx+1}: {str(e)}'}, status=500)
                
                update['images'] = images_urls
        
        result = col.update_one(
            {'_id': ObjectId(company_id)},
            {'$set': update}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'Информация не найдена'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'Информация обновлена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def company_info_api_delete(request, company_id):
    """API: удалить информацию о компании и её изображения."""
    try:
        db = get_mongo_connection()
        col = db['company_info']
        
        company = col.find_one({'_id': ObjectId(company_id)})
        if not company:
            return JsonResponse({'success': False, 'error': 'Информация не найдена'}, status=404)
        
        # Удаляем папку с изображениями
        if company.get('company_name'):
            slug = slugify(company['company_name'], allow_unicode=True)
            company_folder = os.path.join(settings.MEDIA_ROOT, 'company', slug)
            if os.path.exists(company_folder):
                import shutil
                shutil.rmtree(company_folder)
        
        col.delete_one({'_id': ObjectId(company_id)})
        
        return JsonResponse({'success': True, 'message': 'Информация удалена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== BRANCH OFFICE API ==========
@require_http_methods(["GET"])
def branch_office_api_list(request):
    """API: получить список офисов продаж."""
    try:
        db = get_mongo_connection()
        col = db['branch_offices']
        
        is_admin = request.GET.get('admin') == 'true'
        query = {} if is_admin else {'is_active': True}
        
        offices = list(col.find(query).sort('name', 1))
        
        items = []
        for office in offices:
            items.append({
                '_id': str(office['_id']),
                'name': office.get('name', ''),
                'slug': office.get('slug', ''),
                'address': office.get('address', ''),
                'phone': office.get('phone', ''),
                'email': office.get('email', ''),
                'schedule': office.get('schedule', ''),
                'is_head_office': office.get('is_head_office', False),
                'main_image': office.get('main_image', ''),
                'images': office.get('images', []),
                'is_active': office.get('is_active', True),
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def branch_office_api_create(request):
    """API: создать офис продаж с загрузкой фото."""
    try:
        db = get_mongo_connection()
        col = db['branch_offices']
        
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Название офиса обязательно'}, status=400)
        
        slug = request.POST.get('slug', '').strip()
        if not slug:
            slug = slugify(name, allow_unicode=True)
        
        # Проверка уникальности slug
        if col.find_one({'slug': slug}):
            return JsonResponse({'success': False, 'error': 'Офис с таким slug уже существует'}, status=400)
        
        # Загрузка главного изображения в S3
        main_image_path = ''
        if 'main_image' in request.FILES:
            main_image = request.FILES['main_image']
            main_image_filename = f"main_{main_image.name}"
            s3_key = f"offices/{slug}/{main_image_filename}"
            
            try:
                s3_url = s3_client.upload_fileobj(
                    main_image,
                    s3_key,
                    content_type=main_image.content_type or 'image/jpeg'
                )
                main_image_path = s3_url
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Ошибка загрузки главного изображения: {str(e)}'}, status=500)
        
        # Загрузка дополнительных изображений в S3
        images_paths = []
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            for idx, img in enumerate(images):
                img_filename = f"{idx+1}_{img.name}"
                s3_key = f"offices/{slug}/{img_filename}"
                
                try:
                    s3_url = s3_client.upload_fileobj(
                        img,
                        s3_key,
                        content_type=img.content_type or 'image/jpeg'
                    )
                    images_paths.append(s3_url)
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Ошибка загрузки изображения {idx+1}: {str(e)}'}, status=500)
        
        # Парсим координаты, если переданы
        lat_raw = request.POST.get('latitude', '').strip()
        lng_raw = request.POST.get('longitude', '').strip()
        latitude = None
        longitude = None
        try:
            if lat_raw:
                latitude = float(lat_raw.replace(',', '.'))
            if lng_raw:
                longitude = float(lng_raw.replace(',', '.'))
        except ValueError:
            latitude = None
            longitude = None

        # Обработка видео (массив URL)
        videos_data = []
        video_urls = request.POST.get('video_urls', '').strip()
        if video_urls:
            for url in video_urls.split('\n'):
                url = url.strip()
                if url:
                    videos_data.append(url)

        office_data = {
            'name': name,
            'slug': slug,
            'address': request.POST.get('address', '').strip(),
            'city': request.POST.get('city', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'schedule': request.POST.get('schedule', '').strip(),
            'is_head_office': request.POST.get('is_head_office') == 'on',
            'main_image': main_image_path,
            'images': images_paths,
            'videos': videos_data,
            'latitude': latitude,
            'longitude': longitude,
            'is_active': True,
            'created_at': datetime.now(),
        }
        
        result = col.insert_one(office_data)
        
        return JsonResponse({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'Офис продаж успешно создан'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def branch_office_api_detail(request, office_id):
    """API: получить данные офиса по id."""
    try:
        db = get_mongo_connection()
        col = db['branch_offices']
        office = col.find_one({'_id': ObjectId(office_id)})
        if not office:
            return JsonResponse({'success': False, 'error': 'Офис не найден'}, status=404)
        office['_id'] = str(office['_id'])
        return JsonResponse({'success': True, 'item': office})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def branch_office_api_update(request, office_id):
    """API: обновить офис (включая координаты)."""
    try:
        db = get_mongo_connection()
        col = db['branch_offices']

        update = {
            'name': request.POST.get('name', '').strip(),
            'slug': request.POST.get('slug', '').strip(),
            'city': request.POST.get('city', '').strip(),
            'address': request.POST.get('address', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'schedule': request.POST.get('schedule', '').strip(),
            'is_head_office': request.POST.get('is_head_office') == 'on',
        }

        lat_raw = request.POST.get('latitude', '').strip()
        lng_raw = request.POST.get('longitude', '').strip()
        try:
            if lat_raw:
                update['latitude'] = float(lat_raw.replace(',', '.'))
            if lng_raw:
                update['longitude'] = float(lng_raw.replace(',', '.'))
        except ValueError:
            pass

        # Обновление изображений (опционально) - загрузка в S3
        slug = update['slug'] or 'office'

        if 'main_image' in request.FILES:
            main_image = request.FILES['main_image']
            main_image_filename = f"main_{main_image.name}"
            s3_key = f"offices/{slug}/{main_image_filename}"
            
            try:
                s3_url = s3_client.upload_fileobj(
                    main_image,
                    s3_key,
                    content_type=main_image.content_type or 'image/jpeg'
                )
                update['main_image'] = s3_url
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Ошибка загрузки главного изображения: {str(e)}'}, status=500)

        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            images_paths = []
            for idx, img in enumerate(images):
                img_filename = f"{idx+1}_{img.name}"
                s3_key = f"offices/{slug}/{img_filename}"
                
                try:
                    s3_url = s3_client.upload_fileobj(
                        img,
                        s3_key,
                        content_type=img.content_type or 'image/jpeg'
                    )
                    images_paths.append(s3_url)
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Ошибка загрузки изображения {idx+1}: {str(e)}'}, status=500)
            update['images'] = images_paths

        # Обновление видео
        video_urls = request.POST.get('video_urls', '').strip()
        if video_urls:
            videos_data = []
            for url in video_urls.split('\n'):
                url = url.strip()
                if url:
                    videos_data.append(url)
            update['videos'] = videos_data

        col.update_one({'_id': ObjectId(office_id)}, {'$set': update})
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def branch_office_api_toggle(request, office_id):
    """API: переключить активность офиса."""
    try:
        db = get_mongo_connection()
        col = db['branch_offices']
        
        # Получаем текущий статус
        office = col.find_one({'_id': ObjectId(office_id)})
        if not office:
            return JsonResponse({'success': False, 'error': 'Офис не найден'}, status=404)
        
        current_status = office.get('is_active', True)
        new_status = not current_status
        
        col.update_one(
            {'_id': ObjectId(office_id)},
            {'$set': {'is_active': new_status}}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Офис {"активирован" if new_status else "деактивирован"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def branch_office_api_delete(request, office_id):
    """API: удалить офис и его изображения."""
    try:
        db = get_mongo_connection()
        col = db['branch_offices']
        
        office = col.find_one({'_id': ObjectId(office_id)})
        if not office:
            return JsonResponse({'success': False, 'error': 'Офис не найден'}, status=404)
        
        # Удаляем папку с изображениями
        if office.get('slug'):
            office_folder = os.path.join(settings.MEDIA_ROOT, 'offices', office['slug'])
            if os.path.exists(office_folder):
                import shutil
                shutil.rmtree(office_folder)
        
        col.delete_one({'_id': ObjectId(office_id)})
        
        return JsonResponse({'success': True, 'message': 'Офис удален'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== EMPLOYEE API ==========
@require_http_methods(["GET"])
def employee_api_list(request):
    """API: получить список сотрудников."""
    try:
        db = get_mongo_connection()
        col = db['employees']
        
        is_admin = request.GET.get('admin') == 'true'
        query = {} if is_admin else {'is_active': True}
        
        employees = list(col.find(query).sort('full_name', 1))
        
        items = []
        for employee in employees:
            items.append({
                '_id': str(employee['_id']),
                'full_name': employee.get('full_name', ''),
                'slug': employee.get('slug', ''),
                'position': employee.get('position', ''),
                'phone': employee.get('phone', ''),
                'email': employee.get('email', ''),
                'experience_years': employee.get('experience_years', 0),
                'specialization': employee.get('specialization', ''),
                'bio': employee.get('bio', ''),
                'achievements': employee.get('achievements', ''),
                'main_image': employee.get('main_image', ''),
                'images': employee.get('images', []),
                'videos': employee.get('videos', []),
                'is_active': employee.get('is_active', True),
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def employee_api_create(request):
    """API: создать сотрудника с загрузкой фото."""
    try:
        db = get_mongo_connection()
        col = db['employees']
        
        full_name = request.POST.get('full_name', '').strip()
        if not full_name:
            return JsonResponse({'success': False, 'error': 'ФИО сотрудника обязательно'}, status=400)
        
        slug = request.POST.get('slug', '').strip()
        if not slug:
            slug = slugify(full_name, allow_unicode=True)
        
        # Проверка уникальности slug
        if col.find_one({'slug': slug}):
            return JsonResponse({'success': False, 'error': 'Сотрудник с таким slug уже существует'}, status=400)
        
        # Загрузка изображений в S3 (все в массив images)
        images_paths = []
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            for idx, img in enumerate(images):
                img_filename = f"{idx+1}_{img.name}"
                s3_key = f"employees/{slug}/{img_filename}"
                
                try:
                    s3_url = s3_client.upload_fileobj(
                        img,
                        s3_key,
                        content_type=img.content_type or 'image/jpeg'
                    )
                    images_paths.append(s3_url)
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Ошибка загрузки изображения {idx+1}: {str(e)}'}, status=500)
        
        # Обработка видео (массив URL)
        videos_data = []
        video_urls = request.POST.get('video_urls', '').strip()
        if video_urls:
            for url in video_urls.split('\n'):
                url = url.strip()
                if url:
                    videos_data.append({
                        'url': url,
                        'thumbnail': get_video_thumbnail(url)
                    })
        
        employee_data = {
            'full_name': full_name,
            'slug': slug,
            'position': request.POST.get('position', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'experience_years': int(request.POST.get('experience_years', 0) or 0),
            'specialization': request.POST.get('specialization', '').strip(),
            'bio': request.POST.get('bio', '').strip(),
            'achievements': request.POST.get('achievements', '').strip(),
            'images': images_paths,
            'videos': videos_data,
            'is_active': True,
            'created_at': datetime.now(),
        }
        
        result = col.insert_one(employee_data)
        
        return JsonResponse({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'Сотрудник успешно создан'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def employee_api_toggle(request, employee_id):
    """API: переключить активность сотрудника."""
    try:
        db = get_mongo_connection()
        col = db['employees']
        
        # Получаем текущий статус
        employee = col.find_one({'_id': ObjectId(employee_id)})
        if not employee:
            return JsonResponse({'success': False, 'error': 'Сотрудник не найден'}, status=404)
        
        current_status = employee.get('is_active', True)
        new_status = not current_status
        
        col.update_one(
            {'_id': ObjectId(employee_id)},
            {'$set': {'is_active': new_status}}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Сотрудник {"активирован" if new_status else "деактивирован"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def employee_api_detail(request, employee_id):
    """API: получить данные сотрудника по id."""
    try:
        db = get_mongo_connection()
        col = db['employees']
        employee = col.find_one({'_id': ObjectId(employee_id)})
        if not employee:
            return JsonResponse({'success': False, 'error': 'Сотрудник не найден'}, status=404)
        employee['_id'] = str(employee['_id'])
        return JsonResponse({'success': True, 'item': employee})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def employee_api_update(request, employee_id):
    """API: обновить данные сотрудника."""
    try:
        db = get_mongo_connection()
        col = db['employees']
        
        employee = col.find_one({'_id': ObjectId(employee_id)})
        if not employee:
            return JsonResponse({'success': False, 'error': 'Сотрудник не найден'}, status=404)
        
        full_name = request.POST.get('full_name', '').strip()
        if not full_name:
            return JsonResponse({'success': False, 'error': 'ФИО обязательно'}, status=400)
        
        slug = slugify(full_name, allow_unicode=True)
        
        update = {
            'full_name': full_name,
            'position': request.POST.get('position', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'experience_years': int(request.POST.get('experience_years', 0) or 0),
            'specialization': request.POST.get('specialization', '').strip(),
            'bio': request.POST.get('bio', '').strip(),
            'achievements': [a.strip() for a in request.POST.get('achievements', '').split(',') if a.strip()],
            'is_active': request.POST.get('is_active') == 'on',
            'slug': slug,
        }
        
        # Загрузка изображений в S3 (все в массив images)
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            if images:
                images_urls = []
                
                for idx, img in enumerate(images):
                    img_filename = f"{idx+1}_{img.name}"
                    s3_key = f"employees/{slug}/{img_filename}"
                    
                    try:
                        s3_url = s3_client.upload_fileobj(
                            img,
                            s3_key,
                            content_type=img.content_type or 'image/jpeg'
                        )
                        images_urls.append(s3_url)
                    except Exception as e:
                        return JsonResponse({'success': False, 'error': f'Ошибка загрузки изображения {idx+1}: {str(e)}'}, status=500)
                
                update['images'] = images_urls
        
        # Обработка видео
        video_urls = request.POST.get('video_urls', '').strip()
        if video_urls:
            videos_data = []
            for url in video_urls.split('\n'):
                url = url.strip()
                if url:
                    videos_data.append(url)
            update['videos'] = videos_data
        
        result = col.update_one(
            {'_id': ObjectId(employee_id)},
            {'$set': update}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'Сотрудник не найден'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'Сотрудник обновлен'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def employee_api_delete(request, employee_id):
    """API: удалить сотрудника и его изображения."""
    try:
        db = get_mongo_connection()
        col = db['employees']
        
        employee = col.find_one({'_id': ObjectId(employee_id)})
        if not employee:
            return JsonResponse({'success': False, 'error': 'Сотрудник не найден'}, status=404)
        
        # Удаляем изображения из S3 если есть slug
        if employee.get('slug'):
            s3_prefix = f"employees/{employee['slug']}/"
            try:
                s3_client.delete_prefix(s3_prefix)
            except Exception as e:
                pass
        
        col.delete_one({'_id': ObjectId(employee_id)})
        
        return JsonResponse({'success': True, 'message': 'Сотрудник удален'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
