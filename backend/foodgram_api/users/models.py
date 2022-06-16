from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.forms import ValidationError

SUBSCRIBE_STR = 'id: {}, автор: {}, подписчик: {}'
SELF_SUBSCRIBE_ERROR = 'Нельзя подписаться на самого себя.'


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
    email = models.EmailField(
        'адрес электронной почты',
        unique=True,
        error_messages={
            'unique': (
                'Пользователь с таким адресом электронной '
                'почты уже существует.'
            ),
        }
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta(AbstractUser.Meta):
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='автор'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='подписчик'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='can\'t_follow_yourself'
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'

    def clean(self) -> None:
        if self.author == self.user:
            raise ValidationError(SELF_SUBSCRIBE_ERROR)

    def __str__(self):
        return SUBSCRIBE_STR.format(
            self.id, self.author.username, self.user.username
        )
