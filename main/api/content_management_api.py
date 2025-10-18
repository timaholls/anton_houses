"""
API функции для управления контентом (теги, категории, авторы, статьи, лендинги каталога)
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from bson import ObjectId
from datetime import datetime

from ..services.mongo_service import get_mongo_connection
from ..s3_service import s3_client


# ========== TAGS API ==========
@require_http_methods(["GET"])
def tags_api_list(request):
    """API: получить список тегов."""
    try:
        db = get_mongo_connection()
        col = db['tags']
        
        # Если admin=true, показываем все, иначе только активные
        is_admin = request.GET.get('admin') == 'true'
        query = {} if is_admin else {'is_active': True}
        
        tags = list(col.find(query).sort('name', 1))
        
        items = []
        for tag in tags:
            items.append({
                '_id': str(tag['_id']),
                'name': tag.get('name', ''),
                'slug': tag.get('slug', ''),
                'h1_title': tag.get('h1_title', ''),
                'meta_title': tag.get('meta_title', ''),
                'meta_description': tag.get('meta_description', ''),
                'is_active': tag.get('is_active', True),
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def tags_api_create(request):
    """API: создать тег."""
    try:
        db = get_mongo_connection()
        col = db['tags']
        
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Название обязательно'}, status=400)
        
        slug = request.POST.get('slug', '').strip()
        if not slug:
            slug = slugify(name, allow_unicode=True)
        
        # Проверка уникальности slug
        if col.find_one({'slug': slug}):
            return JsonResponse({'success': False, 'error': 'Тег с таким slug уже существует'}, status=400)
        
        tag_data = {
            'name': name,
            'slug': slug,
            'h1_title': request.POST.get('h1_title', '').strip(),
            'meta_title': request.POST.get('meta_title', '').strip(),
            'meta_description': request.POST.get('meta_description', '').strip(),
            'is_active': True,
            'created_at': datetime.now(),
        }
        
        result = col.insert_one(tag_data)
        
        return JsonResponse({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'Тег успешно создан'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def tags_api_toggle(request, tag_id):
    """API: переключить активность тега."""
    try:
        db = get_mongo_connection()
        col = db['tags']
        
        # Получаем текущий статус
        tag = col.find_one({'_id': ObjectId(tag_id)})
        if not tag:
            return JsonResponse({'success': False, 'error': 'Тег не найден'}, status=404)
        
        current_status = tag.get('is_active', True)
        new_status = not current_status
        
        result = col.update_one(
            {'_id': ObjectId(tag_id)},
            {'$set': {'is_active': new_status}}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Тег {"активирован" if new_status else "деактивирован"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def tags_api_delete(request, tag_id):
    """API: удалить тег."""
    try:
        db = get_mongo_connection()
        col = db['tags']
        
        result = col.delete_one({'_id': ObjectId(tag_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'Тег не найден'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'Тег удален'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def tags_api_get(request, tag_id):
    """API: получить один тег для редактирования."""
    try:
        db = get_mongo_connection()
        col = db['tags']
        
        tag = col.find_one({'_id': ObjectId(tag_id)})
        if not tag:
            return JsonResponse({'success': False, 'error': 'Тег не найден'}, status=404)
        
        tag['_id'] = str(tag['_id'])
        return JsonResponse({'success': True, 'item': tag})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def tags_api_update(request, tag_id):
    """API: обновить тег."""
    try:
        db = get_mongo_connection()
        col = db['tags']
        
        # Проверяем существование тега
        tag = col.find_one({'_id': ObjectId(tag_id)})
        if not tag:
            return JsonResponse({'success': False, 'error': 'Тег не найден'}, status=404)
        
        update = {}
        
        if 'name' in request.POST:
            update['name'] = request.POST.get('name', '').strip()
        
        if 'slug' in request.POST:
            slug = request.POST.get('slug', '').strip()
            if slug and slug != tag.get('slug'):
                # Проверяем уникальность нового slug
                if col.find_one({'slug': slug, '_id': {'$ne': ObjectId(tag_id)}}):
                    return JsonResponse({'success': False, 'error': 'Тег с таким slug уже существует'}, status=400)
                update['slug'] = slug
        
        if 'h1_title' in request.POST:
            update['h1_title'] = request.POST.get('h1_title', '').strip()
        
        if 'meta_title' in request.POST:
            update['meta_title'] = request.POST.get('meta_title', '').strip()
        
        if 'meta_description' in request.POST:
            update['meta_description'] = request.POST.get('meta_description', '').strip()
        
        # Обновляем тег
        result = col.update_one(
            {'_id': ObjectId(tag_id)},
            {'$set': update}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'Тег не найден'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'Тег обновлен'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== CATEGORIES API ==========
@require_http_methods(["GET"])
def categories_api_list(request):
    """API: получить список категорий."""
    try:
        db = get_mongo_connection()
        col = db['categories']
        
        is_admin = request.GET.get('admin') == 'true'
        query = {} if is_admin else {'is_active': True}
        
        categories = list(col.find(query).sort('name', 1))
        
        items = []
        for cat in categories:
            items.append({
                '_id': str(cat['_id']),
                'name': cat.get('name', ''),
                'slug': cat.get('slug', ''),
                'description': cat.get('description', ''),
                'is_active': cat.get('is_active', True),
                'created_at': cat.get('created_at', ''),
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def categories_api_create(request):
    """API: создать категорию."""
    try:
        db = get_mongo_connection()
        col = db['categories']
        
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Название обязательно'}, status=400)
        
        slug = request.POST.get('slug', '').strip()
        if not slug:
            slug = slugify(name, allow_unicode=True)
        
        if col.find_one({'slug': slug}):
            return JsonResponse({'success': False, 'error': 'Категория с таким slug уже существует'}, status=400)
        
        category_data = {
            'name': name,
            'slug': slug,
            'description': request.POST.get('description', '').strip(),
            'is_active': True,
            'created_at': datetime.now(),
        }
        
        result = col.insert_one(category_data)
        
        return JsonResponse({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'Категория успешно создана'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def categories_api_toggle(request, category_id):
    """API: переключить активность категории."""
    try:
        db = get_mongo_connection()
        col = db['categories']
        
        # Получаем текущий статус
        category = col.find_one({'_id': ObjectId(category_id)})
        if not category:
            return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)
        
        current_status = category.get('is_active', True)
        new_status = not current_status
        
        result = col.update_one(
            {'_id': ObjectId(category_id)},
            {'$set': {'is_active': new_status}}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Категория {"активирована" if new_status else "деактивирована"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def categories_api_delete(request, category_id):
    """API: удалить категорию."""
    try:
        db = get_mongo_connection()
        col = db['categories']
        
        result = col.delete_one({'_id': ObjectId(category_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'Категория удалена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def categories_api_get(request, category_id):
    """API: получить одну категорию для редактирования."""
    try:
        db = get_mongo_connection()
        col = db['categories']
        
        category = col.find_one({'_id': ObjectId(category_id)})
        if not category:
            return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)
        
        category['_id'] = str(category['_id'])
        return JsonResponse({'success': True, 'item': category})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def categories_api_update(request, category_id):
    """API: обновить категорию."""
    try:
        db = get_mongo_connection()
        col = db['categories']
        
        # Проверяем существование категории
        category = col.find_one({'_id': ObjectId(category_id)})
        if not category:
            return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)
        
        update = {}
        
        if 'name' in request.POST:
            update['name'] = request.POST.get('name', '').strip()
        
        if 'slug' in request.POST:
            slug = request.POST.get('slug', '').strip()
            if slug and slug != category.get('slug'):
                # Проверяем уникальность нового slug
                if col.find_one({'slug': slug, '_id': {'$ne': ObjectId(category_id)}}):
                    return JsonResponse({'success': False, 'error': 'Категория с таким slug уже существует'}, status=400)
                update['slug'] = slug
        
        if 'description' in request.POST:
            update['description'] = request.POST.get('description', '').strip()
        
        # Обновляем категорию
        result = col.update_one(
            {'_id': ObjectId(category_id)},
            {'$set': update}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'Категория обновлена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== AUTHORS API ==========
@require_http_methods(["GET"])
def authors_api_list(request):
    """API: получить список авторов."""
    try:
        db = get_mongo_connection()
        col = db['authors']
        
        is_admin = request.GET.get('admin') == 'true'
        query = {} if is_admin else {'is_active': True}
        
        authors = list(col.find(query).sort('name', 1))
        
        items = []
        for author in authors:
            items.append({
                '_id': str(author['_id']),
                'name': author.get('name', ''),
                'position': author.get('position', ''),
                'description': author.get('description', ''),
                'articles_count': author.get('articles_count', 0),
                'total_views': author.get('total_views', 0),
                'total_likes': author.get('total_likes', 0),
                'is_active': author.get('is_active', True),
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def authors_api_create(request):
    """API: создать автора."""
    try:
        db = get_mongo_connection()
        col = db['authors']
        
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Имя автора обязательно'}, status=400)
        
        author_data = {
            'name': name,
            'position': request.POST.get('position', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'articles_count': 0,
            'total_views': 0,
            'total_likes': 0,
            'is_active': True,
            'created_at': datetime.now(),
        }
        
        result = col.insert_one(author_data)
        
        return JsonResponse({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'Автор успешно создан'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def authors_api_toggle(request, author_id):
    """API: переключить активность автора."""
    try:
        db = get_mongo_connection()
        col = db['authors']
        
        # Получаем текущий статус
        author = col.find_one({'_id': ObjectId(author_id)})
        if not author:
            return JsonResponse({'success': False, 'error': 'Автор не найден'}, status=404)
        
        current_status = author.get('is_active', True)
        new_status = not current_status
        
        result = col.update_one(
            {'_id': ObjectId(author_id)},
            {'$set': {'is_active': new_status}}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Автор {"активирован" if new_status else "деактивирован"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def authors_api_delete(request, author_id):
    """API: удалить автора."""
    try:
        db = get_mongo_connection()
        col = db['authors']
        
        result = col.delete_one({'_id': ObjectId(author_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'Автор не найден'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'Автор удален'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== ARTICLES API ==========
@require_http_methods(["GET"])
def articles_api_list(request):
    """API: получить список статей."""
    try:
        db = get_mongo_connection()
        col = db['articles']
        categories_col = db['categories']
        authors_col = db['authors']
        
        is_admin = request.GET.get('admin') == 'true'
        query = {} if is_admin else {'is_active': True}
        
        articles = list(col.find(query).sort('published_date', -1))
        
        items = []
        for article in articles:
            # Получаем имена категории и автора
            category_name = ''
            if article.get('category_id'):
                cat = categories_col.find_one({'_id': ObjectId(article['category_id'])})
                category_name = cat['name'] if cat else ''
            
            author_name = ''
            if article.get('author_id'):
                author = authors_col.find_one({'_id': ObjectId(article['author_id'])})
                author_name = author['name'] if author else ''
            
            items.append({
                '_id': str(article['_id']),
                'title': article.get('title', ''),
                'slug': article.get('slug', ''),
                'article_type': article.get('article_type', 'news'),
                'category_id': str(article.get('category_id', '')),
                'category_name': category_name,
                'author_id': str(article.get('author_id', '')),
                'author_name': author_name,
                'excerpt': article.get('excerpt', ''),
                'published_date': article.get('published_date', ''),
                'is_active': article.get('is_active', True),
                'show_on_home': article.get('show_on_home', False),
                'is_featured': article.get('is_featured', False),
                'views_count': article.get('views_count', 0),
                'likes_count': article.get('likes_count', 0),
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def articles_api_create(request):
    """API: создать статью с загрузкой фото."""
    try:
        db = get_mongo_connection()
        col = db['articles']
        
        title = request.POST.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'Заголовок обязателен'}, status=400)
        
        category_id = request.POST.get('category_id', '').strip()
        if not category_id:
            return JsonResponse({'success': False, 'error': 'Категория обязательна'}, status=400)
        
        slug = request.POST.get('slug', '').strip()
        if not slug:
            slug = slugify(title, allow_unicode=True)
        
        # Проверка уникальности slug
        if col.find_one({'slug': slug}):
            return JsonResponse({'success': False, 'error': 'Статья с таким slug уже существует'}, status=400)
        
        # Загрузка главного изображения в S3
        main_image_path = ''
        if 'main_image' in request.FILES:
            main_image = request.FILES['main_image']
            main_image_filename = f"main_{main_image.name}"
            s3_key = f'articles/{slug}/{main_image_filename}'
            content_type = main_image.content_type if hasattr(main_image, 'content_type') else 'image/jpeg'
            main_image_path = s3_client.upload_fileobj(main_image, s3_key, content_type)
        
        # Загрузка дополнительных изображений в S3
        images_paths = []
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            for idx, img in enumerate(images):
                img_filename = f"{idx+1}_{img.name}"
                s3_key = f'articles/{slug}/{img_filename}'
                content_type = img.content_type if hasattr(img, 'content_type') else 'image/jpeg'
                img_url = s3_client.upload_fileobj(img, s3_key, content_type)
                images_paths.append(img_url)
        
        # Обработка тегов (множественный выбор)
        tags = request.POST.getlist('tags')
        tag_ids = [ObjectId(tag_id) for tag_id in tags if tag_id]
        
        article_data = {
            'title': title,
            'slug': slug,
            'article_type': request.POST.get('article_type', 'news'),
            'category_id': ObjectId(category_id),
            'author_id': ObjectId(request.POST.get('author_id')) if request.POST.get('author_id') else None,
            'content': request.POST.get('content', '').strip(),
            'excerpt': request.POST.get('excerpt', '').strip(),
            'main_image': main_image_path,
            'images': images_paths,
            'tags': tag_ids,
            'show_on_home': request.POST.get('show_on_home') == 'on',
            'is_featured': request.POST.get('is_featured') == 'on',
            'is_active': True,
            'views_count': 0,
            'likes_count': 0,
            'comments_count': 0,
            'published_date': datetime.now(),
            'updated_date': datetime.now(),
        }
        
        result = col.insert_one(article_data)
        
        return JsonResponse({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'Статья успешно создана'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def articles_api_toggle(request, article_id):
    """API: переключить активность статьи."""
    try:
        db = get_mongo_connection()
        col = db['articles']
        
        # Получаем текущий статус
        article = col.find_one({'_id': ObjectId(article_id)})
        if not article:
            return JsonResponse({'success': False, 'error': 'Статья не найдена'}, status=404)
        
        current_status = article.get('is_active', True)
        new_status = not current_status
        
        result = col.update_one(
            {'_id': ObjectId(article_id)},
            {'$set': {'is_active': new_status}}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Статья {"активирована" if new_status else "деактивирована"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def articles_api_delete(request, article_id):
    """API: удалить статью и её изображения."""
    try:
        db = get_mongo_connection()
        col = db['articles']
        
        # Получаем статью перед удалением
        article = col.find_one({'_id': ObjectId(article_id)})
        if not article:
            return JsonResponse({'success': False, 'error': 'Статья не найдена'}, status=404)
        
        # Удаляем изображения из S3
        if article.get('slug'):
            s3_prefix = f"articles/{article['slug']}/"
            s3_client.delete_prefix(s3_prefix)
        
        # Удаляем запись из БД
        col.delete_one({'_id': ObjectId(article_id)})
        
        return JsonResponse({'success': True, 'message': 'Статья удалена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def articles_api_get(request, article_id):
    """API: получить одну статью для редактирования."""
    try:
        db = get_mongo_connection()
        col = db['articles']
        
        article = col.find_one({'_id': ObjectId(article_id)})
        if not article:
            return JsonResponse({'success': False, 'error': 'Статья не найдена'}, status=404)
        
        # Преобразуем ObjectId в строки
        article['_id'] = str(article['_id'])
        if article.get('category_id'):
            article['category_id'] = str(article['category_id'])
        if article.get('author_id'):
            article['author_id'] = str(article['author_id'])
        if article.get('tags'):
            article['tags'] = [str(tag_id) for tag_id in article['tags']]
        
        return JsonResponse({'success': True, 'item': article})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def articles_api_update(request, article_id):
    """API: обновить статью с загрузкой фото в S3."""
    try:
        db = get_mongo_connection()
        col = db['articles']
        
        # Проверяем существование статьи
        article = col.find_one({'_id': ObjectId(article_id)})
        if not article:
            return JsonResponse({'success': False, 'error': 'Статья не найдена'}, status=404)
        
        update = {}
        
        # Обновляем основные поля
        if 'title' in request.POST:
            update['title'] = request.POST.get('title', '').strip()
        
        if 'slug' in request.POST:
            slug = request.POST.get('slug', '').strip()
            if slug and slug != article.get('slug'):
                # Проверяем уникальность нового slug
                if col.find_one({'slug': slug, '_id': {'$ne': ObjectId(article_id)}}):
                    return JsonResponse({'success': False, 'error': 'Статья с таким slug уже существует'}, status=400)
                update['slug'] = slug
        
        if 'article_type' in request.POST:
            update['article_type'] = request.POST.get('article_type', 'news')
        
        if 'category_id' in request.POST:
            category_id = request.POST.get('category_id', '').strip()
            if category_id:
                update['category_id'] = ObjectId(category_id)
        
        if 'author_id' in request.POST:
            author_id = request.POST.get('author_id', '').strip()
            update['author_id'] = ObjectId(author_id) if author_id else None
        
        if 'content' in request.POST:
            update['content'] = request.POST.get('content', '').strip()
        
        if 'excerpt' in request.POST:
            update['excerpt'] = request.POST.get('excerpt', '').strip()
        
        # Обработка тегов
        if 'tags' in request.POST:
            tags = request.POST.getlist('tags')
            tag_ids = [ObjectId(tag_id) for tag_id in tags if tag_id]
            update['tags'] = tag_ids
        
        # Булевы поля
        update['show_on_home'] = request.POST.get('show_on_home') == 'on'
        update['is_featured'] = request.POST.get('is_featured') == 'on'
        
        # Загрузка главного изображения в S3 (если новое)
        if 'main_image' in request.FILES:
            main_image = request.FILES['main_image']
            main_image_filename = f"main_{main_image.name}"
            slug = update.get('slug') or article.get('slug', 'article')
            s3_key = f'articles/{slug}/{main_image_filename}'
            
            try:
                s3_url = s3_client.upload_fileobj(
                    main_image,
                    s3_key,
                    content_type=main_image.content_type or 'image/jpeg'
                )
                update['main_image'] = s3_url
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Ошибка загрузки главного изображения: {str(e)}'}, status=500)
        
        # Загрузка дополнительных изображений в S3 (если новые)
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            if images:
                images_paths = []
                slug = update.get('slug') or article.get('slug', 'article')
                
                for idx, img in enumerate(images):
                    img_filename = f"{idx+1}_{img.name}"
                    s3_key = f'articles/{slug}/{img_filename}'
                    
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
        
        update['updated_date'] = datetime.now()
        
        # Обновляем статью
        result = col.update_one(
            {'_id': ObjectId(article_id)},
            {'$set': update}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'Статья не найдена'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'Статья обновлена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== CATALOG LANDINGS API ==========
@require_http_methods(["GET"])
def catalog_landings_api_list(request):
    """API: получить список SEO страниц каталога."""
    try:
        db = get_mongo_connection()
        col = db['catalog_landings']
        
        is_admin = request.GET.get('admin') == 'true'
        query = {} if is_admin else {'is_active': True}
        
        landings = list(col.find(query).sort('name', 1))
        
        # Словарь для перевода категорий
        category_names = {
            'all': 'Все объекты',
            'apartment': 'Квартиры',
            'house': 'Дома',
            'cottage': 'Коттеджи',
            'townhouse': 'Таунхаусы',
            'commercial': 'Коммерческие помещения',
        }
        
        items = []
        for landing in landings:
            items.append({
                '_id': str(landing['_id']),
                'name': landing.get('name', ''),
                'slug': landing.get('slug', ''),
                'kind': landing.get('kind', 'newbuild'),
                'category': landing.get('category', 'all'),
                'category_display': category_names.get(landing.get('category', 'all'), landing.get('category', 'all')),
                'meta_title': landing.get('meta_title', ''),
                'meta_description': landing.get('meta_description', ''),
                'meta_keywords': landing.get('meta_keywords', ''),
                'is_active': landing.get('is_active', True),
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def catalog_landings_api_create(request):
    """API: создать SEO страницу каталога."""
    try:
        db = get_mongo_connection()
        col = db['catalog_landings']
        
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        
        if not name or not slug:
            return JsonResponse({'success': False, 'error': 'Название и slug обязательны'}, status=400)
        
        # Проверка уникальности slug
        if col.find_one({'slug': slug}):
            return JsonResponse({'success': False, 'error': 'Страница с таким slug уже существует'}, status=400)
        
        landing_data = {
            'name': name,
            'slug': slug,
            'kind': request.POST.get('kind', 'newbuild'),
            'category': request.POST.get('category', 'all'),
            'meta_title': request.POST.get('meta_title', '').strip(),
            'meta_description': request.POST.get('meta_description', '').strip(),
            'meta_keywords': request.POST.get('meta_keywords', '').strip(),
            'is_active': True,
            'created_at': datetime.now(),
        }
        
        result = col.insert_one(landing_data)
        
        return JsonResponse({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'SEO страница успешно создана'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def catalog_landings_api_toggle(request, landing_id):
    """API: переключить активность SEO страницы."""
    try:
        db = get_mongo_connection()
        col = db['catalog_landings']
        
        # Получаем текущий статус
        landing = col.find_one({'_id': ObjectId(landing_id)})
        if not landing:
            return JsonResponse({'success': False, 'error': 'SEO страница не найдена'}, status=404)
        
        current_status = landing.get('is_active', True)
        new_status = not current_status
        
        col.update_one(
            {'_id': ObjectId(landing_id)},
            {'$set': {'is_active': new_status}}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'SEO страница {"активирована" if new_status else "деактивирована"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def catalog_landings_api_delete(request, landing_id):
    """API: удалить SEO страницу."""
    try:
        db = get_mongo_connection()
        col = db['catalog_landings']
        
        result = col.delete_one({'_id': ObjectId(landing_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'success': False, 'error': 'SEO страница не найдена'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'SEO страница удалена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def catalog_landings_api_get(request, landing_id):
    """API: получить одну SEO страницу для редактирования."""
    try:
        db = get_mongo_connection()
        col = db['catalog_landings']
        
        landing = col.find_one({'_id': ObjectId(landing_id)})
        if not landing:
            return JsonResponse({'success': False, 'error': 'SEO страница не найдена'}, status=404)
        
        landing['_id'] = str(landing['_id'])
        return JsonResponse({'success': True, 'item': landing})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def catalog_landings_api_update(request, landing_id):
    """API: обновить SEO страницу."""
    try:
        db = get_mongo_connection()
        col = db['catalog_landings']
        
        # Проверяем существование страницы
        landing = col.find_one({'_id': ObjectId(landing_id)})
        if not landing:
            return JsonResponse({'success': False, 'error': 'SEO страница не найдена'}, status=404)
        
        update = {}
        
        if 'name' in request.POST:
            update['name'] = request.POST.get('name', '').strip()
        
        if 'slug' in request.POST:
            slug = request.POST.get('slug', '').strip()
            if slug and slug != landing.get('slug'):
                # Проверяем уникальность нового slug
                if col.find_one({'slug': slug, '_id': {'$ne': ObjectId(landing_id)}}):
                    return JsonResponse({'success': False, 'error': 'Страница с таким slug уже существует'}, status=400)
                update['slug'] = slug
        
        if 'kind' in request.POST:
            update['kind'] = request.POST.get('kind', 'newbuild')
        
        if 'category' in request.POST:
            update['category'] = request.POST.get('category', 'all')
        
        if 'meta_title' in request.POST:
            update['meta_title'] = request.POST.get('meta_title', '').strip()
        
        if 'meta_description' in request.POST:
            update['meta_description'] = request.POST.get('meta_description', '').strip()
        
        if 'meta_keywords' in request.POST:
            update['meta_keywords'] = request.POST.get('meta_keywords', '').strip()
        
        # Обновляем страницу
        result = col.update_one(
            {'_id': ObjectId(landing_id)},
            {'$set': update}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'success': False, 'error': 'SEO страница не найдена'}, status=404)
        
        return JsonResponse({'success': True, 'message': 'SEO страница обновлена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

