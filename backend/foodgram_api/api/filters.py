from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')

    def filter_name(self, queryset, name, value):
        fitered_queryset = queryset.filter(
            **{'__'.join((name, 'istartswith')): value}
        )
        return fitered_queryset.union(queryset.filter(
            **{'__'.join((name, 'icontains')): value}
        ).difference(fitered_queryset).order_by(
            *queryset.model._meta.ordering
        ), all=True)

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter()
    is_in_shopping_cart = filters.BooleanFilter()
    author = filters.NumberFilter()

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author')
