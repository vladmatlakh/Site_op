from django.shortcuts import render, get_object_or_404
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
    current_category = get_object_or_404(Category, id=category_id)
    games = Game.objects.filter(category=current_category)
    categories = Category.objects.all()
    context = {'games': games, 'categories': categories, 'current_category': current_category}
    return render(request, 'main/index.html', context)


def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    categories = Category.objects.all()
    context = {'game': game, 'categories': categories}
    return render(request, 'main/game_detail.html', context)