# Generated by Django 2.2.16 on 2022-06-11 13:25

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import recipes.models
import recipes.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'избранное',
                'verbose_name_plural': 'избранное',
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(error_messages={'unique': 'Рецепт с таким названием уже существует.'}, max_length=200, unique=True, verbose_name='название')),
                ('measurement_unit', models.CharField(max_length=200, verbose_name='единица измерения')),
            ],
            options={
                'verbose_name': 'ингредиент',
                'verbose_name_plural': 'ингредиенты',
            },
        ),
        migrations.CreateModel(
            name='IngredientRecipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(verbose_name='количество')),
            ],
            options={
                'verbose_name': 'количество ингредиента',
                'verbose_name_plural': 'количества ингредиентов',
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='название')),
                ('image', models.ImageField(upload_to='recipes/', verbose_name='изображение')),
                ('text', models.TextField(verbose_name='описание')),
                ('cooking_time', models.IntegerField(validators=[recipes.validators.min_cooking_time_validator], verbose_name='время приготовления')),
            ],
            options={
                'verbose_name': 'рецепт',
                'verbose_name_plural': 'рецепты',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(error_messages={'unique': 'Тег с таким названием уже существует.'}, max_length=200, unique=True, verbose_name='название')),
                ('color', models.CharField(error_messages={'unique': 'Тег с таким цветом уже существует.'}, max_length=7, null=True, unique=True, validators=[django.core.validators.RegexValidator('^#[a-fA-F0-9]{6}\\Z', 'Введите правильный цвет. Это значение должно начинаться с символа #, за которым следует три пары шестнадцатеричных цифр. Пример: #8fce00.')], verbose_name='цвет')),
                ('slug', recipes.models.SlugField(error_messages={'unique': 'Тег с такой меткой уже существует.'}, max_length=200, null=True, unique=True, verbose_name='метка')),
            ],
            options={
                'verbose_name': 'тег',
                'verbose_name_plural': 'теги',
            },
        ),
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to='recipes.Recipe', verbose_name='рецепт')),
            ],
            options={
                'verbose_name': 'cписок покупок',
                'verbose_name_plural': 'списки покупок',
            },
        ),
    ]
