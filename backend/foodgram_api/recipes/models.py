from django.db import models

from .validators import (
    min_cooking_time_validator, validate_hex_color, validate_slug
)
from users.models import User

INGREDIENT_STR = 'id: {}, название: {}, ед.изм.: {}'
INGREDIENT_RECIPE_STR = 'id: {}, рецепт: {}, ингедиент: {}, кол-во: {}'
RECIPE_STR = 'id: {}, название: {}, автор: {}'
TAG_STR = 'id:{}, название: {}, цвет: {}, метка: {}'


class SlugField(models.SlugField):
    default_validators = [validate_slug]


class Ingredient(models.Model):
    name = models.CharField(
        'название',
        max_length=200,
        unique=True,
        error_messages={
            'unique': 'Рецепт с таким названием уже существует.',
        },
    )
    measurement_unit = models.CharField('единица измерения', max_length=200)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return INGREDIENT_STR.format(
            self.pk, self.name[:15], self.measurement_unit[:15]
        )


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='amounts_of_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='amounts_for_recipes'
    )
    amount = models.IntegerField('количество')

    class Meta:
        verbose_name = 'количество ингредиента'
        verbose_name_plural = 'количества ингредиентов'

    def __str__(self):
        return INGREDIENT_RECIPE_STR.format(
            self.id, self.recipe.name, self.ingredient.name, self.amount
        )


class Tag(models.Model):
    name = models.CharField(
        'название',
        max_length=200,
        unique=True,
        error_messages={
            'unique': 'Тег с таким названием уже существует.',
        }
    )
    color = models.CharField(
        'цвет',
        max_length=7,
        validators=[validate_hex_color],
        unique=True,
        null=True,
        error_messages={
            'unique': 'Тег с таким цветом уже существует.',
        }
    )
    slug = SlugField(
        'метка',
        max_length=200,
        unique=True,
        null=True,
        error_messages={
            'unique': 'Тег с такой меткой уже существует.',
        }
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return TAG_STR.format(self.pk, self.name[:15], self.color, self.slug)


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes'
    )
    name = models.CharField('название', max_length=200)
    image = models.ImageField('изображение', upload_to='recipes/')
    text = models.TextField('описание')
    ingredients = models.ManyToManyField(Ingredient, through=IngredientRecipe)
    tags = models.ManyToManyField(Tag)
    cooking_time = models.IntegerField(
        'время приготовления', validators=[min_cooking_time_validator]
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return RECIPE_STR.format(self.pk, self.name, self.author.username)
