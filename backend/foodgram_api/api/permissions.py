from rest_framework.permissions import (
    BasePermission, IsAuthenticatedOrReadOnly, SAFE_METHODS
)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_anonymous and request.user.is_staff


class IsAdminOrIsAuthorOrReadOnly(
    IsAuthenticatedOrReadOnly, IsAdmin
):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
            or IsAdmin.has_permission(self, request, view)
        )
