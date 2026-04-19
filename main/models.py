from django.db import models

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