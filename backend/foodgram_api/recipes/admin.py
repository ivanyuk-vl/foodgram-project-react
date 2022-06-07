from django.contrib import admin

from .models import Ingredient, IngredientRecipe, Recipe, Tag


admin.site.register(Ingredient)
admin.site.register(IngredientRecipe)
admin.site.register(Recipe)
admin.site.register(Tag)
