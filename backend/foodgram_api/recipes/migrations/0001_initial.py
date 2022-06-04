# Generated by Django 2.2.16 on 2022-06-04 10:50

from django.db import migrations, models
import django.db.models.deletion
import recipes.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(error_messages={'unique': 'Рецепт с таким названием уже существует.'}, max_length=254, unique=True, verbose_name='название')),
                ('measurement_unit', models.CharField(max_length=254, verbose_name='единица измерения')),
            ],
            options={
                'verbose_name': 'ингредиент',
                'verbose_name_plural': 'ингредиенты',
            },
        ),
        migrations.CreateModel(
            name='IngredientAmount',
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
            name='IngredientAmountRecipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
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
                ('name', models.CharField(error_messages={'unique': 'Тег с таким названием уже существует.'}, max_length=254, unique=True, verbose_name='название')),
                ('color', models.CharField(error_messages={'unique': 'Тег с таким цветом уже существует.'}, max_length=7, unique=True, validators=[recipes.validators.HexColorValidator()], verbose_name='цвет')),
                ('slug', models.SlugField(error_messages={'unique': 'Тег с такой меткой уже существует.'}, unique=True, verbose_name='метка')),
            ],
            options={
                'verbose_name': 'тег',
                'verbose_name_plural': 'теги',
            },
        ),
        migrations.CreateModel(
            name='TagRecipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.Recipe')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.Tag')),
            ],
        ),
    ]
