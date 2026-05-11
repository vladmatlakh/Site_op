from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва категорії")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Game(models.Model):
    title = models.CharField(max_length=200, verbose_name="Назва гри")
    description = models.TextField(verbose_name="Опис")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="games")
    image = models.ImageField(upload_to='games/', blank=True, null=True, verbose_name="Зображення")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Review(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="reviews")
    author = models.CharField(max_length=100)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Відгук від {self.author} на {self.game.title}"

class Rating(models.Model):
    SCORE_CHOICES = [(i, str(i)) for i in range(1, 6)]
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="ratings")
    score = models.IntegerField(choices=SCORE_CHOICES)
    # Використовуємо session_key для ідентифікації оцінки користувача (анонімно)
    session_key = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('game', 'session_key'),)

    def __str__(self):
        return f"Оцінка {self.score} для {self.game.title}"

class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ім'я")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Замовлення #{self.id} від {self.name} ({self.total} грн)"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    game = models.ForeignKey(Game, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.game.title} x{self.quantity}"

class GameKeyManager(models.Manager):
    def get_available_keys(self, game, quantity):
        """Отримати доступні ключі для гри"""
        return self.filter(game=game, is_sold=False)[:quantity]

    def assign_keys_to_order(self, order_item):
        """Призначити ключі до замовлення"""
        keys = self.get_available_keys(order_item.game, order_item.quantity)
        assigned_keys = []
        for key in keys:
            key.mark_as_sold(order_item)
            assigned_keys.append(key)
        return assigned_keys

class GameKey(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='keys', verbose_name='Гра')
    code = models.CharField(max_length=200, unique=True, verbose_name='Код ключа')
    is_sold = models.BooleanField(default=False, db_index=True, verbose_name='Продано')
    order_item = models.ForeignKey('OrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='keys', verbose_name='Позиція замовлення')
    sold_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата продажу')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = GameKeyManager()

    class Meta:
        indexes = [
            models.Index(fields=['game', 'is_sold']),
        ]
        verbose_name = 'Ключ гри'
        verbose_name_plural = 'Ключі гри'

    def mark_as_sold(self, order_item):
        """Позначити ключ як проданий"""
        self.is_sold = True
        self.sold_at = timezone.now()
        self.order_item = order_item
        self.save()

    def is_available(self):
        """Перевірити, чи доступний ключ для продажу"""
        return not self.is_sold and self.order_item is None

    def __str__(self):
        return f"{self.game.title} — {self.code}{' (продано)' if self.is_sold else ''}"

class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_codes')
    code = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def create_for_user(cls, user, minutes=15):
        code = uuid.uuid4().hex[:6].upper()
        return cls.objects.create(user=user, code=code, expires_at=timezone.now() + timedelta(minutes=minutes))

    def is_valid(self):
        return (not self.is_used) and timezone.now() <= self.expires_at

    def __str__(self):
        return f"Код відновлення для {self.user.username}: {self.code}"

