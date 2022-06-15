from django.db.models import F
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from .fields import ImageField
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


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    image = ImageField()

    class Meta:
        model = Recipe
        exclude = ('author',)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            recipe.amounts_of_ingredients.create(
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe.image.delete()
        recipe.amounts_of_ingredients.all().delete()
        for attr, value in validated_data.items():
            setattr(recipe, attr, value)
        recipe.save()
        for ingredient in ingredients:
            recipe.amounts_of_ingredients.create(
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
        recipe.tags.set(tags, clear=True)
        return recipe


class RecipeShortReadSerializer(serializers.ModelSerializer):
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
            is_subscribed=instance.is_subscribed_to_author
        )


class RecipePostReadSerializer(RecipeReadSerializer):
    author = UserReadSerializer()


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
