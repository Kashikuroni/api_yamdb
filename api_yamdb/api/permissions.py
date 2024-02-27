from rest_framework.permissions import BasePermission


class AllAuthPermission(BasePermission):

    def has_permission(self, request, view):
        # Разрешаем доступ только для пользователей с определенными ролями
        # Указываем разрешенные роли
        allowed_roles = ['user', 'moderator', 'admin']
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role
            in allowed_roles
        )


class AdminPermission(BasePermission):

    def has_permission(self, request, view):
        # Разрешаем доступ только для администратора
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.role == 'admin')
        )
