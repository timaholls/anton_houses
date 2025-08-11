from django.contrib import admin
from .models import ResidentialComplex, Article, Tag, Author, CompanyInfo, CatalogLanding, SecondaryProperty

@admin.register(ResidentialComplex)
class ResidentialComplexAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'district', 'price_from', 'house_class', 'status', 'is_featured']
    list_filter = ['house_class', 'status', 'is_featured', 'city', 'finishing']
    search_fields = ['name', 'city', 'district', 'street']
    list_editable = ['is_featured', 'price_from']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'price_from', 'city', 'district', 'street', 'commute_time', 'image')
        }),
        ('Характеристики', {
            'fields': ('house_type', 'area_from', 'area_to', 'house_class', 'finishing', 'rooms', 'status')
        }),
        ('Детальная информация', {
            'fields': ('total_apartments', 'completion_start', 'completion_end', 'has_completed', 'developer')
        }),
        ('Цены по типам квартир', {
            'fields': ('studio_price', 'one_room_price', 'two_room_price', 'three_room_price', 'four_room_price')
        }),
        ('Дополнительные изображения', {
            'fields': ('image_2', 'image_3', 'image_4')
        }),
        ('Настройки', {
            'fields': ('is_featured', 'delivery_date')
        }),
    )

@admin.register(SecondaryProperty)
class SecondaryPropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'house_type', 'city', 'district', 'price']
    list_filter = ['house_type', 'city']
    search_fields = ['name', 'city', 'district', 'street']

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'founder_name', 'is_active']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('company_name', 'founder_name', 'founder_position', 'founder_photo')
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

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'articles_count', 'total_views', 'total_likes']
    search_fields = ['name', 'position', 'description']
    readonly_fields = ['articles_count', 'total_views', 'total_likes']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'photo', 'position', 'description')
        }),
        ('Статистика', {
            'fields': ('articles_count', 'total_views', 'total_likes'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'published_date', 'is_featured', 'views_count']
    list_filter = ['category', 'is_featured', 'published_date', 'tags', 'author']
    search_fields = ['title', 'content', 'excerpt']
    list_editable = ['is_featured']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['published_date', 'updated_date', 'views_count', 'likes_count', 'comments_count']
    filter_horizontal = ['tags', 'related_articles']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'image')
        }),
        ('Автор и классификация', {
            'fields': ('author', 'category', 'is_featured', 'tags')
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
