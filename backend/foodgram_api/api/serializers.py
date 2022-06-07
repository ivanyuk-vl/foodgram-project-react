from rest_framework import serializers

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', read_only=True
    )
    name = serializers.SlugRelatedField(
        source='ingredient', slug_field='name', read_only=True
    )
    measurement_unit = serializers.SlugRelatedField(
        source='ingredient', slug_field='measurement_unit', read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        exclude = ('image',)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
        recipe.tags.set(tags)
        return recipe


class RecipeGetSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        exclude = ('image',)

    def get_ingredients(self, instance):
        return IngredientRecipeGetSerializer(
            instance=instance.amounts_of_ingredients.all(), many=True
        ).data
