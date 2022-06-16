from django import forms
from django.contrib import admin

from .models import (
    Favorite, Ingredient, IngredientAmount, Recipe, ShoppingCart, Tag
)

INGREDIENTS_COUNT_ERROR = 'Нужно указать хотя бы один ингредиент.'


class IngredientAmountInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        count = 0
        for form in self.forms:
            if form.cleaned_data:
                count += 1
        if count < 1:
            raise forms.ValidationError(INGREDIENTS_COUNT_ERROR)


class IngredientAmountInline(admin.TabularInline):
    model = IngredientAmount
    formset = IngredientAmountInlineFormset


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('author', 'name')
    empty_value_display = '-пусто-'
    inlines = (IngredientAmountInline,)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
