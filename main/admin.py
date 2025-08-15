from django.contrib import admin
from .models import ResidentialComplex, Article, Tag, Author, CompanyInfo, CatalogLanding, SecondaryProperty
from .models import Vacancy
from .models import BranchOffice, Employee
from .models import ResidentialVideo, VideoComment, MortgageProgram, SpecialOffer

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
    list_display = ['title', 'author', 'category', 'published_date', 'is_featured', 'show_on_home', 'views_count']
    list_filter = ['category', 'is_featured', 'show_on_home', 'published_date', 'tags', 'author']
    search_fields = ['title', 'content', 'excerpt']
    list_editable = ['is_featured', 'show_on_home']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['published_date', 'updated_date', 'views_count', 'likes_count', 'comments_count']
    filter_horizontal = ['tags', 'related_articles']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'image')
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
    fields = ('full_name', 'position', 'photo', 'phone', 'email', 'is_active')

@admin.register(BranchOffice)
class BranchOfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'address', 'phone', 'is_active']
    list_filter = ['city', 'is_active']
    search_fields = ['name', 'city', 'address']
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'city', 'address', 'phone', 'email', 'schedule', 'is_active')
        }),
        ('Медиа', {
            'fields': ('image', 'photo')
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
    list_display = ['full_name', 'position', 'branch', 'is_active']
    list_filter = ['branch', 'position', 'is_active']
    search_fields = ['full_name', 'position']


class VideoCommentInline(admin.TabularInline):
    model = VideoComment
    extra = 0
    fields = ('name', 'rating', 'text', 'is_approved', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(ResidentialVideo)
class ResidentialVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'residential_complex', 'views_count', 'published_date', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured', 'published_date', 'residential_complex__city']
    search_fields = ['title', 'description', 'residential_complex__name']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['related_videos']
    readonly_fields = ['views_count', 'published_date', 'updated_date']

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'residential_complex', 'description', 'is_active', 'is_featured')
        }),
        ('Видео и превью', {
            'fields': ('video_url', 'video_file', 'thumbnail')
        }),
        ('Похожие видео', {
            'fields': ('related_videos',)
        }),
        ('Статистика', {
            'fields': ('views_count', 'published_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )

    inlines = [VideoCommentInline]

@admin.register(VideoComment)
class VideoCommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'video', 'rating', 'created_at', 'is_approved']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['name', 'text', 'video__title']

@admin.register(MortgageProgram)
class MortgageProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate', 'is_active']
    list_editable = ['rate', 'is_active']
    search_fields = ['name']

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'residential_complex', 'is_active', 'priority']
    list_filter = ['is_active', 'residential_complex__city']
    search_fields = ['title', 'description', 'residential_complex__name']
    list_editable = ['is_active', 'priority']
    fields = ('residential_complex', 'title', 'description', 'image', 'is_active', 'priority')
