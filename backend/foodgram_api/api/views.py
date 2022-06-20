from django.db.models import Count, Exists, OuterRef, Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser import utils
from djoser.conf import settings as djoser_settings
from djoser.serializers import SetPasswordSerializer, UserCreateSerializer
from djoser.views import TokenCreateView as DjoserTokenCreateView
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
    SubscribeReadSerializer, RecipeReadSerializer, RecipeShortReadSerializer,
    RecipeSerializer, TagReadSerializer, UserReadSerializer, UserSerializer
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


class RelationMixin:
    def relation(
        self, request, id, is_related_name, related_manager_name,
        does_not_exist_error, unique_error
    ):
        instance = get_object_or_404(self.get_queryset(), id=id)
        instance_name = 'author' if (
            is_related_name == 'is_subscribed'
        ) else 'recipe'
        if (
            is_related_name == 'is_subscribed'
            and self.request.method == 'POST'
            and self.request.user == instance
        ):
            return get_bad_request_response(SELF_SUBSCRIBE_ERROR)
        if self.request.method == 'DELETE':
            if not getattr(instance, is_related_name):
                return get_bad_request_response(
                    does_not_exist_error.format(
                        self.request.user.username,
                        getattr(instance, 'name', None) or instance.username
                    )
                )
            getattr(self.request.user, related_manager_name).get(
                **{instance_name: instance}
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if getattr(instance, is_related_name):
            return get_bad_request_response(unique_error.format(
                self.request.user.username,
                getattr(instance, 'name', None) or instance.username
            ))
        getattr(self.request.user, related_manager_name).create(
            **{instance_name: instance}
        )
        return Response(
            self.get_serializer(instance).data, status=status.HTTP_201_CREATED
        )


class TokenCreateView(DjoserTokenCreateView):
    def _action(self, serializer):
        token = utils.login_user(self.request, serializer.user)
        token_serializer_class = djoser_settings.SERIALIZERS.token
        return Response(
            data=token_serializer_class(token).data,
            status=status.HTTP_201_CREATED
        )


class UserViewSet(
    mixins.CreateModelMixin, mixins.RetrieveModelMixin,
    mixins.ListModelMixin, GenericViewSet, RelationMixin
):
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
        if self.action == 'me':
            return UserReadSerializer
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
        self.request.user.set_password(
            serializer.validated_data['new_password']
        )
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<author_id>\d+)/subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, author_id, *args, **kwargs):
        return self.relation(
            request, author_id, 'is_subscribed', 'subscriptions',
            DOES_NOT_EXIST_SUBSCRIBE_ERROR, UNIQUE_SUBSCRIBE_ERROR
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

    def get_object(self):
        self.filter_backends = ()
        return super().get_object()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagReadSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet, RelationMixin):
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.annotate(is_subscribed=Exists(
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

    def get_serializer_class(self):
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortReadSerializer
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return self.serializer_class

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        tags = self.request.query_params.getlist('tags')
        if tags and ''.join(tags):
            filtered_queryset = queryset.filter(tags__slug=tags.pop())
            for tag in tags:
                filtered_queryset = filtered_queryset.union(
                    queryset.filter(tags__slug=tag)
                )
            return filtered_queryset.order_by(
                *queryset.model._meta.ordering
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = False
        return super().update(request, *args, **kwargs)

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, recipe_id, *args, **kwargs):
        return self.relation(
            request, recipe_id, 'is_favorited', 'favorite',
            DOES_NOT_EXIST_FAVORITE_ERROR, UNIQUE_FAVORITE_ERROR
        )

    @action(
        ['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, recipe_id, *args, **kwargs):
        return self.relation(
            request, recipe_id, 'is_in_shopping_cart', 'shopping_cart',
            DOES_NOT_EXIST_CART_ERROR, UNIQUE_CART_ERROR
        )

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        response = FileResponse(ingredients_to_pdf([(
            f'{name} ({measurement_unit}) - {amount}'
        ) for name, measurement_unit, amount in Ingredient.objects.filter(
            recipes__shopping_cart__user=self.request.user
        ).annotate(amount=Sum(
            'amounts_for_recipes__amount'
        )).values_list(
            'name', 'measurement_unit', 'amount'
        )]), as_attachment=True)
        response['Content-Type'] = 'application/pdf'
        return response
