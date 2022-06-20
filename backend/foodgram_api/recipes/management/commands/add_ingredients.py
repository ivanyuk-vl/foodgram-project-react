import json
import os

from django.core.management.base import BaseCommand

from foodgram_api.settings import STATIC_ROOT
from recipes.models import Ingredient

ADDED_INGREDIENTS_COUNT_MESSAGE = 'Количество добавленных ингредиентов: {}.'


class Command(BaseCommand):
    def handle(self, *args, **options):
        rows = []
        with open(os.path.join(
            os.path.join(STATIC_ROOT, 'data'), 'ingredients.json'
        ), encoding='UTF-8') as file:
            for ingredient in json.load(file):
                for key, value in ingredient.items():
                    ingredient[key] = value.lower()
                rows.append(Ingredient(**ingredient))
        print(ADDED_INGREDIENTS_COUNT_MESSAGE.format(
            len(Ingredient.objects.bulk_create(rows))
        ))
