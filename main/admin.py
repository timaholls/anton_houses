from django.contrib import admin
from django.db import models
from django.http import JsonResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import ResidentialComplex, Article, Tag, Author, CompanyInfo, CatalogLanding, SecondaryProperty, Category, Gallery, FutureComplex
from .models import Vacancy
from .models import BranchOffice, Employee, EmployeeReview
from .models import MortgageProgram, SpecialOffer

@admin.register(ResidentialComplex)
class ResidentialComplexAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'city', 'district', 'price_from', 'status']
    list_filter = ['city', 'status', 'house_class']
    search_fields = ['name', 'city', 'district']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'city', 'district', 'street', 'commute_time', 'price_from', 'delivery_date', 'status', 'house_class', 'finishing', 'rooms')
        }),
        ('Координаты', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Детали', {
            'fields': ('total_apartments', 'completion_start', 'completion_end', 'developer', 'studio_price', 'one_room_price', 'two_room_price', 'three_room_price', 'four_room_price')
        }),
        ('Витрина каталога', {
            'fields': ('highlight_sale', 'highlight_recommended')
        }),
    )

@admin.register(SecondaryProperty)
class SecondaryPropertyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'city', 'district', 'house_type']
    list_filter = ['city', 'house_type']
    search_fields = ['name', 'city', 'district']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'price', 'city', 'district', 'street', 'commute_time', 'house_type', 'area', 'rooms', 'description', 'agent')
        }),
        ('Координаты', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Витрина каталога', {
            'fields': ('highlight_sale', 'highlight_recommended')
        }),
    )


@admin.register(FutureComplex)
class FutureComplexAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'district', 'delivery_date', 'price_from', 'is_active', 'is_featured']
    list_filter = ['city', 'district', 'is_active', 'is_featured', 'delivery_date', 'created_at']
    search_fields = ['name', 'city', 'district', 'street', 'developer']
    list_editable = ['is_active', 'is_featured']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'city', 'district', 'street')
        }),
        ('Цена и площадь', {
            'fields': ('price_from', 'price_to', 'area_from', 'area_to', 'rooms')
        }),
        ('Сроки и застройщик', {
            'fields': ('delivery_date', 'developer')
        }),
        ('Дополнительная информация', {
            'fields': ('house_class', 'is_active', 'is_featured')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_name', 'founder_name', 'is_active']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('company_name', 'founder_name', 'founder_position')
        }),
        ('Контент', {
            'fields': ('quote', 'description')
        }),
        ('Настройки', {
            'fields': ('is_active',)
        }),
    )
    
    def has_add_permission(self, request):
        # Разрешаем создать только одну запись
        return not CompanyInfo.objects.exists()


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'category', 'object_id', 'is_main', 'is_active', 'order', 'created_at']
    list_filter = ['content_type', 'category', 'is_active', 'is_main', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_main', 'is_active', 'order']
    readonly_fields = ['created_at']
    change_list_template = 'admin/gallery/gallery_changelist.html'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content_type', 'description')
        }),
        ('Контент', {
            'fields': ('image', 'video_url'),
            'classes': ('collapse',)
        }),
        ('Связи', {
            'fields': ('category', 'object_id')
        }),
        ('Настройки', {
            'fields': ('order', 'is_main', 'is_active')
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload/', self.admin_site.admin_view(self.upload_view), name='gallery_upload'),
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='gallery_bulk_upload'),
            path('get-objects/', self.admin_site.admin_view(self.get_objects_view), name='gallery_get_objects'),
            path('get-content/', self.admin_site.admin_view(self.get_content_view), name='gallery_get_content'),
            path('save-content/', self.admin_site.admin_view(self.save_content_view), name='gallery_save_content'),
            path('update-content/', self.admin_site.admin_view(self.update_content_view), name='gallery_update_content'),
            path('delete-content/', self.admin_site.admin_view(self.delete_content_view), name='gallery_delete_content'),
        ]
        return custom_urls + urls
    
    def upload_view(self, request):
        """Drag & Drop загрузка изображений"""
        if request.method == 'POST':
            try:
                files = request.FILES.getlist('images')
                category = request.POST.get('category')
                object_id = request.POST.get('object_id')
                
                created_count = 0
                for i, file in enumerate(files):
                    if file:
                        Gallery.objects.create(
                            title=f"Изображение {i+1}",
                            image=file,
                            category=category,
                            object_id=object_id,
                            order=i
                        )
                        created_count += 1
                
                messages.success(request, f'Загружено {created_count} изображений')
                return JsonResponse({'success': True, 'count': created_count})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return TemplateResponse(request, 'admin/gallery/upload.html', {
            'title': 'Загрузка изображений',
            'categories': Gallery.CATEGORY_CHOICES,
        })
    
    def bulk_upload_view(self, request):
        """Массовая загрузка изображений"""
        if request.method == 'POST':
            try:
                files = request.FILES.getlist('images')
                category = request.POST.get('category')
                object_id = request.POST.get('object_id')
                
                created_count = 0
                for i, file in enumerate(files):
                    if file:
                        Gallery.objects.create(
                            title=file.name,
                            image=file,
                            category=category,
                            object_id=object_id,
                            order=i
                        )
                        created_count += 1
                
                messages.success(request, f'Загружено {created_count} изображений')
                return JsonResponse({'success': True, 'count': created_count})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return TemplateResponse(request, 'admin/gallery/bulk_upload.html', {
            'title': 'Массовая загрузка изображений',
            'categories': Gallery.CATEGORY_CHOICES,
        })
    
    def get_objects_view(self, request):
        """Получить список объектов по категории"""
        from django.http import JsonResponse
        from django.db.models import F
        from .models import ResidentialComplex, SecondaryProperty, Employee, Article, SpecialOffer, BranchOffice, CompanyInfo
        
        print(f"get_objects_view called with category: {request.GET.get('category')}")
        
        category = request.GET.get('category')
        objects = []
        
        try:
            if category == 'residential_complex':
                objects = list(ResidentialComplex.objects.values('id', 'name'))
            elif category == 'secondary_property':
                objects = list(SecondaryProperty.objects.values('id', 'name'))
            elif category == 'employee':
                objects = list(Employee.objects.values('id', 'full_name').annotate(name=F('full_name')))
            elif category == 'article':
                objects = list(Article.objects.values('id', 'title').annotate(name=F('title')))
            elif category == 'special_offer':
                objects = list(SpecialOffer.objects.values('id', 'title').annotate(name=F('title')))
            elif category == 'office':
                objects = list(BranchOffice.objects.values('id', 'name'))
            elif category == 'company':
                company = CompanyInfo.objects.first()
                if company:
                    objects = [{'id': company.id, 'name': company.company_name}]
            elif category == 'employee_video':
                objects = list(Employee.objects.values('id', 'full_name').annotate(name=F('full_name')))
            elif category == 'residential_video':
                objects = list(ResidentialComplex.objects.values('id', 'name'))
            elif category == 'secondary_video':
                objects = list(SecondaryProperty.objects.values('id', 'name'))
            
            return JsonResponse({'success': True, 'objects': objects})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def get_content_view(self, request):
        """Получить существующий контент объекта"""
        from django.http import JsonResponse
        from django.conf import settings
        
        category = request.GET.get('category')
        object_id = request.GET.get('object_id')
        content_type = request.GET.get('content_type', 'image')
        
        try:
            print(f"Fetching content for category: {category}, object_id: {object_id}, content_type: {content_type}")
            content = Gallery.objects.filter(
                category=category,
                object_id=object_id,
                content_type=content_type
            ).values('id', 'title', 'content_type', 'order', 'is_main', 'is_active', 'created_at', 'image', 'video_url', 'description')
            
            print(f"Found {content.count()} items in database")
            for item in content:
                print(f"DB Item: {item}")
            
            # Преобразуем QuerySet в список и добавляем URL изображений
            content_list = []
            for item in content:
                content_item = dict(item)
                
                # Обрабатываем изображения
                if item['image']:
                    gallery_obj = Gallery.objects.get(id=item['id'])
                    try:
                        image_url = request.build_absolute_uri(gallery_obj.image.url) if gallery_obj.image else None
                        content_item['image_url'] = image_url
                        print(f"Generated image URL: {image_url}")
                    except Exception as e:
                        print(f"Error generating image URL: {e}")
                        content_item['image_url'] = None
                
                # Обрабатываем видео URL (добавляем всегда, если есть)
                if item['video_url']:
                    content_item['video_url'] = item['video_url']
                    print(f"Found video URL: {item['video_url']}")
                
                # Убрано - больше не поддерживается загрузка видео файлов
                
                # Video thumbnails removed
                
                content_list.append(content_item)
            
            return JsonResponse({'success': True, 'content': content_list})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def save_content_view(self, request):
        """Сохранить новый контент"""
        from django.http import JsonResponse
        from django.core.files.uploadedfile import UploadedFile
        
        try:
            content_type = request.POST.get('content_type')
            category = request.POST.get('category')
            object_id = request.POST.get('object_id')
            video_url = request.POST.get('video_url', '')
            
            # Обрабатываем файлы
            files = request.FILES.getlist('files')
            
            if content_type == 'image':
                # Получаем индивидуальные данные для каждого файла
                titles = request.POST.getlist('titles')
                descriptions = request.POST.getlist('descriptions')
                transliterated_titles = request.POST.getlist('transliterated_titles')
                
                # Создаем записи для изображений
                for i, file in enumerate(files):
                    title = titles[i] if i < len(titles) else f"Изображение {i+1}"
                    description = descriptions[i] if i < len(descriptions) else ""
                    transliterated_title = transliterated_titles[i] if i < len(transliterated_titles) else f"image-{i+1}"
                    
                    # Проверяем, является ли этот файл главным
                    is_main = request.POST.get(f'is_main_{i}') == 'true'
                    
                    Gallery.objects.create(
                        title=title,
                        content_type='image',
                        image=file,
                        category=category,
                        object_id=object_id,
                        description=description,
                        order=i,
                        is_main=is_main,
                        is_active=True
                    )
            elif content_type == 'video':
                # Создаем запись для видео
                gallery_item = Gallery.objects.create(
                    title="Видео",
                    content_type='video',
                    video_url=video_url,
                    category=category,
                    object_id=object_id,
                    description="Видео из YouTube",
                    is_main=True,
                    is_active=True
                )
                
                # Убрано - больше не поддерживается загрузка видео файлов
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def update_content_view(self, request):
        """Обновить существующий контент"""
        from django.http import JsonResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            file_id = request.POST.get('file_id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            is_main = request.POST.get('is_main') == 'true'
            video_url = request.POST.get('video_url', '')
            
            logger.info(f"Updating gallery item {file_id}: title='{title}', description='{description}', is_main={is_main}")
            
            # Находим объект галереи
            gallery_item = Gallery.objects.get(id=file_id)
            logger.info(f"Found gallery item: current title='{gallery_item.title}', current description='{gallery_item.description}'")
            
            # Обновляем поля
            gallery_item.title = title
            gallery_item.description = description
            gallery_item.video_url = video_url
            logger.info(f"Updated fields: new title='{gallery_item.title}', new description='{gallery_item.description}', video_url='{gallery_item.video_url}'")
            
            
            # Если этот элемент становится главным, снимаем флаг с других
            if is_main:
                Gallery.objects.filter(
                    category=gallery_item.category,
                    object_id=gallery_item.object_id
                ).update(is_main=False)
            
            gallery_item.is_main = is_main
            
            # Сохраняем изменения
            gallery_item.save()
            logger.info(f"Gallery item {file_id} saved successfully")
            
            # Проверяем, что данные действительно сохранились
            gallery_item.refresh_from_db()
            logger.info(f"After save - title: '{gallery_item.title}', description: '{gallery_item.description}'")
            
            # Video thumbnails removed
            
            return JsonResponse({'success': True})
        except Gallery.DoesNotExist:
            error_msg = f"Gallery item with id {file_id} not found"
            logger.error(error_msg)
            return JsonResponse({'success': False, 'error': error_msg})
        except ValidationError as e:
            error_msg = f"Validation error: {e}"
            logger.error(error_msg)
            return JsonResponse({'success': False, 'error': str(e)})
        except ValueError as e:
            error_msg = f"Value error: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({'success': False, 'error': str(e)})
        except Exception as e:
            error_msg = f"Error updating gallery item {file_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    
    def delete_content_view(self, request):
        """Удалить контент"""
        from django.http import JsonResponse
        
        try:
            file_id = request.POST.get('file_id')
            
            # Находим и удаляем объект галереи
            gallery_item = Gallery.objects.get(id=file_id)
            gallery_item.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def changelist_view(self, request, extra_context=None):
        """Переопределяем changelist_view для использования нашего шаблона"""
        from django.template.response import TemplateResponse
        
        # Получаем стандартный контекст
        response = super().changelist_view(request, extra_context)
        
        # Если это обычный запрос (не AJAX), используем наш шаблон
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Сохраняем весь контекст из стандартного response
            context = response.context_data.copy()
            context.update({
                'title': 'Управление галереей',
            })
            return TemplateResponse(request, 'admin/gallery/gallery_changelist.html', context)
        
        return response




@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'position', 'articles_count', 'total_views', 'total_likes']
    search_fields = ['name', 'position', 'description']
    readonly_fields = ['articles_count', 'total_views', 'total_likes']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'position', 'description')
        }),
        ('Статистика', {
            'fields': ('articles_count', 'total_views', 'total_likes'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Настройки', {
            'fields': ('is_active',)
        }),
    )
    
    def get_search_results(self, request, queryset, search_term):
        """Поддержка поиска для autocomplete"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'article_type', 'author', 'category', 'published_date', 'is_featured', 'show_on_home', 'views_count']
    list_filter = ['article_type', 'category', 'is_featured', 'show_on_home', 'published_date', 'tags', 'author']
    search_fields = ['title', 'content', 'excerpt']
    list_editable = ['is_featured', 'show_on_home']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['published_date', 'updated_date', 'views_count', 'likes_count', 'comments_count']
    filter_horizontal = ['tags', 'related_articles']
    autocomplete_fields = ['category']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'article_type', 'slug', 'excerpt', 'content')
        }),
        ('Автор и классификация', {
            'fields': ('author', 'category', 'is_featured', 'show_on_home', 'tags')
        }),
        ('Похожие статьи', {
            'fields': ('related_articles',),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('published_date', 'updated_date', 'views_count', 'likes_count', 'comments_count'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'articles_count']
    search_fields = ['name', 'h1_title', 'meta_title']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug')
        }),
        ('SEO настройки', {
            'fields': ('h1_title', 'meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
    
    def articles_count(self, obj):
        return obj.articles.count()
    articles_count.short_description = 'Количество статей'

@admin.register(CatalogLanding)
class CatalogLandingAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind', 'category', 'slug']
    list_filter = ['kind', 'category']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'meta_title', 'meta_description', 'meta_keywords']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'kind', 'category')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
    )


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'city', 'employment_type', 'is_active', 'published_date']
    list_filter = ['employment_type', 'city', 'department', 'is_active', 'published_date']
    search_fields = ['title', 'department', 'city', 'description', 'requirements']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['published_date', 'updated_date']

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'department', 'city', 'employment_type', 'is_active')
        }),
        ('Вознаграждение', {
            'fields': ('salary_from', 'salary_to', 'currency')
        }),
        ('Контент', {
            'fields': ('description', 'responsibilities', 'requirements', 'benefits')
        }),
        ('Контакты', {
            'fields': ('contact_email',)
        }),
        ('Даты', {
            'fields': ('published_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )

class EmployeeInline(admin.TabularInline):
    model = Employee
    extra = 1
    fields = ('full_name', 'position', 'phone', 'email', 'is_active')

@admin.register(BranchOffice)
class BranchOfficeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'city', 'address', 'phone', 'is_active', 'is_head_office']
    list_filter = ['city', 'is_active', 'is_head_office']
    search_fields = ['name', 'city', 'address']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_head_office']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'city', 'address', 'phone', 'email', 'schedule')
        }),
        ('Настройки', {
            'fields': ('is_active', 'is_head_office')
        }),

        ('Координаты', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Описание', {
            'fields': ('description',)
        }),
    )

    inlines = [EmployeeInline]

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'position', 'branch', 'experience_years', 'is_featured', 'is_active', 'reviews_count', 'average_rating']
    list_filter = ['branch', 'position', 'is_active', 'is_featured']
    search_fields = ['full_name', 'position', 'specializations']
    list_editable = ['is_featured', 'is_active']
    readonly_fields = ['created_at', 'reviews_count', 'average_rating']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'position', 'branch', 'is_featured', 'is_active')
        }),
        ('Видео', {
            'fields': ('video_url', 'video_file'),
            'classes': ('collapse',)
        }),
        ('Опыт и специализация', {
            'fields': ('experience_years', 'description', 'achievements', 'specializations')
        }),
        ('Контакты', {
            'fields': ('phone', 'email')
        }),
        ('Статистика', {
            'fields': ('reviews_count', 'average_rating', 'created_at'),
            'classes': ('collapse',)
        }),
    )





@admin.register(EmployeeReview)
class EmployeeReviewAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee', 'rating', 'is_approved', 'is_published', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_published', 'created_at', 'employee']
    search_fields = ['name', 'text', 'employee__full_name']
    list_editable = ['is_approved', 'is_published']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_reviews', 'publish_reviews', 'unpublish_reviews']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('employee', 'name', 'email', 'phone', 'rating', 'text')
        }),
        ('Статус', {
            'fields': ('is_approved', 'is_published')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def approve_reviews(self, request, queryset):
        """Одобряет выбранные отзывы"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'Одобрено {updated} отзывов')
    approve_reviews.short_description = 'Одобрить выбранные отзывы'
    
    def publish_reviews(self, request, queryset):
        """Публикует одобренные отзывы"""
        updated = queryset.filter(is_approved=True).update(is_published=True)
        self.message_user(request, f'Опубликовано {updated} отзывов')
    publish_reviews.short_description = 'Опубликовать одобренные отзывы'
    
    def unpublish_reviews(self, request, queryset):
        """Снимает с публикации отзывы"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'Снято с публикации {updated} отзывов')
    unpublish_reviews.short_description = 'Снять с публикации'



@admin.register(MortgageProgram)
class MortgageProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate', 'is_active']
    list_editable = ['rate', 'is_active']
    search_fields = ['name']

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'residential_complex', 'is_active', 'priority', 'expires_at', 'is_expired_display']
    list_filter = ['is_active', 'residential_complex__city', 'created_at', 'expires_at']
    search_fields = ['title', 'description', 'residential_complex__name']
    list_editable = ['is_active', 'priority']
    readonly_fields = ['is_expired_display']
    actions = ['deactivate_expired']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('residential_complex', 'title', 'description')
        }),
        ('Настройки', {
            'fields': ('is_active', 'priority', 'expires_at')
        }),
        ('Статус', {
            'fields': ('is_expired_display',),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired_display(self, obj):
        if obj.is_expired:
            return 'Истекла'
        elif obj.expires_at:
            return 'Активна'
        else:
            return 'Без срока'
    is_expired_display.short_description = 'Статус срока'
    
    def deactivate_expired(self, request, queryset):
        """Деактивирует истекшие предложения"""
        from django.utils import timezone
        expired_count = queryset.filter(
            is_active=True,
            expires_at__lt=timezone.now()
        ).update(is_active=False)
        
        self.message_user(
            request,
            f'Деактивировано {expired_count} истекших предложений'
        )
    deactivate_expired.short_description = 'Деактивировать истекшие предложения'
    
    def get_queryset(self, request):
        """Показывает только активные предложения по умолчанию"""
        qs = super().get_queryset(request)
        if request.GET.get('show_expired') != '1':
            from django.utils import timezone
            qs = qs.filter(
                models.Q(is_active=True) & 
                (models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))
            )
        return qs
