"""Views для статей и блога"""
import logging
from django.shortcuts import render
from django.http import Http404
from bson import ObjectId
from ..services.mongo_service import get_mongo_connection

logger = logging.getLogger(__name__)


def articles(request):
    """Страница статей - читает из MongoDB"""
    db = get_mongo_connection()
    category = request.GET.get('category', '')
    article_type = request.GET.get('type', '')  # По умолчанию показываем все типы

    # Получаем статьи по типу (если тип не указан, показываем все)
    query = {'is_active': True}
    if article_type:
        query['article_type'] = article_type

    # Дополнительная фильтрация по категории
    if category:
        category_obj = db['categories'].find_one({'slug': category, 'is_active': True})
        if category_obj:
            query['category_id'] = category_obj['_id']
    
    logger.info(f"Articles query: {query}")
    articles_list = list(db['articles'].find(query).sort('published_date', -1))
    logger.info(f"Found {len(articles_list)} articles")
    
    # Логируем каждую статью
    for article in articles_list:
        logger.info(f"Article: {article.get('title', 'No title')} - Type: {article.get('article_type', 'No type')} - Active: {article.get('is_active', 'No status')}")

    # Получаем статьи по категориям для отображения в секциях
    def get_articles_by_category_slug(slug, limit=3):
        cat = db['categories'].find_one({'slug': slug, 'is_active': True})
        if cat:
            category_query = {
                'category_id': cat['_id'],
                'is_active': True
            }
            if article_type:
                category_query['article_type'] = article_type
            return list(db['articles'].find(category_query).sort('published_date', -1).limit(limit))
        return []
    
    # Получаем все категории с их статьями
    all_categories_with_articles = []
    
    # Получаем все активные категории
    all_categories = list(db['categories'].find({'is_active': True}).sort('name', 1))
    
    for category in all_categories:
        # Получаем статьи для каждой категории
        category_query = {
            'category_id': category['_id'],
            'is_active': True
        }
        if article_type:
            category_query['article_type'] = article_type
            
        category_articles = list(db['articles'].find(category_query).sort('published_date', -1))
        
        if category_articles:  # Только если есть статьи в категории
            all_categories_with_articles.append({
                'category': {
                    'name': category.get('name', 'Категория'),
                    'slug': category.get('slug', ''),
                    'description': category.get('description', '')
                },
                'articles': category_articles
            })
    
    # Старые переменные для совместимости (если нужны)
    mortgage_articles = get_articles_by_category_slug('mortgage', 3)
    laws_articles = get_articles_by_category_slug('laws', 3)
    instructions_articles = get_articles_by_category_slug('instructions', 3)
    market_articles = get_articles_by_category_slug('market', 3)
    tips_articles = get_articles_by_category_slug('tips', 3)

    show_mortgage_section = len(mortgage_articles) > 0
    show_laws_section = len(laws_articles) > 0
    show_instructions_section = len(instructions_articles) > 0
    show_market_section = len(market_articles) > 0
    show_tips_section = len(tips_articles) > 0

    # Получаем все категории для фильтрации
    categories = list(db['categories'].find({'is_active': True}).sort('name', 1))

    # Получаем популярные теги
    popular_tags = list(db['tags'].find({'is_active': True}).limit(10))

    # Получаем рекомендуемые статьи для блока "Похожие статьи"
    featured_articles = list(db['articles'].find({
        'is_featured': True,
        'is_active': True
    }).sort('views_count', -1).limit(3))
    
    logger.info(f"Featured articles query: {{'is_featured': True, 'is_active': True}}")
    logger.info(f"Found {len(featured_articles)} featured articles")
    for article in featured_articles:
        logger.info(f"Featured: {article.get('title', 'No title')} - Featured: {article.get('is_featured', 'No status')} - Active: {article.get('is_active', 'No status')}")
    
    # Загружаем категории и теги для всех статей
    def enrich_articles_with_relations(articles_list):
        """Обогащает статьи данными категорий и тегов"""
        for article in articles_list:
            # Загружаем категорию
            if article.get('category_id'):
                article['category'] = db['categories'].find_one({'_id': article['category_id']})
            
            # Загружаем теги
            if article.get('tags'):
                tag_ids = article.get('tags', [])
                article['tags'] = list(db['tags'].find({'_id': {'$in': tag_ids}}))
            
            # Загружаем автора
            if article.get('author_id'):
                article['author'] = db['authors'].find_one({'_id': article['author_id']})
        
        return articles_list
    
    # Обогащаем все списки статей
    articles_list = enrich_articles_with_relations(articles_list)
    mortgage_articles = enrich_articles_with_relations(mortgage_articles)
    laws_articles = enrich_articles_with_relations(laws_articles)
    instructions_articles = enrich_articles_with_relations(instructions_articles)
    market_articles = enrich_articles_with_relations(market_articles)
    tips_articles = enrich_articles_with_relations(tips_articles)
    featured_articles = enrich_articles_with_relations(featured_articles)
    
    # Обогащаем статьи в категориях
    for category_data in all_categories_with_articles:
        category_data['articles'] = enrich_articles_with_relations(category_data['articles'])

    context = {
        'articles': articles_list,
        'all_categories_with_articles': all_categories_with_articles,  # Новая переменная
        'mortgage_articles': mortgage_articles,
        'laws_articles': laws_articles,
        'instructions_articles': instructions_articles,
        'market_articles': market_articles,
        'tips_articles': tips_articles,
        'show_mortgage_section': show_mortgage_section,
        'show_laws_section': show_laws_section,
        'show_instructions_section': show_instructions_section,
        'show_market_section': show_market_section,
        'show_tips_section': show_tips_section,
        'categories': categories,
        'current_category': category,
        'current_type': article_type,
        'popular_tags': popular_tags,
        'featured_articles': featured_articles,
    }
    return render(request, 'main/articles.html', context)


def article_detail(request, slug):
    """Детальная страница статьи - читает из MongoDB"""
    db = get_mongo_connection()
    article = db['articles'].find_one({'slug': slug, 'is_active': True})
    
    if not article:
        raise Http404("Статья не найдена")

    # Увеличиваем счетчик просмотров
    db['articles'].update_one(
        {'_id': article['_id']},
        {'$inc': {'views_count': 1}}
    )
    article['views_count'] = article.get('views_count', 0) + 1

    # Получаем категорию и автора
    if article.get('category_id'):
        article['category'] = db['categories'].find_one({'_id': article['category_id']})
    
    if article.get('author_id'):
        article['author'] = db['authors'].find_one({'_id': article['author_id']})
    # Обновляем статистику автора
        author_articles = list(db['articles'].find({'author_id': article['author_id'], 'is_active': True}))
        total_views = sum(a.get('views_count', 0) for a in author_articles)
        total_likes = sum(a.get('likes_count', 0) for a in author_articles)
        db['authors'].update_one(
            {'_id': article['author_id']},
            {'$set': {
                'articles_count': len(author_articles),
                'total_views': total_views,
                'total_likes': total_likes
            }}
        )

    # Получаем похожие статьи по категории
    related_articles = []
    if article.get('category_id'):
        related_articles = list(db['articles'].find({
            'category_id': article['category_id'],
            '_id': {'$ne': article['_id']},
            'is_active': True
        }).sort('published_date', -1).limit(3))
    
    # Если нет похожих, берем последние
    if not related_articles:
        related_articles = list(db['articles'].find({
            '_id': {'$ne': article['_id']},
            'is_active': True
        }).sort('published_date', -1).limit(3))

    # Получаем теги статьи
    article_tags = []
    if article.get('tags'):
        article_tags = list(db['tags'].find({'_id': {'$in': article['tags']}, 'is_active': True}))

    # Получаем популярные теги
    popular_tags = list(db['tags'].find({'is_active': True}).limit(10))

    context = {
        'article': article,
        'related_articles': related_articles,
        'article_tags': article_tags,
        'popular_tags': popular_tags,
    }
    return render(request, 'main/article_detail_new.html', context)


def tag_detail(request, slug):
    """Страница тега - читает из MongoDB"""
    db = get_mongo_connection()
    tag = db['tags'].find_one({'slug': slug, 'is_active': True})
    
    if not tag:
        raise Http404("Тег не найден")
    
    # Получаем статьи с этим тегом
    articles = list(db['articles'].find({
        'tags': tag['_id'],
        'is_active': True
    }).sort('published_date', -1))

    context = {
        'tag': tag,
        'articles': articles,
    }
    return render(request, 'main/tag_detail.html', context)

