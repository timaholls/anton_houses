from django.shortcuts import redirect


class MongoAuthMiddleware:
    """
    Простая middleware для защиты внутренних страниц и админ-API.
    - Требует аутентификацию для страниц: /company-management/, /content-management/, /manual-matching/
    - Для API: если ?admin=true или метод не GET — требует аутентификацию
    """

    PROTECTED_PAGES = (
        '/company-management/',
        '/content-management/',
        '/manual-matching/',
    )

    PROTECTED_API_PREFIXES = (
        '/api/company-info', '/api/branch-offices', '/api/employees',
        '/api/tags', '/api/categories', '/api/authors', '/api/articles',
        '/api/catalog-landings', '/api/promotions', '/api/videos', '/api/vacancies',
        '/api/secondary',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip('/') + '/'

        def is_authenticated():
            return bool(request.session.get('user_id'))

        # Защита страниц
        if any(path.startswith(p) for p in self.PROTECTED_PAGES):
            if not is_authenticated() and not path.startswith('/login/'):
                next_url = request.get_full_path()
                return redirect(f"/login/?next={next_url}")

        # Защита админских API (POST/PUT/PATCH/DELETE или ?admin=true)
        if any(path.startswith(p) for p in self.PROTECTED_API_PREFIXES):
            admin_flag = request.GET.get('admin') == 'true'
            if (request.method != 'GET' or admin_flag) and not is_authenticated():
                return redirect(f"/login/?next={request.get_full_path()}")

        response = self.get_response(request)
        return response


