"""Views для офисов продаж"""
from django.shortcuts import render
from django.http import Http404
from django.core.paginator import Paginator
from ..services.mongo_service import get_mongo_connection
from ..s3_service import PLACEHOLDER_IMAGE_URL


def offices(request):
    """Список офисов продаж - читает из MongoDB"""
    db = get_mongo_connection()
    city = request.GET.get('city', '')
    
    query = {'is_active': True}
    if city:
        query['city'] = {'$regex': city, '$options': 'i'}
    
    offices_list = list(db['branch_offices'].find(query).sort('name', 1))
    
    # Получаем уникальные города
    all_offices = list(db['branch_offices'].find({'is_active': True}))
    cities = list(set(o.get('city', '') for o in all_offices if o.get('city')))
    
    paginator = Paginator(offices_list, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'offices': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'cities': cities,
        'filters': {
            'city': city,
        },
        'PLACEHOLDER_IMAGE_URL': PLACEHOLDER_IMAGE_URL,
    }
    return render(request, 'main/offices.html', context)


def office_detail(request, slug):
    """Детальная страница офиса с сотрудниками - читает из MongoDB"""
    db = get_mongo_connection()
    office = db['branch_offices'].find_one({'slug': slug, 'is_active': True})
    
    if not office:
        raise Http404("Офис не найден")
    
    # Получаем сотрудников этого офиса
    # Предполагается что у сотрудников есть поле office_id
    employees = list(db['employees'].find({
        'is_active': True
    }).sort('full_name', 1))
    # Подготовим данные сотрудников для шаблона
    for emp in employees:
        try:
            emp['id'] = str(emp.get('_id'))
        except Exception:
            emp['id'] = ''
        # Подставим slug текущего офиса, чтобы была рабочая ссылка на филиал
        emp['branch_slug'] = office.get('slug')

    context = {
        'office': office,
        'employees': employees,
        'PLACEHOLDER_IMAGE_URL': PLACEHOLDER_IMAGE_URL,
    }
    return render(request, 'main/office_detail.html', context)

