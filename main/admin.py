from django.contrib import admin
from .models import Category, Game, Review, Rating, NewsletterSubscription, GameKey

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'created_at', 'updated_at')
    list_filter = ('category',)
    search_fields = ('title',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('game', 'author', 'created_at', 'updated_at')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('game', 'score', 'session_key', 'created_at')
    list_filter = ('score',)
    search_fields = ('game__title', 'session_key')

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'created_at')
    search_fields = ('email', 'name')

@admin.register(GameKey)
class GameKeyAdmin(admin.ModelAdmin):
    list_display = ('game', 'code', 'is_sold', 'order_item', 'sold_at', 'created_at')
    list_filter = ('is_sold', 'game')
    search_fields = ('code', 'game__title')