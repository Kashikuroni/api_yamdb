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

    # ПОДУМАТЬ О ЗАМЕНЕ ДЕКОРАТОРОВ
    @action(detail=False, methods=['post'])
    def signup(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')

        # Проверка наличия пользователя с указанным email
        if CustomUser.objects.filter(email=email).exists():
            return Response({'error': 'Пользователь с таким email уже существует'}, status=status.HTTP_400_BAD_REQUEST)

        # Создание нового пользователя
        user = CustomUser.objects.create_user(email=email, username=username, password=password)

        # Отправка письма с кодом подтверждения
        current_site = get_current_site(request)
        mail_subject = 'Подтверждение регистрации'
        message = render_to_string('registration/confirmation_email.txt', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        send_mail(mail_subject, message, 'from@example.com', [user.email])

        return Response({'success': 'Письмо с кодом подтверждения отправлено на ваш адрес электронной почты'})

    # ПОДУМАТЬ О ЗАМЕНЕ ДЕКОРАТОРОВ
    @action(detail=False, methods=['post'])
    def resend_confirmation(self, request):
        email = request.data.get('email')

        # Проверка наличия пользователя с указанным email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Пользователь с указанным email не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Отправка письма с кодом подтверждения
        current_site = get_current_site(request)
        mail_subject = 'Повторное подтверждение регистрации'
        message = render_to_string('registration/confirmation_email.txt', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        send_mail(mail_subject, message, 'from@example.com', [user.email])

        return Response({'success': 'Письмо с кодом подтверждения отправлено на ваш адрес электронной почты'})
    
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
