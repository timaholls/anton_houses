from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/api/', views.catalog_api, name='catalog_api'),
    path('api/catalog/', views.catalog_api, name='catalog_api_alt'),
    path('api/secondary/', views.secondary_api, name='secondary_api'),
    path('articles/', views.articles, name='articles'),
    path('articles/<slug:slug>/', views.article_detail, name='article_detail'),
    path('api/articles/<int:article_id>/view/', views.article_view_api, name='article_view_api'),
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    path('complex/<int:complex_id>/', views.detail, name='detail'),
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

    # Вакансии
    path('vacancies/', views.vacancies, name='vacancies'),
    path('vacancies/<slug:slug>/', views.vacancy_detail, name='vacancy_detail'),

    # Офисы продаж
    path('offices/', views.offices, name='offices'),
    path('offices/<slug:slug>/', views.office_detail, name='office_detail'),

    # Видеообзоры
    path('videos/', views.videos, name='videos'),
    path('videos/<int:video_id>/', views.video_detail, name='video_detail'),
    path('api/videos/objects/', views.videos_objects_api, name='videos_objects_api'),

    
    # Ипотека
    path('mortgage/', views.mortgage, name='mortgage'),
    
    # Акции
    path('offers/', views.all_offers, name='all_offers'),
    path('offers/<int:offer_id>/', views.offer_detail, name='offer_detail'),
    path('team/', views.team, name='team'),
    path('team/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('team/<int:employee_id>/properties/', views.agent_properties, name='agent_properties'),
    path('future-complexes/', views.future_complexes, name='future_complexes'),
    path('future-complexes/<int:complex_id>/', views.future_complex_detail, name='future_complex_detail'),
] 