from django.core.exceptions import ObjectDoesNotExist
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
    IngredientSerializer, RecipeGetSerializer, RecipeSerializer,
    TagSerializer, UserSerializer
)
from recipes.models import Ingredient, Recipe, Tag
from users.models import User

DELETE_SUBSCRIBE_ERROR = 'Пользователь {} не подписан на автора {}.'
SELF_SUBSCRIBE_ERROR = 'Нельзя подписаться на самого себя.'
UNIQUE_SUBSCRIBE_ERROR = 'Пользователь {} уже подписан на автора {}.'


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
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
        author = get_object_or_404(User, id=author_id)
        try:
            if self.request.method == 'DELETE':
                self.request.user.subscriptions.get(author=author).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            self.request.user.subscriptions.create(author=author)
        except ObjectDoesNotExist:
            return Response(
                {'errors': DELETE_SUBSCRIBE_ERROR.format(
                    self.request.user.username, author.username
                )},
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
        return Response()

    def subscriptions(self, request, *args, **kwargs):
        return Response()


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
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            RecipeGetSerializer(instance=serializer.save()).data,
            status=status.HTTP_201_CREATED
        )
