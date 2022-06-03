from django.db import models

from users.models import User

INGREDIENT_STR = 'id: {}, название: {}, ед.изм.: {}'
TAG_STR = 'id:{}, название: {}, цвет: {}, метка: {}'


class Ingredient(models.Model):
    name = models.CharField('название', max_length=254, unique=True)
    measurement_unit = models.CharField('единица измерения', max_length=254)

    def __str__(self):
        return INGREDIENT_STR.format(
            self.pk, self.name[:15], self.measurement_unit[:15]
        )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField('количество')

    class Meta:
        verbose_name = 'количество ингредиента'
        verbose_name_plural = 'количества ингредиентов'


class IngredientAmountRecipe(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient_amount = models.ForeignKey(
        IngredientAmount, on_delete=models.CASCADE
    )


class Tag(models.Model):
    name = models.CharField('название', max_length=254, unique=True)
    color = models.CharField('цвет', max_length=7, unique=True)
    slug = models.SlugField('метка', unique=True)

    def __str__(self):
        return TAG_STR.format(self.pk, self.name[:15], self.color, self.slug)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class TagRecipe(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes'
    )
    name = models.CharField('название', max_length=200)
    image = models.ImageField('изображение', upload_to='recipes/')
    text = models.TextField('описание')
    ingredients = models.ManyToManyField(
        IngredientAmount, through='IngredientAmountRecipe'
    )
    tags = models.ManyToManyField(Tag, through='TagRecipe')
    cooking_time = models.IntegerField('время приготовления')
