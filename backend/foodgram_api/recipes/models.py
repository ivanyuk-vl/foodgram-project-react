from django.db import models

from .fields import ModelsSlugField
from .validators import (
    min_cooking_time_validator, min_ingredient_amount_validator,
    validate_hex_color
)
from users.models import User

ID_RECIPE_USER_STR = 'id: {}, рецепт: {}, пользователь: {}'
INGREDIENT_STR = 'id: {}, название: {}, ед.изм.: {}'
INGREDIENT_AMOUNT_STR = 'id: {}, рецепт: {}, ингедиент: {}, кол-во: {}'
RECIPE_STR = 'id: {}, название: {}, автор: {}'


class Ingredient(models.Model):
    name = models.CharField(
        'название',
        max_length=200,
    )
    measurement_unit = models.CharField('единица измерения', max_length=200)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_ingredient'
            )
        ]

    def __str__(self):
        return INGREDIENT_STR.format(
            self.pk, self.name[:15], self.measurement_unit[:15]
        )


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='amounts_of_ingredients',
        verbose_name='рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='amounts_for_recipes',
        verbose_name='ингредиент'
    )
    amount = models.IntegerField(
        'количество',
        validators=[min_ingredient_amount_validator]
    )

    class Meta:
        verbose_name = 'количество ингредиента'
        verbose_name_plural = 'количества ингредиентов'
        ordering = ('recipe__name',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_amount'
            )
        ]

    def __str__(self):
        return INGREDIENT_AMOUNT_STR.format(
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
    slug = ModelsSlugField(
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
        ordering = ('name',)

    def __str__(self):
        return self.slug


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='автор'
    )
    name = models.CharField('название', max_length=200)
    image = models.ImageField('изображение', upload_to='recipes/')
    text = models.TextField('описание')
    ingredients = models.ManyToManyField(
        Ingredient, through=IngredientAmount, related_name='recipes'
    )
    tags = models.ManyToManyField(Tag, verbose_name='теги')
    cooking_time = models.IntegerField(
        'время приготовления', validators=[min_cooking_time_validator]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата публикации',
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return RECIPE_STR.format(self.pk, self.name, self.author.username)


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='рецепт'
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        ordering = ('user__username',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]

    def __str__(self):
        return ID_RECIPE_USER_STR.format(
            self.pk, self.recipe.name, self.user.username
        )


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='пользователь'
    )

    class Meta:
        verbose_name = 'cписок покупок'
        verbose_name_plural = 'списки покупок'
        ordering = ('user__username',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return ID_RECIPE_USER_STR.format(
            self.pk, self.recipe.name, self.user.username
        )
