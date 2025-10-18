"""Views для вакансий"""
from django.shortcuts import render
from django.http import Http404
from django.core.paginator import Paginator
from datetime import datetime
from bson import ObjectId
from ..services.mongo_service import get_mongo_connection


def vacancies(request):
    """Список вакансий (MongoDB)"""
    try:
        db = get_mongo_connection()
        col = db['vacancies']
        q = {'is_active': True}
        docs = list(col.find(q).sort('published_date', -1))

        # Адаптеры к ожиданиям шаблона
        def to_item(d):
            class V:  # простой адаптер
                pass
            v = V()
            v.id = str(d.get('_id'))
            v.slug = d.get('slug') or (str(d['_id']) if d.get('_id') else '')
            v.title = d.get('title', '')
            v.department = d.get('department', '')
            v.city = d.get('city', 'Уфа')
            v.employment_type = d.get('employment_type', 'fulltime')
            # display
            employment_map = {
                'fulltime': 'Полная занятость',
                'parttime': 'Частичная занятость',
                'contract': 'Контракт',
                'intern': 'Стажировка',
                'remote': 'Удаленная работа',
            }
            v.get_employment_type_display = employment_map.get(v.employment_type, v.employment_type)
            v.salary_from = d.get('salary_from')
            v.salary_to = d.get('salary_to')
            v.currency = d.get('currency', 'RUB')
            v.published_date = d.get('published_date') or d.get('created_at') or datetime.utcnow()
            return v

        items = [to_item(d) for d in docs]

        page = int(request.GET.get('page', 1))
        paginator = Paginator(items, 10)
        page_obj = paginator.get_page(page)

        context = {
        'vacancies': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        }
        return render(request, 'main/vacancies.html', context)
    except Exception:
        # fallback: пусто
        paginator = Paginator([], 10)
        page_obj = paginator.get_page(1)
        return render(request, 'main/vacancies.html', {'vacancies': page_obj, 'page_obj': page_obj, 'paginator': paginator})


def vacancy_detail(request, slug):
    """Детальная страница вакансии (MongoDB)"""
    db = get_mongo_connection()
    col = db['vacancies']
    doc = col.find_one({'slug': slug}) or col.find_one({'_id': ObjectId(slug)})
    if not doc:
        raise Http404('Вакансия не найдена')

    class V: pass
    v = V()
    v.id = str(doc.get('_id'))
    v.slug = doc.get('slug') or v.id
    v.title = doc.get('title', '')
    v.department = doc.get('department', '')
    v.city = doc.get('city', 'Уфа')
    v.employment_type = doc.get('employment_type', 'fulltime')
    employment_map = {
        'fulltime': 'Полная занятость',
        'parttime': 'Частичная занятость',
        'contract': 'Контракт',
        'intern': 'Стажировка',
        'remote': 'Удаленная работа',
    }
    v.get_employment_type_display = employment_map.get(v.employment_type, v.employment_type)
    v.salary_from = doc.get('salary_from')
    v.salary_to = doc.get('salary_to')
    v.currency = doc.get('currency', 'RUB')
    v.description = doc.get('description', '')
    v.responsibilities = doc.get('responsibilities', '')
    v.requirements = doc.get('requirements', '')
    v.benefits = doc.get('benefits', '')
    v.contact_email = doc.get('contact_email', 'hr@antonhaus.ru')
    v.published_date = doc.get('published_date') or doc.get('created_at') or datetime.utcnow()

    return render(request, 'main/vacancy_detail.html', {'vacancy': v})

