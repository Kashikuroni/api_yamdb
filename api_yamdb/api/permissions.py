from rest_framework.permissions import BasePermission, SAFE_METHODS


class AdminPermission(BasePermission):
    """Доступ только администратору и суперпользователю."""
    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
            and (request.user.is_staff or request.user.role == 'admin')
        )


class IsNotAuthenticatedSaved(BasePermission):
    """Абстрактный класс дающий доступ по безопасным методам."""
    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True


class TitlePermission(IsNotAuthenticatedSaved):
    """
    Разрешения связанные с Произведениями, Жанрами и Категориями.
    Доступ только авторизованному пользователю с ролью Админ,
    Либо только чтение.
    """
    def has_permission(self, request, view) -> bool:
        parent_permission = super().has_permission(request, view)
        if (parent_permission
                or request.user.is_authenticated
                and request.user.role == 'admin'):
            return True


class ReviewPermission(IsNotAuthenticatedSaved):
    """
    Разрешения для Отзывов и Комментариев к ним.
    Доступ только авторизованному пользователю с ролью Админ, Модератор,
    Либо Владелец,
    Либо только чтение.
    """
    def has_permission(self, request, view) -> bool:
        parent_permission = super().has_permission(request, view)
        if parent_permission or request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj) -> bool:
        if (request.method in SAFE_METHODS
                or request.user.role in ('admin', 'moderator')
                or obj.author == request.user):
            return True
