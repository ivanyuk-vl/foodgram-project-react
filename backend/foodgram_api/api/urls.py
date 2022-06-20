from django.urls import include, path, re_path
from djoser.views import TokenDestroyView as DjoserTokenDestroyView
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet, RecipeViewSet, TagViewSet, TokenCreateView, UserViewSet
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
urlpatterns = [
    re_path(r"^auth/token/login/?$", TokenCreateView.as_view(), name="login"),
    re_path(
        r"^auth/token/logout/?$", DjoserTokenDestroyView.as_view(),
        name="logout"
    ),
    path('', include(router.urls)),
]
