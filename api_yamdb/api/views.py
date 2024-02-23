from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q

from .serializers import SignUpSerializer, ObtainTokenSerializer, UserSerializer
from .jwt_utils import create_access_token, decode_access_token
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

class ObtainTokenViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = ObtainTokenSerializer
    
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')

        try:
            user = CustomUser.objects.get(username=username, confirmation_code=confirmation_code)
        except ObjectDoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Создаем или получаем токен
        token = create_access_token(username)

        # Сохраняем токен в модели пользователя
        user.token = token
        user.save()

        return Response({'token': token}, status=status.HTTP_200_OK)
                

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            raise NotAuthenticated('Необходим JWT-токен')

        if not request.user.is_staff:
            raise PermissionDenied('Нет прав доступа')
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Вызываем исключение, если данные невалидны
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
