from django.shortcuts import render
from .models import Game, Category  # Імпортуємо твої моделі


def home(request):
    categories = Category.objects.all()
    return render(request, 'main/home.html', {'categories': categories})


def about(request):
    categories = Category.objects.all()
    return render(request, 'main/about.html', {'categories': categories})


def contact(request):
    categories = Category.objects.all()
    return render(request, 'main/contact.html', {'categories': categories})


def catalog(request):
    # Отримуємо всі ігри з бази даних
    games = Game.objects.all()
    # Отримуємо всі категорії для випадаючого меню в хедері
    categories = Category.objects.all()
    context = {'games': games, 'categories': categories}
    return render(request, 'main/index.html', context)


def category_detail(request, category_id):
    # Фільтрація ігор за категорією
    games = Game.objects.filter(category_id=category_id)
    categories = Category.objects.all()
    context = {'games': games, 'categories': categories}
    return render(request, 'main/index.html', context)