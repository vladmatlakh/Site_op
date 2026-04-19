from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('catalog/', views.catalog, name='catalog'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),
]
