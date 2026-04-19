from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')

def about(request):
    context = {
        'title': 'Про нас',
        'content': 'Це сторінка з інформацією про наш проект.'
    }
    return render(request, 'main/inner.html', context)

def contact(request):
    context = {
        'title': 'Контакти',
        'content': 'Наші контакти: email@example.com'
    }
    return render(request, 'main/inner.html', context)
