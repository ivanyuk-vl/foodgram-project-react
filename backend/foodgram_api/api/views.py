from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.db.utils import IntegrityError
from djoser.serializers import SetPasswordSerializer, UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import (
    GenericViewSet, ModelViewSet, ReadOnlyModelViewSet
)

from .serializers import (
    IngredientSerializer, SubscribeSerializer, RecipeGetSerializer,
    RecipeShortSerializer, RecipeSerializer, TagSerializer, UserSerializer
)
from recipes.models import Ingredient, Recipe, Tag
from users.models import User

DOES_NOT_EXIST_SUBSCRIBE_ERROR = 'Пользователь {} не подписан на автора {}.'
SELF_SUBSCRIBE_ERROR = 'Нельзя подписаться на самого себя.'
UNIQUE_SUBSCRIBE_ERROR = 'Пользователь {} уже подписан на автора {}.'


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return SubscribeSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        return self.serializer_class

    def get_instance(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            DjoserUserSerializer(instance=serializer.save()).data,
            status=status.HTTP_201_CREATED
        )

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(['post'], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<author_id>\d+)/subscribe'
    )
    def subscribe(self, request, author_id, *args, **kwargs):
        author = get_object_or_404(User.objects.filter(id=author_id).annotate(
            recipes_count=Count('recipes')
        ))
        try:
            if self.request.method == 'DELETE':
                self.request.user.subscriptions.get(author=author).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            self.request.user.subscriptions.create(author=author)
        except ObjectDoesNotExist:
            return Response(
                {
                    'errors': DOES_NOT_EXIST_SUBSCRIBE_ERROR.format(
                        self.request.user.username, author.username
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError as exception:
            exception_message = str(exception)
            if exception_message.startswith('UNIQUE'):
                data = UNIQUE_SUBSCRIBE_ERROR.format(
                    self.request.user.username, author.username
                )
            elif exception_message.startswith('CHECK'):
                data = SELF_SUBSCRIBE_ERROR
            else:
                raise IntegrityError(exception)
            return Response(
                {'errors': data}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            self.get_serializer(author).data,
            status=status.HTTP_201_CREATED
        )

    def get_subscriptions(self):
        return (
            User.objects
            .filter(subscribers__user=self.request.user)
            .annotate(recipes_count=Count('recipes'))
        )

    def get_subscribe_serializer(self):
        return SubscribeSerializer

    @action(['get'], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        self.get_queryset = self.get_subscriptions
        self.get_serializer_class = self.get_subscribe_serializer
        return self.list(request, *args, **kwargs)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        elif self.action == 'favorite':
            return RecipeShortSerializer
        return self.serializer_class

    def get_recipe_get_serializer(self):
        return RecipeGetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.get_serializer_class = self.get_recipe_get_serializer
        return Response(
            self.get_serializer(instance=serializer.save()).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/favorite'
    )
    def favorite(self, request, recipe_id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if self.action == 'DELETE':
            self.request.user.favorite.get(recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        self.request.user.favorite.create(recipe=recipe)
        return Response(status=status.HTTP_201_CREATED)
