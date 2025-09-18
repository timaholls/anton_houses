from .models import BranchOffice


def head_office(request):
    """Контекст-процессор для добавления головного офиса во все шаблоны"""
    head_office = BranchOffice.objects.filter(is_active=True, is_head_office=True).first()
    return {
        'head_office': head_office
    }
