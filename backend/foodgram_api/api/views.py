from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Exists, OuterRef, Sum
from django.db.utils import IntegrityError
from django.http import HttpResponse
from djoser.serializers import SetPasswordSerializer, UserCreateSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import (
    GenericViewSet, ModelViewSet, ReadOnlyModelViewSet
)

from .filters import NameSearchFilter, RecipeFilter
from .permissions import IsAdminOrIsAuthorOrReadOnly
from .serializers import (
    IngredientReadSerializer, SubscribePostReadSerializer,
    SubscribeReadSerializer, RecipeReadSerializer,
    RecipePostReadSerializer, RecipeShortReadSerializer, RecipeSerializer,
    TagReadSerializer, UserSerializer
)
from recipes.models import Ingredient, Favorite, Recipe, ShoppingCart, Tag
from users.models import SELF_SUBSCRIBE_ERROR, Subscribe, User


DOES_NOT_EXIST_CART_ERROR = 'У пользователя {} нет рецета {} в списке покупок.'
DOES_NOT_EXIST_FAVORITE_ERROR = 'У пользователя {} нет рецета {} в избранном.'
DOES_NOT_EXIST_SUBSCRIBE_ERROR = 'Пользователь {} не подписан на автора {}.'
UNIQUE_CART_ERROR = 'У пользователя {} уже есть рецепт {} в списке покупок.'
UNIQUE_FAVORITE_ERROR = 'У пользователя {} уже есть рецепт {} в избранном.'
UNIQUE_SUBSCRIBE_ERROR = 'Пользователь {} уже подписан на автора {}.'


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_users_queryset(self):
        return User.objects.annotate(is_subscribed=Exists(
            Subscribe.objects.filter(
                author=OuterRef('pk'),
                user__username=self.request.user.username
            )
        ))

    def get_queryset(self):
        return self.get_users_queryset().all()

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return SubscribePostReadSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        return self.serializer_class

    def get_instance(self):
        return self.request.user

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
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
        url_path=r'(?P<author_id>\d+)/subscribe',
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
            return Response({'errors': DOES_NOT_EXIST_SUBSCRIBE_ERROR.format(
                self.request.user.username, author.username
            )}, status=status.HTTP_400_BAD_REQUEST)
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

    def get_subscriptions_queryset(self):
        return (
            self.get_users_queryset()
            .annotate(recipes_count=Count('recipes'))
            .filter(subscribers__user=self.request.user)
        )

    def get_subscribe_read_serializer_class(self):
        return SubscribeReadSerializer

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, *args, **kwargs):
        self.get_queryset = self.get_subscriptions_queryset
        self.get_serializer_class = self.get_subscribe_read_serializer_class
        return self.list(request, *args, **kwargs)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (NameSearchFilter,)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagReadSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (IsAdminOrIsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.annotate(is_subscribed=Exists(
            Subscribe.objects.filter(
                author=OuterRef('author'),
                user__username=self.request.user.username
            )
        )).annotate(is_favorited=Exists(
            Favorite.objects.filter(
                recipe=OuterRef('id'),
                user__username=self.request.user.username
            )
        )).annotate(is_in_shopping_cart=Exists(
            ShoppingCart.objects.filter(
                recipe=OuterRef('id'),
                user__username=self.request.user.username
            )
        ))
        tags = self.request.query_params.getlist('tags')
        if tags and ''.join(tags):
            return queryset.filter(tags__slug__in=tags)
        return queryset.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        elif self.action in ('favorite', 'shopping_cart'):
            return RecipeShortReadSerializer
        return self.serializer_class

    def get_read_serializer_class(self):
        if self.action == 'update':
            return RecipeReadSerializer
        return RecipePostReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.get_serializer_class = self.get_read_serializer_class
        return Response(self.get_serializer(
            serializer.save(author=self.request.user)
        ).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.get_serializer_class = self.get_read_serializer_class
        return Response(self.get_serializer(serializer.save()).data)

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/favorite'
    )
    def favorite(self, request, recipe_id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        try:
            if self.action == 'DELETE':
                self.request.user.favorite.get(recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            self.request.user.favorite.create(recipe=recipe)
        except ObjectDoesNotExist:
            return Response({'errors': DOES_NOT_EXIST_FAVORITE_ERROR.format(
                self.request.user.username, recipe.name
            )}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exception:
            if not str(exception).startswith('UNIQUE'):
                raise IntegrityError(exception)
            return Response(UNIQUE_FAVORITE_ERROR.format(
                self.request.user.username, recipe.name
            ), status=status.HTTP_400_BAD_REQUEST)
        return Response(
            self.get_serializer(recipe), status=status.HTTP_201_CREATED
        )

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>)\d+/shopping_cart'
    )
    def shopping_cart(self, request, recipe_id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        try:
            if self.action == 'DELETE':
                self.request.user.shopping_cart.get(recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            self.request.user.shopping_cart.create(recipe=recipe)
        except ObjectDoesNotExist:
            return Response({'errors': DOES_NOT_EXIST_CART_ERROR.format(
                self.request.user.username, recipe.name
            )}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exception:
            if not str(exception).startswith('UNIQUE'):
                raise IntegrityError(exception)
            return Response(UNIQUE_CART_ERROR.format(
                self.request.user.username, recipe.name
            ), status=status.HTTP_400_BAD_REQUEST)
        return Response(
            self.get_serializer(recipe), status=status.HTTP_201_CREATED
        )

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        return HttpResponse('\n'.join([(
            f'* {ingredient.name} ({ingredient.measurement_unit}) '
            f'- {ingredient.amount}'
        ) for ingredient in Ingredient.objects.filter(
            recipes__shopping_cart__user=self.request.user
        ).annotate(amount=Sum('amounts_for_recipes__amount'))]))
