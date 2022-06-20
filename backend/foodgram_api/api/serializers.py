from django.db.models import F
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from .fields import ImageField
from recipes.admin import SAME_INGREDIENTS_ERROR
from recipes.models import Ingredient, IngredientAmount, Recipe, Tag


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed',)


class UserReadSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, instance):
        return instance.subscribers.filter(
            user=self.context['request'].user
        ).exists()


class IngredientReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class TagReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = fields


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class IngredientAmountReadSerializer(IngredientReadSerializer):
    amount = serializers.IntegerField()

    class Meta(IngredientReadSerializer.Meta):
        fields = IngredientReadSerializer.Meta.fields + ('amount',)


class RecipeShortReadSerializer(serializers.ModelSerializer):
    image = ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class RecipeReadSerializer(RecipeShortReadSerializer):
    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta(RecipeShortReadSerializer.Meta):
        fields = RecipeShortReadSerializer.Meta.fields + (
            'tags', 'author', 'ingredients', 'text',
            'is_favorited', 'is_in_shopping_cart'
        )
        depth = 1

    def get_ingredients(self, instance):
        return IngredientAmountReadSerializer(instance.ingredients.annotate(
            amount=F('amounts_for_recipes__amount')
        ), many=True).data

    def get_author(self, instance):
        return dict(
            **UserSerializer(instance=instance.author).data,
            is_subscribed=instance.is_subscribed
        )


class RecipePostReadSerializer(RecipeReadSerializer):
    author = UserReadSerializer()


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    image = ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, ingredients):
        same_ingredients = [
            ingredient['ingredient'] for ingredient in ingredients
        ]
        for ingredient in set(same_ingredients):
            same_ingredients.remove(ingredient)
        if same_ingredients:
            raise serializers.ValidationError(
                SAME_INGREDIENTS_ERROR.format([
                    f'id: {ingredient.id} ({ingredient.name})'
                    for ingredient in set(same_ingredients)
                ])
            )
        return ingredients

    def set_m2m_fields(self, recipe, ingredients, tags, clear=False):
        if clear:
            recipe.amounts_of_ingredients.all().delete()
        for ingredient in ingredients:
            recipe.amounts_of_ingredients.create(
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
        recipe.tags.set(tags, clear=clear)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.set_m2m_fields(recipe, ingredients, tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().update(recipe, validated_data)
        self.set_m2m_fields(recipe, ingredients, tags, clear=True)
        return recipe

    def to_representation(self, instance):
        if self.context['request'].method == 'POST':
            return RecipePostReadSerializer(
                instance, context=self.context
            ).data
        return RecipeReadSerializer(instance).data


class SubscribeReadSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, instance):
        limit = self.context['request'].query_params.get('recipes_limit')
        return RecipeShortReadSerializer(
            instance.recipes.all()[:int(limit) if (
                limit and limit.isdigit() and int(limit) >= 0
            ) else None],
            many=True
        ).data


class SubscribePostReadSerializer(SubscribeReadSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, instance):
        return instance.subscribers.filter(
            user=self.context['request'].user
        ).exists()
