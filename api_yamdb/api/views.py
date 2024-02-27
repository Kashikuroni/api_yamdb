from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import TitleSerializer, CategorySerializer, GenreSerializer

from reviews.models import Title, Category, Genre


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('category__slug', 'genre__slug', 'name', 'year')


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('name',)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('name',)


class ReviewViewSet(viewsets.ModelViewSet):
    pass

import re
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.request import Request

from .serializers import SignUpSerializer, UserSerializer
from .jwt_utils import create_access_token
from .permissions import IsAdmin
from users.models import CustomUser

class SignUpViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        username = request.data.get('username')

        # Проверяем, существует ли уже пользователь с таким email и username
        existing_user = CustomUser.objects.filter(email=email, username=username).first()
        
        if existing_user:
                confirmation_code = get_random_string(length=6)
                existing_user.confirmation_code = confirmation_code
                existing_user.save()
                self.send_confirmation_email(email, confirmation_code)
                return Response({'message': 'Код подтверждения был отправлен на ваш email'}, status=status.HTTP_200_OK)
        
        # Если пользователь не найден, пробуем создать нового
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            confirmation_code = get_random_string(length=6)
            user.confirmation_code = confirmation_code
            user.save()
            self.send_confirmation_email(email, confirmation_code)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_confirmation_email(self, email, confirmation_code):
        subject = 'Код подтверждения регистрации'
        message = f'Ваш код подтверждения: {confirmation_code}'
        send_mail(
            subject,
            message,
            'sergeiorlovlv@gmail.com',  # Замените на свой адрес электронной почты
            [email],
            fail_silently=False,
        )

class ObtainTokenAPIView(APIView):
    
    def post(self, request, *args, **kwargs):
        # Получаем данные из запроса
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')
        
        if not (username and confirmation_code):
            return Response({'error': 'Отсутствует имя пользователя или подтверждающий код'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        if user.confirmation_code != confirmation_code:
            return Response({'error': 'Неверный подтверждающий код'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем токен
        token = create_access_token(username)
        
        # Сохраняем токен в модели пользователя
        user.token = token
        user.save()
        
        return Response({'token': token}, status=status.HTTP_200_OK)
                

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            role = serializer.validated_data.get('role')
            if role == 'admin':
                # Создаем пользователя с ролью "admin" и правами администратора
                user = serializer.save()
                user.is_staff = True
                user.save()
            else:
                serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
