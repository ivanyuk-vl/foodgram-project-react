from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class User(AbstractUser):
    password = models.CharField('пароль', max_length=150)
    username = models.CharField(
        'имя пользователя',
        max_length=150,
        unique=True,
        help_text=(
            'Обязательное поле. Не более 150 символов. Только буквы, '
            'цифры и символы @/./+/-/_.'
        ),
        validators=[UnicodeUsernameValidator(r'^[\w.@+-]+\Z')],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )
    first_name = models.CharField('имя', max_length=150)
    last_name = models.CharField('фамилия', max_length=150)
    email = models.EmailField('адрес электронной почты', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class Subscribe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
