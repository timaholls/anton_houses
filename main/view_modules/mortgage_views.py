"""Views для ипотеки"""
from django.shortcuts import render
from ..services.mongo_service import get_mongo_connection


def mortgage(request):
    """Страница ипотеки с калькулятором"""
    # Получаем ипотечные программы из MongoDB
    try:
        db = get_mongo_connection()
        # Получаем все активные программы (общие и индивидуальные)
        docs = list(db['mortgage_programs'].find({'is_active': True}).sort('rate', 1))
        class P:
            def __init__(self, name, rate, is_individual=False, complexes=None):
                self.name, self.rate, self.is_individual, self.complexes = name, rate, is_individual, complexes or []
        mortgage_programs = [P(d.get('name',''), float(d.get('rate', 0)), d.get('is_individual', False), d.get('complexes', [])) for d in docs]
    except Exception:
        mortgage_programs = []
    if not mortgage_programs:
        class P:
            def __init__(self, name, rate, is_individual=False, complexes=None):
                self.name, self.rate, self.is_individual, self.complexes = name, rate, is_individual, complexes or []
        mortgage_programs = [P('Базовая', 11.4, False, [])]

    context = {
        'mortgage_programs': mortgage_programs,
    }
    return render(request, 'main/mortgage.html', context)

