from django.shortcuts import render


def services(request):
    context = {}
    return render(request, 'main/services.html', context)


