from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Avg, Count
from .models import Game, Category, Rating, NewsletterSubscription  # Імпортуємо моделі


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
    context = _base_context(request)
    context.update({'order': last_order})
    return render(request, 'main/checkout_success.html', context)