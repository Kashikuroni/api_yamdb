from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import filters, pagination, viewsets
from rest_framework.pagination import PageNumberPagination

from api.jwt_utils import create_access_token
from api.permissions import AllAuthPermission, AdminPermission
from api.serializers import (
    SignUpSerializer, UserSerializer, UserMeSerializer,
    TitleSerializer, CategorySerializer, GenreSerializer,
    ReviewSerializer, CommentSerializer
)
from users.models import CustomUser
from reviews.models import Title, Category, Genre


class SignUpViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        username = request.data.get('username')

        # Проверяем, существует ли уже пользователь с таким email и username
        existing_user = CustomUser.objects.filter(
            email=email,
            username=username
        ).first()

        if existing_user:
            confirmation_code = get_random_string(length=6)
            existing_user.confirmation_code = confirmation_code
            existing_user.save()
            self.send_confirmation_email(email, confirmation_code)
            return Response(
                {'message': ('Код подтверждения '
                             'был отправлен на ваш email')},
                status=status.HTTP_200_OK
            )

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
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    def send_confirmation_email(self, email, confirmation_code):
        subject = 'Код подтверждения регистрации'
        message = f'Ваш код подтверждения: {confirmation_code}'
        send_mail(
            subject,
            message,
            # Замените на свой адрес электронной почты
            'sergeiorlovlv@gmail.com',
            [email],
            fail_silently=False,
        )


class ObtainTokenAPIView(APIView):

    def post(self, request, *args, **kwargs):
        # Получаем данные из запроса
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')

        if not (username and confirmation_code):
            return Response(
                {'error': ('Отсутствует имя пользователя '
                           'или подтверждающий код')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.confirmation_code != confirmation_code:
            return Response(
                {'error': 'Неверный подтверждающий код'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем токен
        token = create_access_token(username)

        # Сохраняем токен в модели пользователя
        user.token = token
        user.save()

        return Response({'token': token}, status=status.HTTP_200_OK)


class UserMeAPIView(APIView):
    # Используем свой класс разрешений
    permission_classes = [AllAuthPermission]

    def get(self, request):
        # Получаем текущего аутентифицированного пользователя
        user = request.user
        serializer = UserMeSerializer(user)  # Сериализуем пользователя
        return Response(serializer.data)  # Возвращаем данные пользователя

    def patch(self, request):
        # Получаем текущего аутентифицированного пользователя
        user = request.user
        # Обновляем данные пользователя
        serializer = UserMeSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AdminPermission]  # Используем свой класс разрешений
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    pagination_class = pagination.PageNumberPagination

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
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginator = self.pagination_class()
            data = {
                'count': paginator.page.paginator.count,
                'next': (paginator.get_next_link()
                         if paginator.get_next_link() else None),
                'previous': (paginator.get_previous_link()
                             if paginator.get_previous_link() else None),
                'results': serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                'count': queryset.count(),
                'next': None, 'previous': None,
                'results': serializer.data
            }, status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        queryset = CustomUser.objects.filter(username=kwargs['pk'])
        user = get_object_or_404(queryset)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user = get_object_or_404(queryset, username=kwargs['pk'])
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user = get_object_or_404(queryset, username=kwargs['pk'])
        self.perform_destroy(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('category__slug', 'genre__slug', 'name', 'year')
    pagination_class = PageNumberPagination


def check_permissions(view_func):
    def check_view(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.user.role != 'admin':
            return Response(status=status.HTTP_403_FORBIDDEN)
        return view_func(self, request, *args, **kwargs)
    return check_view


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.order_by('id')
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('name',)
    pagination_class = PageNumberPagination
    lookup_field = 'slug'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs['slug']}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    @check_permissions
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @check_permissions
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @check_permissions
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.order_by('id')
    serializer_class = GenreSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('name',)
    pagination_class = PageNumberPagination


class ReviewViewSet(viewsets.ModelViewSet):
    """Обработка запросов по отзывам."""
    serializer_class = ReviewSerializer


class CommentViewSet(viewsets.ModelViewSet):
    """Обработка запросов по комментариям."""
    serializer_class = CommentSerializer

