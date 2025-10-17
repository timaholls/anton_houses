from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/api/', views.catalog_api, name='catalog_api'),
    path('api/catalog/', views.catalog_api, name='catalog_api_alt'),
    path('api/secondary/', views.secondary_api, name='secondary_api'),
    path('api/secondary/list/', views.secondary_api_list, name='secondary_api_list'),
    path('articles/', views.articles, name='articles'),
    path('articles/<slug:slug>/', views.article_detail, name='article_detail'),
    path('api/articles/<int:article_id>/view/', views.article_view_api, name='article_view_api'),
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    path('complex/<str:complex_id>/', views.detail, name='detail'),
    path('api/districts/', views.districts_api, name='districts_api'),
    path('api/streets/', views.streets_api, name='streets_api'),
    
    # Быстрые ссылки каталога
    path('catalog/completed/', views.catalog_completed, name='catalog_completed'),
    path('catalog/construction/', views.catalog_construction, name='catalog_construction'),
    path('catalog/economy/', views.catalog_economy, name='catalog_economy'),
    path('catalog/comfort/', views.catalog_comfort, name='catalog_comfort'),
    path('catalog/premium/', views.catalog_premium, name='catalog_premium'),
    path('catalog/finished/', views.catalog_finished, name='catalog_finished'),
    path('catalog/unfinished/', views.catalog_unfinished, name='catalog_unfinished'),

    # Политика конфиденциальности
    path('privacy/', views.privacy_policy, name='privacy'),

    # Лэндинги каталога с SEO
    path('catalog/l/<slug:slug>/', views.catalog_landing, name='catalog_landing'),
    path('newbuilds/', views.newbuild_index, name='newbuild_index'),
    path('secondary/', views.secondary_index, name='secondary_index'),
    path('secondary/<int:pk>/', views.secondary_detail, name='secondary_detail'),
    path('secondary/<str:complex_id>/', views.secondary_detail_mongo, name='secondary_detail_mongo'),

    # Вакансии
    path('vacancies/', views.vacancies, name='vacancies'),
    path('vacancies/<slug:slug>/', views.vacancy_detail, name='vacancy_detail'),

    # Офисы продаж
    path('offices/', views.offices, name='offices'),
    path('offices/<slug:slug>/', views.office_detail, name='office_detail'),

    # Видеообзоры
    path('videos/', views.videos, name='videos'),
    path('videos/<str:video_id>/', views.video_detail, name='video_detail'),
    # Вакансии (Mongo)
    path('api/vacancies/', views.vacancies_api_list, name='vacancies_api_list'),
    path('api/vacancies/create/', views.vacancies_api_create, name='vacancies_api_create'),
    path('api/videos/objects/', views.videos_objects_api, name='videos_objects_api'),
    # Videos API (Mongo)
    path('api/videos/', views.videos_create, name='videos_create'),
    path('api/videos/list/', views.videos_list, name='videos_list'),
    path('api/videos/by-complex/<str:complex_id>/', views.videos_by_complex, name='videos_by_complex'),
    path('api/videos/<str:video_id>/toggle/', views.videos_toggle, name='videos_toggle'),

    
    # Ипотека
    path('mortgage/', views.mortgage, name='mortgage'),
    
    # Акции
    path('offers/', views.all_offers, name='all_offers'),
    path('offers/<str:offer_id>/', views.offer_detail, name='offer_detail'),
    path('team/', views.team, name='team'),
    path('team/<str:employee_id>/', views.employee_detail, name='employee_detail'),
    path('team/<str:employee_id>/properties/', views.agent_properties, name='agent_properties'),
    path('future-complexes/', views.future_complexes, name='future_complexes'),
    path('future-complexes/<str:complex_id>/', views.future_complex_detail, name='future_complex_detail'),
    
    # Ручное сопоставление MongoDB
    path('manual-matching/', views.manual_matching, name='manual_matching'),
    path('api/manual-matching/unmatched/', views.get_unmatched_records, name='get_unmatched_records'),
    path('api/manual-matching/save/', views.save_manual_match, name='save_manual_match'),
    path('api/manual-matching/unified/', views.get_unified_records, name='get_unified_records'),
    path('api/manual-matching/unified/<str:unified_id>/', views.unified_delete, name='unified_delete'),
    path('api/manual-matching/toggle-featured/', views.toggle_featured, name='toggle_featured'),
    path('api/domrf/create/', views.domrf_create, name='domrf_create'),
    # Unified edit/get
    path('api/manual-matching/unified/<str:unified_id>/get/', views.unified_get, name='unified_get'),
    path('api/manual-matching/unified/<str:unified_id>/update/', views.unified_update, name='unified_update'),
    # Mortgage programs API (Mongo)
    path('api/mortgage-programs/', views.mortgage_programs_list, name='mortgage_programs_list'),
    path('api/mortgage-programs/create/', views.mortgage_programs_create, name='mortgage_programs_create'),
    path('api/mortgage-programs/<str:program_id>/update/', views.mortgage_programs_update, name='mortgage_programs_update'),
    path('api/mortgage-programs/<str:program_id>/', views.mortgage_programs_delete, name='mortgage_programs_delete'),
    # Promotions API
    path('api/promotions/', views.promotions_create, name='promotions_create'),
    path('api/promotions/list/', views.promotions_list, name='promotions_list'),
    path('api/promotions/<str:promo_id>/', views.promotions_delete, name='promotions_delete'),
    path('api/promotions/<str:promo_id>/toggle/', views.promotions_toggle, name='promotions_toggle'),
    # Secondary properties (Mongo)
    path('api/secondary/list/', views.secondary_list, name='secondary_list'),
    path('api/secondary/create/', views.secondary_create, name='secondary_create'),
    path('api/secondary/<str:secondary_id>/toggle/', views.secondary_api_toggle, name='secondary_api_toggle'),
    path('api/secondary/<str:secondary_id>/', views.secondary_api_delete, name='secondary_api_delete'),
    # Secondary get/update
    path('api/secondary/<str:secondary_id>/get/', views.secondary_api_get, name='secondary_api_get'),
    path('api/secondary/<str:secondary_id>/update/', views.secondary_api_update, name='secondary_api_update'),
    # Vacancies API
    path('api/vacancies/<str:vacancy_id>/toggle/', views.vacancies_api_toggle, name='vacancies_api_toggle'),
    path('api/vacancies/<str:vacancy_id>/', views.vacancies_api_delete, name='vacancies_api_delete'),
    # Videos API
    path('api/videos/<str:video_id>/', views.videos_api_delete, name='videos_api_delete'),
    
    # ========== Content Management (Tags, Authors, Categories, Articles, CatalogLandings) ==========
    path('content-management/', views.content_management, name='content_management'),
    
    # Tags API
    path('api/tags/', views.tags_api_list, name='tags_api_list'),
    path('api/tags/create/', views.tags_api_create, name='tags_api_create'),
    path('api/tags/<str:tag_id>/toggle/', views.tags_api_toggle, name='tags_api_toggle'),
    path('api/tags/<str:tag_id>/', views.tags_api_delete, name='tags_api_delete'),
    
    # Categories API
    path('api/categories/', views.categories_api_list, name='categories_api_list'),
    path('api/categories/create/', views.categories_api_create, name='categories_api_create'),
    path('api/categories/<str:category_id>/toggle/', views.categories_api_toggle, name='categories_api_toggle'),
    path('api/categories/<str:category_id>/', views.categories_api_delete, name='categories_api_delete'),
    
    # Authors API
    path('api/authors/', views.authors_api_list, name='authors_api_list'),
    path('api/authors/create/', views.authors_api_create, name='authors_api_create'),
    path('api/authors/<str:author_id>/toggle/', views.authors_api_toggle, name='authors_api_toggle'),
    path('api/authors/<str:author_id>/', views.authors_api_delete, name='authors_api_delete'),
    
    # Articles API (MongoDB)
    path('api/articles/', views.articles_api_list, name='articles_api_list_mongo'),
    path('api/articles/create/', views.articles_api_create, name='articles_api_create'),
    path('api/articles/<str:article_id>/toggle/', views.articles_api_toggle, name='articles_api_toggle'),
    path('api/articles/<str:article_id>/delete/', views.articles_api_delete, name='articles_api_delete'),
    
    # Catalog Landings API
    path('api/catalog-landings/', views.catalog_landings_api_list, name='catalog_landings_api_list'),
    path('api/catalog-landings/create/', views.catalog_landings_api_create, name='catalog_landings_api_create'),
    path('api/catalog-landings/<str:landing_id>/toggle/', views.catalog_landings_api_toggle, name='catalog_landings_api_toggle'),
    path('api/catalog-landings/<str:landing_id>/', views.catalog_landings_api_delete, name='catalog_landings_api_delete'),
    
    # ========== Company Management (CompanyInfo, BranchOffice, Employee) ==========
    path('company-management/', views.company_management, name='company_management'),
    
    # Company Info API
    path('api/company-info/', views.company_info_api_list, name='company_info_api_list'),
    path('api/company-info/create/', views.company_info_api_create, name='company_info_api_create'),
    path('api/company-info/<str:company_id>/get/', views.company_info_api_detail, name='company_info_api_detail'),
    path('api/company-info/<str:company_id>/update/', views.company_info_api_update, name='company_info_api_update'),
    path('api/company-info/<str:company_id>/toggle/', views.company_info_api_toggle, name='company_info_api_toggle'),
    path('api/company-info/<str:company_id>/', views.company_info_api_delete, name='company_info_api_delete'),
    
    # Branch Office API
    path('api/branch-offices/', views.branch_office_api_list, name='branch_office_api_list'),
    path('api/branch-offices/create/', views.branch_office_api_create, name='branch_office_api_create'),
    # ВАЖНО: уникальные пути, чтобы не конфликтовать с DELETE тем же паттерном
    path('api/branch-offices/<str:office_id>/get/', views.branch_office_api_detail, name='branch_office_api_detail'),
    path('api/branch-offices/<str:office_id>/update/', views.branch_office_api_update, name='branch_office_api_update'),
    path('api/branch-offices/<str:office_id>/toggle/', views.branch_office_api_toggle, name='branch_office_api_toggle'),
    path('api/branch-offices/<str:office_id>/', views.branch_office_api_delete, name='branch_office_api_delete'),
    
    # Employee API
    path('api/employees/', views.employee_api_list, name='employee_api_list'),
    path('api/employees/create/', views.employee_api_create, name='employee_api_create'),
    path('api/employees/<str:employee_id>/get/', views.employee_api_detail, name='employee_api_detail'),
    path('api/employees/<str:employee_id>/update/', views.employee_api_update, name='employee_api_update'),
    path('api/employees/<str:employee_id>/toggle/', views.employee_api_toggle, name='employee_api_toggle'),
    path('api/employees/<str:employee_id>/', views.employee_api_delete, name='employee_api_delete'),
    
    # Manual Matching API
    path('api/manual-matching/records/', views.get_unmatched_records, name='get_unmatched_records'),
    path('api/manual-matching/save/', views.save_manual_match, name='save_manual_match'),
    path('api/manual-matching/unified/', views.get_unified_records, name='get_unified_records'),
    path('api/manual-matching/delete/', views.delete_record, name='delete_record'),
    path('api/manual-matching/future-projects/', views.get_future_projects, name='get_future_projects'),
    path('api/manual-matching/create-future-project/', views.create_future_project, name='create_future_project'),
    path('api/manual-matching/domrf-data/<str:domrf_id>/', views.get_domrf_data, name='get_domrf_data'),
    path('api/manual-matching/delete-photo/', views.delete_photo, name='delete_photo'),
    path('api/manual-matching/apartment-stats/<str:domrf_id>/', views.get_apartment_stats, name='get_apartment_stats'),
] 