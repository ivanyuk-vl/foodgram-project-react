from django.db.models import Count, Exists, OuterRef, Sum
from django.http import FileResponse
from djoser.serializers import SetPasswordSerializer, UserCreateSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import (
    GenericViewSet, ModelViewSet, ReadOnlyModelViewSet
)

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientReadSerializer, SubscribePostReadSerializer,
    SubscribeReadSerializer, RecipeReadSerializer,
    RecipePostReadSerializer, RecipeShortReadSerializer, RecipeSerializer,
    TagReadSerializer, UserSerializer
)
from .utils import ingredients_to_pdf
from recipes.models import Ingredient, Favorite, Recipe, ShoppingCart, Tag
from users.models import SELF_SUBSCRIBE_ERROR, Subscribe, User


DOES_NOT_EXIST_CART_ERROR = 'У пользователя {} нет рецета {} в списке покупок.'
DOES_NOT_EXIST_FAVORITE_ERROR = 'У пользователя {} нет рецета {} в избранном.'
DOES_NOT_EXIST_SUBSCRIBE_ERROR = 'Пользователь {} не подписан на автора {}.'
UNIQUE_CART_ERROR = 'У пользователя {} уже есть рецепт {} в списке покупок.'
UNIQUE_FAVORITE_ERROR = 'У пользователя {} уже есть рецепт {} в избранном.'
UNIQUE_SUBSCRIBE_ERROR = 'Пользователь {} уже подписан на автора {}.'


def get_bad_request_response(message):
    return Response({'errors': message}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        queryset = User.objects.annotate(is_subscribed=Exists(
            Subscribe.objects.filter(
                author=OuterRef('pk'),
                user__username=self.request.user.username
            )
        )).all()
        if self.action in ('subscribe', 'subscriptions'):
            queryset = queryset.annotate(recipes_count=Count('recipes'))
        if self.action == 'subscriptions':
            return queryset.filter(subscribers__user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return SubscribePostReadSerializer
        if self.action == 'subscriptions':
            return SubscribeReadSerializer
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return self.serializer_class

    def get_instance(self):
        return self.request.user

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(['post'], detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<author_id>\d+)/subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, author_id, *args, **kwargs):
        author = get_object_or_404(self.get_queryset(), id=author_id)
        if self.request.user == author:
            return get_bad_request_response(SELF_SUBSCRIBE_ERROR)
        if self.request.method == 'DELETE':
            if not author.is_subscribed:
                return get_bad_request_response(
                    DOES_NOT_EXIST_SUBSCRIBE_ERROR.format(
                        self.request.user.username, author.username
                    )
                )
            self.request.user.subscriptions.get(author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if author.is_subscribed:
            return get_bad_request_response(UNIQUE_SUBSCRIBE_ERROR.format(
                self.request.user.username, author.username
            ))
        self.request.user.subscriptions.create(author=author)
        return Response(
            self.get_serializer(author).data,
            status=status.HTTP_201_CREATED
        )

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagReadSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
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
        )).all()
        tags = self.request.query_params.getlist('tags')
        if self.request.method == 'GET' and tags and ''.join(tags):
            return queryset.filter(tags__slug__in=tags)
        return queryset

    def get_serializer_class(self):
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortReadSerializer
        if self.request.method == 'GET':
            return RecipeReadSerializer
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
        url_path=r'(?P<recipe_id>\d+)/favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, recipe_id, *args, **kwargs):
        recipe = get_object_or_404(self.get_queryset(), id=recipe_id)
        if self.request.method == 'DELETE':
            if not recipe.is_favorited:
                return get_bad_request_response(
                    DOES_NOT_EXIST_FAVORITE_ERROR.format(
                        self.request.user.username, recipe.name
                    )
                )
            self.request.user.favorite.get(recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if recipe.is_favorited:
            return get_bad_request_response(UNIQUE_FAVORITE_ERROR.format(
                self.request.user.username, recipe.name
            ))
        self.request.user.favorite.create(recipe=recipe)
        return Response(
            self.get_serializer(recipe).data, status=status.HTTP_201_CREATED
        )

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, recipe_id, *args, **kwargs):
        recipe = get_object_or_404(self.get_queryset().filter(id=recipe_id))
        if self.request.method == 'DELETE':
            if not recipe.is_in_shopping_cart:
                return get_bad_request_response(
                    DOES_NOT_EXIST_CART_ERROR.format(
                        self.request.user.username, recipe.name
                    )
                )
            self.request.user.shopping_cart.get(recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if recipe.is_in_shopping_cart:
            return get_bad_request_response(UNIQUE_CART_ERROR.format(
                self.request.user.username, recipe.name
            ))
        self.request.user.shopping_cart.create(recipe=recipe)
        return Response(
            self.get_serializer(recipe).data, status=status.HTTP_201_CREATED
        )

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        response = FileResponse(ingredients_to_pdf([(
            f'{ingredient.name} ({ingredient.measurement_unit}) '
            f'- {ingredient.amount}'
        ) for ingredient in Ingredient.objects.filter(
            recipes__shopping_cart__user=self.request.user
        ).annotate(amount=Sum(
            'amounts_for_recipes__amount'
        ))]), as_attachment=True)
        response['Content-Type'] = 'application/pdf'
        return response
