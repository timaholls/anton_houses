"""Views для управления контентом и компанией"""
from django.shortcuts import render
from ..services.mongo_service import get_mongo_connection


def content_management(request):
    """Интерфейс управления контентом"""
    return render(request, 'main/content_management.html')


def company_management(request):
    """Интерфейс управления компанией"""
    return render(request, 'main/company_management.html')


def manual_matching(request):
    """Интерфейс ручного сопоставления данных из MongoDB"""
    return render(request, 'main/manual_matching.html')

