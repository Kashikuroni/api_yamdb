from rest_framework.permissions import BasePermission
from rest_framework import response, status


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


def author_or_admin_permission(func):
    def check_view(self, request, *args, **kwargs):
        if (request.user.role in ('admin', 'moderator')
                or self.get_object().author == self.request.user):
            return func(self, request, *args, **kwargs)
        return response.Response(status=status.HTTP_403_FORBIDDEN)
    return check_view


class CustomPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        elif (request.user and request.user.is_authenticated
              and request.user.role == 'admin'):
            return True
        else:
            return (request.user and request.user.is_authenticated
                    and request.user.is_staff)


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


def author_or_admin_permission(func):
    def check_view(self, request, *args, **kwargs):
        if (request.user.role in ('admin', 'moderator')
                or self.get_object().author == self.request.user):
            return func(self, request, *args, **kwargs)
        return response.Response(status=status.HTTP_403_FORBIDDEN)
    return check_view
