from django.db import models

from .validators import min_cooking_time_validator, HexColorValidator
from users.models import User

INGREDIENT_STR = 'id: {}, название: {}, ед.изм.: {}'
INGREDIENT_AMOUNT_STR = 'id ингедиента: {}, кол-во: {}'
INGREDIENT_AMOUNT_RECIPE_STR = 'id рецепта: {}, id кол-ва ингредиента: {}'
TAG_STR = 'id:{}, название: {}, цвет: {}, метка: {}'
TAG_RECIPE_STR = 'id рецепта: {}, id тега: {}'


class Ingredient(models.Model):
    name = models.CharField('название', max_length=254, unique=True)
    measurement_unit = models.CharField('единица измерения', max_length=254)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return INGREDIENT_STR.format(
            self.pk, self.name[:15], self.measurement_unit[:15]
        )


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField('количество')

    class Meta:
        verbose_name = 'количество ингредиента'
        verbose_name_plural = 'количества ингредиентов'

    def __str__(self):
        return INGREDIENT_AMOUNT_STR.format(self.ingredient.pk, self.amount)


class IngredientAmountRecipe(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient_amount = models.ForeignKey(
        IngredientAmount, on_delete=models.CASCADE
    )

    def __str__(self):
        return INGREDIENT_AMOUNT_RECIPE_STR.format(
            self.recipe.pk, self.ingredient_amount.pk
        )


class Tag(models.Model):
    name = models.CharField('название', max_length=254, unique=True)
    color = models.CharField(
        'цвет', max_length=7, validators=[HexColorValidator()], unique=True
    )
    slug = models.SlugField('метка', unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return TAG_STR.format(self.pk, self.name[:15], self.color, self.slug)


class TagRecipe(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return TAG_RECIPE_STR.format(self.recipe.pk, self.tag.pk)


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes'
    )
    name = models.CharField('название', max_length=200)
    image = models.ImageField('изображение', upload_to='recipes/')
    text = models.TextField('описание')
    ingredients = models.ManyToManyField(
        IngredientAmount, through=IngredientAmountRecipe
    )
    tags = models.ManyToManyField(Tag, through=TagRecipe)
    cooking_time = models.IntegerField(
        'время приготовления', validators=[min_cooking_time_validator]
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'
