from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('api/catalog/', views.catalog_api, name='catalog_api'),
    path('articles/', views.articles, name='articles'),
    
    # Быстрые ссылки каталога
    path('catalog/completed/', views.catalog_completed, name='catalog_completed'),
    path('catalog/construction/', views.catalog_construction, name='catalog_construction'),
    path('catalog/economy/', views.catalog_economy, name='catalog_economy'),
    path('catalog/comfort/', views.catalog_comfort, name='catalog_comfort'),
    path('catalog/premium/', views.catalog_premium, name='catalog_premium'),
    path('catalog/finished/', views.catalog_finished, name='catalog_finished'),
    path('catalog/unfinished/', views.catalog_unfinished, name='catalog_unfinished'),
    
    # API для фильтров
    path('api/districts/', views.districts_api, name='districts_api'),
    path('api/streets/', views.streets_api, name='streets_api'),
] 