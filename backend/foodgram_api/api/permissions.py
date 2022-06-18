from rest_framework.permissions import (
    BasePermission, IsAuthenticatedOrReadOnly, SAFE_METHODS
)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_anonymous and request.user.is_staff


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
