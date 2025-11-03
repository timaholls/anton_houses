from django.urls import path

# Импортируем все существующие функции из views.py
from .views import (
    # Auth
    login_view, logout_view,
    # Home
    home, privacy_policy, unsubscribe_page, services,
    # Catalog
    catalog, detail, secondary_detail_mongo, secondary_detail,
    catalog_completed, catalog_construction, catalog_economy, catalog_comfort,
    catalog_premium, catalog_finished, catalog_unfinished, catalog_landing,
    newbuild_index, secondary_index,
    # Articles
    articles, article_detail, tag_detail,
    # Vacancies
    vacancies, vacancy_detail,
    # Offices
    offices, office_detail,
    # Videos
    videos, video_detail,
    # Employees
    team, agent_properties, employee_detail,
    # Mortgage
    mortgage,
    # Offers
    all_offers, offer_detail,
    # Future complexes
    future_complexes, future_complex_detail,
    # Management
    content_management, company_management, manual_matching,
    # Not recommended
    not_recommended, not_recommended_detail,
    # API (реально существующие в views.py)
    catalog_api, secondary_api, secondary_api_list,
    districts_api, streets_api, article_view_api,
    # Manual Matching API
    get_unmatched_records, save_manual_match, get_unified_records,
    preview_manual_match,
    unified_delete, unified_get, unified_update, toggle_featured,
    domrf_create, delete_record, get_future_projects, create_future_project,
    get_domrf_data, delete_photo, get_apartment_stats,
    # Content Management API
    tags_api_list, tags_api_create, tags_api_get, tags_api_update, tags_api_toggle, tags_api_delete,
    categories_api_list, categories_api_create, categories_api_get, categories_api_update, categories_api_toggle, categories_api_delete,
    authors_api_list, authors_api_create, authors_api_toggle, authors_api_delete,
    articles_api_list, articles_api_create, articles_api_get, articles_api_update, articles_api_toggle, articles_api_delete,
    catalog_landings_api_list, catalog_landings_api_create, catalog_landings_api_get, catalog_landings_api_update,
    catalog_landings_api_toggle, catalog_landings_api_delete,
    # Company Management API
    employee_reviews_api, employee_review_toggle, employee_review_update, employee_review_delete,
    company_info_api_list, company_info_api_create, company_info_api_detail, company_info_api_update,
    company_info_api_toggle, company_info_api_delete, company_info_delete_image,
    branch_office_api_list, branch_office_api_create, branch_office_api_detail, branch_office_api_update,
    branch_office_api_toggle, branch_office_api_delete, branch_office_delete_image,
    employee_api_list, employee_api_create, employee_api_detail, employee_api_update,
    employee_api_toggle, employee_api_delete, employee_delete_image,
    # Vacancies API
    vacancies_api_list, vacancies_api_create, vacancies_api_toggle, vacancies_api_delete,
    # Videos API
    videos_objects_api, videos_create, videos_list, videos_by_complex, videos_toggle, videos_api_delete,
    # Mortgage API
    mortgage_programs_list, mortgage_programs_create, mortgage_programs_update, mortgage_programs_delete,
    # Promotions API
    promotions_create, promotions_list, promotions_delete, promotions_toggle,
    # Secondary API
    secondary_list, secondary_create, secondary_api_toggle, secondary_api_get, 
    secondary_api_update, secondary_api_delete,
)

# Импортируем функции из manual_matching_api
from .api.manual_matching_api import (
    get_location_options,
    delete_apartment_photo,
    delete_development_photo,
    delete_construction_photo,
    get_complexes_for_mortgage,
    get_mortgage_program,
    get_not_recommended_objects,
    get_future_project,
    update_future_project
)

# Импортируем функции из subscription_api
from .api.subscription_api import (
    subscribe_to_updates,
    unsubscribe_from_updates,
    get_subscription_stats
)

# Импортируем функции из apartment_booking_api
from .api.apartment_booking_api import (
    book_apartment,
    get_booking_stats,
    update_booking_status
)

# Импортируем view для квартир
from .view_modules.apartment_views import apartment_detail

app_name = 'main'

urlpatterns = [
    # ========== ОСНОВНЫЕ СТРАНИЦЫ ==========
    
    # Auth
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Home
    path('', home, name='home'),
    path('services/', services, name='services'),
    path('privacy/', privacy_policy, name='privacy'),
    path('unsubscribe/', unsubscribe_page, name='unsubscribe'),
    
    # ========== КАТАЛОГ ==========
    
    path('catalog/', catalog, name='catalog'),
    path('complex/<str:complex_id>/', detail, name='detail'),
    path('apartment/<str:complex_id>/<str:apartment_id>/', apartment_detail, name='apartment_detail'),
    
    # Быстрые ссылки каталога
    path('catalog/completed/', catalog_completed, name='catalog_completed'),
    path('catalog/construction/', catalog_construction, name='catalog_construction'),
    path('catalog/economy/', catalog_economy, name='catalog_economy'),
    path('catalog/comfort/', catalog_comfort, name='catalog_comfort'),
    path('catalog/premium/', catalog_premium, name='catalog_premium'),
    path('catalog/finished/', catalog_finished, name='catalog_finished'),
    path('catalog/unfinished/', catalog_unfinished, name='catalog_unfinished'),

    # Лэндинги каталога с SEO
    path('catalog/l/<str:slug>/', catalog_landing, name='catalog_landing'),
    path('newbuilds/', newbuild_index, name='newbuild_index'),
    
    # Вторичная недвижимость
    path('secondary/', secondary_index, name='secondary_index'),
    path('secondary/<int:pk>/', secondary_detail, name='secondary_detail'),
    path('secondary/<str:complex_id>/', secondary_detail_mongo, name='secondary_detail_mongo'),
    
    # ========== КОНТЕНТ ==========
    
    # Статьи
    path('articles/', articles, name='articles'),
    path('articles/<str:slug>/', article_detail, name='article_detail'),
    path('tag/<str:slug>/', tag_detail, name='tag_detail'),

    # Вакансии
    path('vacancies/', vacancies, name='vacancies'),
    path('vacancies/<str:slug>/', vacancy_detail, name='vacancy_detail'),

    # Офисы продаж
    path('offices/', offices, name='offices'),
    path('offices/<str:slug>/', office_detail, name='office_detail'),

    # Видеообзоры
    path('videos/', videos, name='videos'),
    path('videos/<str:video_id>/', video_detail, name='video_detail'),
    
    # Ипотека
    path('mortgage/', mortgage, name='mortgage'),
    
    # Акции
    path('offers/', all_offers, name='all_offers'),
    path('offers/<str:offer_id>/', offer_detail, name='offer_detail'),
    
    # Команда
    path('team/', team, name='team'),
    path('team/<str:employee_id>/', employee_detail, name='employee_detail'),
    path('team/<str:employee_id>/properties/', agent_properties, name='agent_properties'),
    
    # Будущие комплексы
    path('future-complexes/', future_complexes, name='future_complexes'),
    path('future-complexes/<str:complex_id>/', future_complex_detail, name='future_complex_detail'),
    
    # Не рекомендуем
    path('not-recommended/', not_recommended, name='not_recommended'),
    path('not-recommended/<str:object_id>/', not_recommended_detail, name='not_recommended_detail'),
    
    # ========== УПРАВЛЕНИЕ ==========
    
    path('content-management/', content_management, name='content_management'),
    path('company-management/', company_management, name='company_management'),
    path('manual-matching/', manual_matching, name='manual_matching'),
    
    # ========== MANUAL MATCHING API ==========
    
    path('api/manual-matching/unmatched/', get_unmatched_records, name='get_unmatched_records'),
    path('api/manual-matching/save/', save_manual_match, name='save_manual_match'),
    path('api/manual-matching/preview/', preview_manual_match, name='preview_manual_match'),
    path('api/manual-matching/unified/', get_unified_records, name='get_unified_records'),
    path('api/manual-matching/unified/<str:unified_id>/', unified_delete, name='unified_delete'),
    path('api/manual-matching/unified/<str:unified_id>/get/', unified_get, name='unified_get'),
    path('api/manual-matching/unified/<str:unified_id>/update/', unified_update, name='unified_update'),
    path('api/manual-matching/toggle-featured/', toggle_featured, name='toggle_featured'),
    path('api/manual-matching/records/', get_unmatched_records, name='get_unmatched_records_alt'),
    path('api/manual-matching/delete/', delete_record, name='delete_record'),
    path('api/manual-matching/future-projects/', get_future_projects, name='get_future_projects'),
    path('api/manual-matching/future-projects/<str:project_id>/', get_future_project, name='get_future_project'),
    path('api/manual-matching/future-projects/<str:project_id>/update/', update_future_project, name='update_future_project'),
    path('api/manual-matching/create-future-project/', create_future_project, name='create_future_project'),
    path('api/manual-matching/domrf-data/<str:domrf_id>/', get_domrf_data, name='get_domrf_data'),
    path('api/manual-matching/delete-photo/', delete_photo, name='delete_photo'),
    path('api/manual-matching/delete-apartment-photo/', delete_apartment_photo, name='delete_apartment_photo'),
    path('api/manual-matching/delete-development-photo/', delete_development_photo, name='delete_development_photo'),
    path('api/manual-matching/delete-construction-photo/', delete_construction_photo, name='delete_construction_photo'),
    path('api/manual-matching/apartment-stats/<str:domrf_id>/', get_apartment_stats, name='get_apartment_stats'),
    path('api/manual-matching/location-options/', get_location_options, name='get_location_options'),
    path('api/domrf/create/', domrf_create, name='domrf_create'),
    path('api/not-recommended/', get_not_recommended_objects, name='get_not_recommended_objects'),
    
    # ========== API (РАБОЧИЕ ЭНДПОИНТЫ) ==========
    
    # Catalog API
    path('catalog/api/', catalog_api, name='catalog_api'),
    path('api/catalog/', catalog_api, name='catalog_api_alt'),
    
    # Secondary API
    path('api/secondary/', secondary_api, name='secondary_api'),
    path('api/secondary/list/', secondary_api_list, name='secondary_api_list'),
    
    # Districts & Streets API
    path('api/districts/', districts_api, name='districts_api'),
    path('api/streets/', streets_api, name='streets_api'),
    
    # Articles API
    path('api/articles/<int:article_id>/view/', article_view_api, name='article_view_api'),
    
    # ========== CONTENT MANAGEMENT API ==========
    
    # Tags API
    path('api/tags/', tags_api_list, name='tags_api_list'),
    path('api/tags/create/', tags_api_create, name='tags_api_create'),
    path('api/tags/<str:tag_id>/', tags_api_get, name='tags_api_get'),
    path('api/tags/<str:tag_id>/update/', tags_api_update, name='tags_api_update'),
    path('api/tags/<str:tag_id>/toggle/', tags_api_toggle, name='tags_api_toggle'),
    path('api/tags/<str:tag_id>/delete/', tags_api_delete, name='tags_api_delete'),
    
    # Categories API
    path('api/categories/', categories_api_list, name='categories_api_list'),
    path('api/categories/create/', categories_api_create, name='categories_api_create'),
    path('api/categories/<str:category_id>/', categories_api_get, name='categories_api_get'),
    path('api/categories/<str:category_id>/update/', categories_api_update, name='categories_api_update'),
    path('api/categories/<str:category_id>/toggle/', categories_api_toggle, name='categories_api_toggle'),
    path('api/categories/<str:category_id>/delete/', categories_api_delete, name='categories_api_delete'),
    
    # Authors API
    path('api/authors/', authors_api_list, name='authors_api_list'),
    path('api/authors/create/', authors_api_create, name='authors_api_create'),
    path('api/authors/<str:author_id>/toggle/', authors_api_toggle, name='authors_api_toggle'),
    path('api/authors/<str:author_id>/', authors_api_delete, name='authors_api_delete'),
    
    # Articles API (Extended)
    path('api/articles/', articles_api_list, name='articles_api_list_mongo'),
    path('api/articles/create/', articles_api_create, name='articles_api_create'),
    path('api/articles/<str:article_id>/', articles_api_get, name='articles_api_get'),
    path('api/articles/<str:article_id>/update/', articles_api_update, name='articles_api_update'),
    path('api/articles/<str:article_id>/toggle/', articles_api_toggle, name='articles_api_toggle'),
    path('api/articles/<str:article_id>/delete/', articles_api_delete, name='articles_api_delete'),
    
    # Catalog Landings API
    path('api/catalog-landings/', catalog_landings_api_list, name='catalog_landings_api_list'),
    path('api/catalog-landings/create/', catalog_landings_api_create, name='catalog_landings_api_create'),
    path('api/catalog-landings/<str:landing_id>/', catalog_landings_api_get, name='catalog_landings_api_get'),
    path('api/catalog-landings/<str:landing_id>/update/', catalog_landings_api_update, name='catalog_landings_api_update'),
    path('api/catalog-landings/<str:landing_id>/toggle/', catalog_landings_api_toggle, name='catalog_landings_api_toggle'),
    path('api/catalog-landings/<str:landing_id>/delete/', catalog_landings_api_delete, name='catalog_landings_api_delete'),
    
    # ========== COMPANY MANAGEMENT API ==========
    
    # Company Info API
    path('api/company-info/', company_info_api_list, name='company_info_api_list'),
    path('api/company-info/create/', company_info_api_create, name='company_info_api_create'),
    path('api/company-info/<str:company_id>/get/', company_info_api_detail, name='company_info_api_detail'),
    path('api/company-info/<str:company_id>/update/', company_info_api_update, name='company_info_api_update'),
    path('api/company-info/<str:company_id>/toggle/', company_info_api_toggle, name='company_info_api_toggle'),
    path('api/company-info/<str:company_id>/delete-image/', company_info_delete_image, name='company_info_delete_image'),
    path('api/company-info/<str:company_id>/', company_info_api_delete, name='company_info_api_delete'),
    
    # Branch Office API
    path('api/branch-offices/', branch_office_api_list, name='branch_office_api_list'),
    path('api/branch-offices/create/', branch_office_api_create, name='branch_office_api_create'),
    path('api/branch-offices/<str:office_id>/get/', branch_office_api_detail, name='branch_office_api_detail'),
    path('api/branch-offices/<str:office_id>/update/', branch_office_api_update, name='branch_office_api_update'),
    path('api/branch-offices/<str:office_id>/toggle/', branch_office_api_toggle, name='branch_office_api_toggle'),
    path('api/branch-offices/<str:office_id>/delete-image/', branch_office_delete_image, name='branch_office_delete_image'),
    path('api/branch-offices/<str:office_id>/', branch_office_api_delete, name='branch_office_api_delete'),
    
    # Employee API
    path('api/employees/', employee_api_list, name='employee_api_list'),
    path('api/employees/create/', employee_api_create, name='employee_api_create'),
    path('api/employees/<str:employee_id>/get/', employee_api_detail, name='employee_api_detail'),
    path('api/employees/<str:employee_id>/update/', employee_api_update, name='employee_api_update'),
    path('api/employees/<str:employee_id>/toggle/', employee_api_toggle, name='employee_api_toggle'),
    path('api/employees/<str:employee_id>/delete-image/', employee_delete_image, name='employee_delete_image'),
    path('api/employees/<str:employee_id>/', employee_api_delete, name='employee_api_delete'),
    
    # Employee Reviews API
    path('api/employee-reviews/', employee_reviews_api, name='employee_reviews_api'),
    path('api/employee-reviews/<str:review_id>/toggle/', employee_review_toggle, name='employee_review_toggle'),
    path('api/employee-reviews/<str:review_id>/update/', employee_review_update, name='employee_review_update'),
    path('api/employee-reviews/<str:review_id>/delete/', employee_review_delete, name='employee_review_delete'),
    
    # ========== ДОПОЛНИТЕЛЬНЫЕ API ==========
    
    # Vacancies API
    path('api/vacancies/', vacancies_api_list, name='vacancies_api_list'),
    path('api/vacancies/create/', vacancies_api_create, name='vacancies_api_create'),
    path('api/vacancies/<str:vacancy_id>/toggle/', vacancies_api_toggle, name='vacancies_api_toggle'),
    path('api/vacancies/<str:vacancy_id>/', vacancies_api_delete, name='vacancies_api_delete'),
    
    # Videos API
    path('api/videos/', videos_create, name='videos_create'),
    path('api/videos/list/', videos_list, name='videos_list'),
    path('api/videos/objects/', videos_objects_api, name='videos_objects_api'),
    path('api/videos/by-complex/<str:complex_id>/', videos_by_complex, name='videos_by_complex'),
    path('api/videos/<str:video_id>/toggle/', videos_toggle, name='videos_toggle'),
    path('api/videos/<str:video_id>/', videos_api_delete, name='videos_api_delete'),
    
    # Mortgage Programs API
    path('api/mortgage-programs/', mortgage_programs_list, name='mortgage_programs_list'),
    path('api/mortgage-programs/create/', mortgage_programs_create, name='mortgage_programs_create'),
    path('api/mortgage-programs/complexes/', get_complexes_for_mortgage, name='get_complexes_for_mortgage'),
    path('api/mortgage-programs/<str:program_id>/get/', get_mortgage_program, name='get_mortgage_program'),
    path('api/mortgage-programs/<str:program_id>/update/', mortgage_programs_update, name='mortgage_programs_update'),
    path('api/mortgage-programs/<str:program_id>/', mortgage_programs_delete, name='mortgage_programs_delete'),
    
    # Promotions API
    path('api/promotions/', promotions_create, name='promotions_create'),
    path('api/promotions/list/', promotions_list, name='promotions_list'),
    path('api/promotions/<str:promo_id>/', promotions_delete, name='promotions_delete'),
    path('api/promotions/<str:promo_id>/toggle/', promotions_toggle, name='promotions_toggle'),
    
    # Secondary Properties API (Extended)
    path('api/secondary/list/', secondary_list, name='secondary_list'),
    path('api/secondary/create/', secondary_create, name='secondary_create'),
    path('api/secondary/<str:secondary_id>/toggle/', secondary_api_toggle, name='secondary_api_toggle'),
    path('api/secondary/<str:secondary_id>/', secondary_api_delete, name='secondary_api_delete'),
    path('api/secondary/<str:secondary_id>/get/', secondary_api_get, name='secondary_api_get'),
    path('api/secondary/<str:secondary_id>/update/', secondary_api_update, name='secondary_api_update'),
    
    # Subscription API
    path('api/subscribe/', subscribe_to_updates, name='subscribe_to_updates'),
    path('api/unsubscribe/', unsubscribe_from_updates, name='unsubscribe_from_updates'),
    path('api/subscription-stats/', get_subscription_stats, name='get_subscription_stats'),
    
    # Apartment Booking API
    path('api/book-apartment/', book_apartment, name='book_apartment'),
    path('api/booking-stats/', get_booking_stats, name='get_booking_stats'),
    path('api/booking/<str:booking_id>/update-status/', update_booking_status, name='update_booking_status'),
]
