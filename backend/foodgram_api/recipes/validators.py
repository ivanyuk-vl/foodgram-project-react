from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

HEX_COLOR_ERROR = (
    'Введите правильный цвет. Это значение должно начинаться с символа #, '
    'за которым следует три пары шестнадцатеричных цифр.'
)
MIN_COOKING_TIME_ERROR = 'Время приготовления не может быть меньше 1 минуты.'


class HexColorValidator(RegexValidator):
    regex = r'^#[\da-fA-F]{6}\Z'
    message = HEX_COLOR_ERROR


def min_cooking_time_validator(time):
    if time < 1:
        raise ValidationError(MIN_COOKING_TIME_ERROR)
