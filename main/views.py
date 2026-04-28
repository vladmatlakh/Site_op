from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Avg, Count
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Game, Category, Rating, NewsletterSubscription, Order, OrderItem, PasswordResetCode  # Імпортуємо моделі


def _get_cart(request):
    cart = request.session.get('cart', {})
    return cart


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _cart_count(cart):
    return sum(cart.values()) if cart else 0


def _base_context(request):
    categories = Category.objects.all()
    cart = _get_cart(request)
    return {
        'categories': categories,
        'cart_count': _cart_count(cart),
    }


def home(request):
    context = _base_context(request)
    return render(request, 'main/home.html', context)


def about(request):
    context = _base_context(request)
    return render(request, 'main/about.html', context)


def contact(request):
    context = _base_context(request)
    return render(request, 'main/contact.html', context)


def how_to_buy(request):
    context = _base_context(request)
    return render(request, 'main/how_to_buy.html', context)


def key_activation(request):
    context = _base_context(request)
    return render(request, 'main/key_activation.html', context)


def catalog(request):
    games = Game.objects.all()
    context = _base_context(request)
    context.update({'games': games})
    return render(request, 'main/index.html', context)


def category_detail(request, category_id):
    current_category = get_object_or_404(Category, id=category_id)
    games = Game.objects.filter(category=current_category)
    context = _base_context(request)
    context.update({'games': games, 'current_category': current_category})
    return render(request, 'main/index.html', context)


def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    # Обробка оцінки (rating)
    if request.method == 'POST' and 'score' in request.POST:
        score = int(request.POST.get('score', 0))
        if score not in [1, 2, 3, 4, 5]:
            messages.error(request, 'Некоректна оцінка.')
            return redirect('game_detail', game_id=game.id)
        # Забезпечити наявність session_key
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        rating, created = Rating.objects.update_or_create(
            game=game,
            session_key=session_key,
            defaults={'score': score}
        )
        if created:
            messages.success(request, 'Дякуємо! Вашу оцінку збережено.')
        else:
            messages.success(request, 'Вашу оцінку оновлено.')
        return redirect('game_detail', game_id=game.id)

    stats = game.ratings.aggregate(avg=Avg('score'), cnt=Count('id'))
    avg_rating = stats['avg'] or 0
    rating_count = stats['cnt'] or 0

    user_score = None
    if request.session.session_key:
        r = game.ratings.filter(session_key=request.session.session_key).first()
        if r:
            user_score = r.score

    context = _base_context(request)
    context.update({'game': game, 'avg_rating': avg_rating, 'rating_count': rating_count, 'user_score': user_score})
    return render(request, 'main/game_detail.html', context)


def cart_view(request):
    cart = _get_cart(request)
    game_ids = [int(gid) for gid in cart.keys()]
    games = Game.objects.filter(id__in=game_ids)
    items = []
    total = 0
    for g in games:
        qty = int(cart.get(str(g.id), 0))
        line_total = g.price * qty
        total += line_total
        items.append({'game': g, 'qty': qty, 'line_total': line_total})
    context = _base_context(request)
    context.update({'items': items, 'total': total})
    return render(request, 'main/cart.html', context)


def add_to_cart(request, game_id):
    if request.method != 'POST':
        return redirect('game_detail', game_id=game_id)
    _ = get_object_or_404(Game, id=game_id)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1
    cart = _get_cart(request)
    cart[str(game_id)] = cart.get(str(game_id), 0) + quantity
    _save_cart(request, cart)
    messages.success(request, 'Товар додано до кошика.')
    next_url = request.POST.get('next') or 'cart'
    if next_url in ['catalog', 'cart']:
        return redirect(next_url)
    return redirect('game_detail', game_id=game_id)


def remove_from_cart(request, game_id):
    cart = _get_cart(request)
    if str(game_id) in cart:
        del cart[str(game_id)]
        _save_cart(request, cart)
        messages.info(request, 'Товар видалено з кошика.')
    return redirect('cart')


def update_cart(request, game_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = _get_cart(request)
        if quantity <= 0:
            cart.pop(str(game_id), None)
        else:
            cart[str(game_id)] = quantity
        _save_cart(request, cart)
        messages.success(request, 'Кошик оновлено.')
    return redirect('cart')


def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip() or None
        if not email:
            messages.error(request, 'Вкажіть email для підписки.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        obj, created = NewsletterSubscription.objects.get_or_create(email=email, defaults={'name': name})
        if not created:
            # Оновимо ім'я, якщо задане
            if name and obj.name != name:
                obj.name = name
                obj.save(update_fields=['name'])
            messages.info(request, 'Ви вже підписані на розсилку. Дані оновлено.')
        else:
            messages.success(request, 'Дякуємо! Ви підписалися на розсилку.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# -------- АВТЕНТИФІКАЦІЯ --------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        messages.success(request, 'Вітаємо! Ви увійшли в акаунт.')
        return redirect(request.GET.get('next') or 'home')
    context = _base_context(request)
    context.update({'form': form})
    return render(request, 'main/login.html', context)


def logout_view(request):
    if request.user.is_authenticated:
        auth_logout(request)
        messages.info(request, 'Ви вийшли з акаунта.')
    return redirect('home')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, 'Реєстрація успішна!')
        return redirect('home')
    context = _base_context(request)
    context.update({'form': form})
    return render(request, 'main/register.html', context)


@login_required
def profile(request):
    if request.user.is_staff:
        orders = Order.objects.select_related('user').prefetch_related('items__game').order_by('-created_at')
    else:
        orders = Order.objects.filter(user=request.user).prefetch_related('items__game').order_by('-created_at')
    context = _base_context(request)
    context.update({'orders': orders})
    return render(request, 'main/profile.html', context)


def password_reset_request(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Користувача з таким email не знайдено.')
            return redirect('password_reset_request')
        code_obj = PasswordResetCode.create_for_user(user)
        subject = 'Відновлення паролю — GameStore'
        message = f"Ваш тимчасовий код відновлення: {code_obj.code}\nДіє до: {code_obj.expires_at.strftime('%Y-%m-%d %H:%M')} UTC"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        messages.success(request, 'Код відновлення надіслано на вашу пошту.')
        return redirect('password_reset_confirm')
    context = _base_context(request)
    return render(request, 'main/password_reset_request.html', context)


def password_reset_confirm(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        code = (request.POST.get('code') or '').strip().upper()
        new_password = request.POST.get('new_password') or ''
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Користувача з таким email не знайдено.')
            return redirect('password_reset_confirm')
        code_obj = PasswordResetCode.objects.filter(user=user, code=code, is_used=False).order_by('-created_at').first()
        if not code_obj or not code_obj.is_valid():
            messages.error(request, 'Невірний або прострочений код.')
            return redirect('password_reset_confirm')
        if len(new_password) < 8:
            messages.error(request, 'Пароль має містити щонайменше 8 символів.')
            return redirect('password_reset_confirm')
        user.set_password(new_password)
        user.save()
        code_obj.is_used = True
        code_obj.save(update_fields=['is_used'])
        messages.success(request, 'Пароль успішно змінено. Увійдіть з новим паролем.')
        return redirect('login')
    context = _base_context(request)
    return render(request, 'main/password_reset_confirm.html', context)


def buy_now(request, game_id):
    """Почати швидку покупку одного товару і перейти на оформлення замовлення."""
    game = get_object_or_404(Game, id=game_id)
    qty = 1
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            qty = 1
    if qty < 1:
        qty = 1
    # Зберігаємо позиції для оформлення у сесії окремо від кошика
    request.session['checkout_items'] = {str(game.id): qty}
    request.session.modified = True
    return redirect('checkout')


def _collect_checkout_items(request):
    """Отримати позиції, які будемо оформляти: або з checkout_items, або з усього кошика."""
    src = request.session.get('checkout_items') or _get_cart(request)
    game_ids = [int(gid) for gid in src.keys()]
    games = Game.objects.filter(id__in=game_ids)
    items = []
    total = 0
    for g in games:
        qty = int(src.get(str(g.id), 0))
        if qty <= 0:
            continue
        line_total = g.price * qty
        total += line_total
        items.append({'game': g, 'qty': qty, 'line_total': line_total})
    return items, total


def checkout(request):
    """Сторінка оформлення замовлення: збір даних оплати та підтвердження."""
    # Якщо явно не задано checkout_items, використовуємо весь кошик
    if not request.session.get('checkout_items'):
        # якщо кошик порожній, повернемо до каталогу
        if not _get_cart(request):
            messages.info(request, 'Ваш кошик порожній. Додайте товари перед оформленням.')
            return redirect('catalog')
    errors = {}
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        payment_method = (request.POST.get('payment_method') or '').strip()
        card_number = (request.POST.get('card_number') or '').replace(' ', '')
        card_exp = (request.POST.get('card_exp') or '').strip()
        card_cvv = (request.POST.get('card_cvv') or '').strip()

        # Валідація мінімальна
        if not name:
            errors['name'] = 'Вкажіть ПІБ.'
        if not email:
            errors['email'] = 'Вкажіть email для отримання ключів.'
        if not phone:
            errors['phone'] = 'Вкажіть номер телефону.'
        if payment_method not in ['card', 'paypal']:
            errors['payment_method'] = 'Оберіть спосіб оплати.'
        if payment_method == 'card':
            if len(card_number) < 12:
                errors['card_number'] = 'Некоректний номер картки.'
            if not card_exp:
                errors['card_exp'] = 'Вкажіть термін дії.'
            if len(card_cvv) < 3:
                errors['card_cvv'] = 'Некоректний CVV.'

        if not errors:
            # Імітація успішної оплати
            items, total = _collect_checkout_items(request)

            # Створюємо замовлення
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                phone=phone,
                total=total,
            )
            for it in items:
                OrderItem.objects.create(
                    order=order,
                    game=it['game'],
                    quantity=it['qty'],
                    price=it['game'].price,
                )

            # очистимо куплені позиції з кошика
            cart = _get_cart(request)
            for it in items:
                gid = str(it['game'].id)
                if gid in cart:
                    del cart[gid]
            _save_cart(request, cart)
            # очистимо тимчасові checkout_items
            if 'checkout_items' in request.session:
                del request.session['checkout_items']
                request.session.modified = True
            # Перенаправимо на сторінку успіху
            request.session['last_order_id'] = order.id
            request.session['last_order'] = {
                'name': name, 'email': email, 'phone': phone,
                'total': float(total), 'count': sum([it['qty'] for it in items])
            }
            return redirect('checkout_success')
        else:
            # Показати помилки
            for field, msg in errors.items():
                messages.error(request, f"{field}: {msg}")

    items, total = _collect_checkout_items(request)
    if not items:
        messages.info(request, 'Немає товарів для оформлення.')
        return redirect('catalog')

    context = _base_context(request)
    context.update({'items': items, 'total': total})
    return render(request, 'main/checkout.html', context)


def checkout_success(request):
    """Сторінка підтвердження замовлення після успішної оплати (імітація)."""
    last_order = request.session.pop('last_order', None)
    order_obj = None
    order_id = request.session.pop('last_order_id', None)
    if order_id:
        try:
            order_obj = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            order_obj = None
    context = _base_context(request)
    context.update({'order': last_order, 'order_obj': order_obj})
    return render(request, 'main/checkout_success.html', context)