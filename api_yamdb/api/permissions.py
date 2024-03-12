from rest_framework.permissions import BasePermission, SAFE_METHODS


class AllAuthPermission(BasePermission):
    def has_permission(self, request, view):
        allowed_roles = ['user', 'moderator', 'admin']
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role
            in allowed_roles
        )


class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.role == 'admin')
        )


class IsNotAuthenticatedSaved(BasePermission):
    """Абстрактный класс дающий доступ по безопасным методам."""
    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True


class TitlePermission(IsNotAuthenticatedSaved):
    """Разрешения связанные с Произведениями, Жанрами и Категориями."""
    def has_permission(self, request, view) -> bool:
        parent_permission = super().has_permission(request, view)
        if (parent_permission
                or request.user.is_authenticated
                and request.user.role == 'admin'):
            return True


class ReviewPermission(IsNotAuthenticatedSaved):
    """Разрешения для Отзывов и Комментариев к ним."""
    def has_permission(self, request, view) -> bool:
        parent_permission = super().has_permission(request, view)
        if parent_permission or request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj) -> bool:
        if (request.method in SAFE_METHODS
                or request.user.role in ('admin', 'moderator')
                or obj.author == request.user):
            return True
