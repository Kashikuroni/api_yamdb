from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

# from .jwt_utils import decode_access_token
from users.models import CustomUser


class IsAdmin(BasePermission):
    
    def has_permission(self, request, view):
        # Получаем заголовок Authorization из запроса
        authorization_header = request.headers.get('Authorization')
                
        # Проверяем наличие заголовка и формат токена
        if not authorization_header or not authorization_header.startswith('Bearer '):
            raise AuthenticationFailed('Необходим JWT-токен в заголовке Authorization')

        # Извлекаем токен из заголовка
        token = authorization_header.split(' ')[1]
        
        # Попытка аутентификации пользователя с помощью JWT
        jwt_authentication = JWTAuthentication()
        try:
            user, _ = jwt_authentication.authenticate(request)
        except AuthenticationFailed as e:
            # Если аутентификация не удалась, возвращаем False
            raise AuthenticationFailed('Недействительный JWT-токен')
        
        # Проверяем, была ли успешно аутентификация
        if user is None:
            return False

        # Проверяем, является ли пользователь администратором
        if user.is_staff or user.username == 'TestAdmin':
            return True
        
        return False
    

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Проверяет, аутентифицирован ли пользователь, иначе разрешает только чтение.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated or request.method in ['GET', 'HEAD', 'OPTIONS']

class IsModeratorOrReadOnly(BasePermission):
    """
    Проверяет, является ли пользователь модератором, иначе разрешает только чтение.
    """
    def has_permission(self, request, view):
        return request.user.role == 'moderator' or request.method in ['GET', 'HEAD', 'OPTIONS']

class CanModifyAnyReviewOrComment(BasePermission):
    """
    Проверяет, имеет ли пользователь право редактировать или удалять любые отзывы и комментарии.
    """
    def has_object_permission(self, request, view, obj):
        # Проверяем, является ли пользователь модератором
        if request.user.role == 'moderator':
            # Проверяем, имеет ли пользователь право редактировать или удалять данный объект
            return True
        return False
