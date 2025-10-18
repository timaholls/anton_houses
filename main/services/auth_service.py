"""Сервис аутентификации"""
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .mongo_service import get_mongo_user


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Простой логин через коллекцию users (email + пароль PBKDF2/argon2)."""
    error = ''
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        password = (request.POST.get('password') or '')
        next_url = request.GET.get('next') or request.POST.get('next') or '/'
        user = get_mongo_user(email)
        if not user:
            error = 'Неверный email или пароль'
        else:
            # Хеш хранится в поле password_hash (Django PBKDF2 формат или raw sha256 fallback)
            from django.contrib.auth.hashers import check_password
            ok = False
            try:
                ok = check_password(password, user.get('password_hash', ''))
            except Exception:
                import hashlib
                ok = hashlib.sha256(password.encode('utf-8')).hexdigest() == user.get('password_hash', '')
            if ok and user.get('is_active', True):
                request.session['user_id'] = str(user.get('_id'))
                request.session['user_email'] = user.get('email')
                request.session['user_name'] = user.get('name', '')
                return redirect(next_url)
            error = 'Неверный email или пароль'
    else:
        next_url = request.GET.get('next') or '/'
    return render(request, 'main/login.html', {'error': error, 'next': next_url})


def logout_view(request):
    """Выход из системы"""
    request.session.flush()
    return redirect('/login/')

