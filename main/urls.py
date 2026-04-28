from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('catalog/', views.catalog, name='catalog'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),

    # Help pages (not shown in header)
    path('help/how-to-buy/', views.how_to_buy, name='how_to_buy'),
    path('help/key-activation/', views.key_activation, name='key_activation'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:game_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:game_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:game_id>/', views.update_cart, name='update_cart'),

    # Checkout / Buy now
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('buy-now/<int:game_id>/', views.buy_now, name='buy_now'),

    # Newsletter subscription
    path('subscribe/', views.subscribe, name='subscribe'),
]
