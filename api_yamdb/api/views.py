import random
import string

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
# НАДО БУДЕТ ЗАМЕНИТЬ НА СВОИ ПРЕМИШЕНЫ
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string

from .serializers import CustomUserSerializer
from users.models import CustomUser
from jwt_utils import create_access_token, decode_access_token


class CustomUserViewSet(viewsets.ViewSet):
    # НАДО БУДЕТ ЗАМЕНИТЬ НА СВОИ ПРЕМИШЕНЫ
    permission_classes = [IsAuthenticated, IsAdminUser]

    # Генерируем код подтверждения
    @staticmethod
    def generate_confirmation_code(length=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    # Отправляем письмо с кодом подтверждения
    @staticmethod
    def send_confirmation_code(user, request):
        mail_subject = 'Подтверждение регистрации'
        message = f'Ваш код подтверждения {user.confirmation_code}.'
        send_mail(mail_subject, message, 'segeiorlovlv@gmail.com', [user.email])

    # ПОДУМАТЬ О ЗАМЕНЕ ДЕКОРАТОРОВ
    @action(detail=False, methods=['post'])
    def signup(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        
        # Проверка наличия пользователя с указанным email
        existing_user = CustomUser.objects.filter(email=email).exists()
        if existing_user:
            self.send_confirmation_code(existing_user, request)
            return Response({'success': 'Письмо с кодом подтверждения отправлено на Ваш адрес электронной почты'})
            
        # Создание нового пользователя
        user = CustomUser.objects.create_user(email=email, username=username)
        # Генерация кода подтверждения и сохранение его в модели пользователя
        user.confirmation_code = self.generate_confirmation_code()
        user.save()

        # Отправка письма с кодом подтверждения
        self.send_confirmation_code(user, request)
        return Response({'success': 'Письмо с кодом подтверждения отправлено на Ваш адрес электронной почты'})
    
    @action(detail=False, methods=['get'])
    def list_all_users(self, request):
        # Проверяем, является ли пользователь администратором
        if not request.user.is_staff:
            return Response({'error': 'Доступ запрещён'}, status=status.HTTP_403_FORBIDDEN)
        
        # Проверяем наличие JWT-токена и декодируем его
        token = request.headers.get('Authorization', '').split(' ')[1]
        token_payload = decode_access_token(token)
        if 'error' in token_payload:
            return Response({'error': 'Некорректный токен'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Получаем список всех пользователей
        users = CustomUser.objects.all()

        # Сериализуем список пользователей и отправляем в ответе
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Добавление нового пользователя, который доступен только администратору
    def create(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Получение пользователя по его username с правами доступа только для администратора
    def retrieve(self, request, username=None):
        user = get_object_or_404(CustomUser, username=username)
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)
    
    # Изменение данных пользователя по его username с правами доступа только для администратора
    def update(self, request, username=None):
        user = get_object_or_404(CustomUser, username=username)
        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Удаление пользователя по его username с правами доступа только для администратора
    def destroy(self, request, username=None):
        user = get_object_or_404(CustomUser, username=username)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Получение JWT-токена:
class ObtainJWTTokenViewSet(viewsets.ViewSet):
    def create(self, request):
        # Получаем данные из запроса
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')

        # Проверяем, что оба поля присутствуют в запросе
        if not username or not confirmation_code:
            return Response({'error': 'Both username and confirmation code are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пользователь существует и подтверждение кода совпадает
        try:
            user = CustomUser.objects.get(username=username)
            if user.confirmation_code != confirmation_code:
                return Response({'error': 'Invalid confirmation code'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Создаем JWT-токен для пользователя
        token = create_access_token(username)

        # Отправляем токен в ответе
        return Response({'token': token}, status=status.HTTP_200_OK)


# Получение и изменение данных своей учетной записи
class MyAccountViewSet(viewsets.ViewSet):
    # НАДО БУДЕТ ЗАМЕНИТЬ НА СВОИ ПРЕМИШЕНЫ
    permission_classes = [IsAuthenticated]

    # Получение данных своей учетной записи
    def retrieve(self, request):
        user = request.user
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)
    
    # Изменение данных своей учетной записи
    def update(self, request):
        # Проверяем, что пользователь аутентифицирован
        if request.user.is_authenticated:
            # Получаем имя пользователя
            username = request.user.username

            # Создаем JWT-токен
            access_token = create_access_token(username)

            # Обновляем данные пользователя
            user = request.user
            serializer = CustomUserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Пользователь не аутентифицирован
            return Response({'error': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
