from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

HEX_COLOR_ERROR = (
    'Введите правильный цвет. Это значение должно начинаться с символа #, '
    'за которым следует три пары шестнадцатеричных цифр. Пример: #8fce00.'
)
MIN_COOKING_TIME_ERROR = 'Время приготовления не может быть меньше 1 минуты.'
MIN_INGREDIENT_AMOUNT_ERROR = 'Количества ингредиента не может быть меньше 1.'
SLUG_ERROR = (
    'Значение должно состоять только из латинских букв, цифр, знаков '
    'подчеркивания или дефиса.'
)
validate_hex_color = RegexValidator(r'^#[a-fA-F0-9]{6}\Z', HEX_COLOR_ERROR)
validate_slug = RegexValidator(r'^[-a-zA-Z0-9_]+$', SLUG_ERROR)


def min_cooking_time_validator(time):
    if time < 1:
        raise ValidationError(MIN_COOKING_TIME_ERROR)


def min_ingredient_amount_validator(amount):
    if amount < 1:
        raise ValidationError(MIN_INGREDIENT_AMOUNT_ERROR)
