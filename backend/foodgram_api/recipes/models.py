from django.db import models

INGREDIENT_STR = 'id: {}, название: {}, ед.изм.: {}'
TAG_STR = 'id:{}, название: {}, цвет: {}, метка: {}'


class Ingredient(models.Model):
    name = models.CharField('название', max_length=254, blank=False)
    measurement_unit = models.CharField(
        'единица измерения', max_length=254, blank=False
    )

    def __str__(self):
        return INGREDIENT_STR.format(
            self.pk, self.name[:15], self.measurement_unit[:15]
        )


class Tag(models.Model):
    name = models.CharField(
        'название', max_length=254, blank=False, unique=True
    )
    color = models.CharField('цвет', max_length=7, blank=False, unique=True)
    slug = models.SlugField('метка', blank=False, unique=True)

    def __str__(self):
        return TAG_STR.format(self.pk, self.name[:15], self.color, self.slug)
