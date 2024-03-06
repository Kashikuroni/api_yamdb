from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import filters, pagination, viewsets, mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

from api.jwt_utils import create_access_token
from api.permissions import (
    AllAuthPermission, AdminPermission,
    author_or_admin_permission,
    CustomPermission
)
from api.serializers import (
    SignUpSerializer, UserSerializer, UserMeSerializer,
    TitleSerializer, CategorySerializer, GenreSerializer,
    ReviewSerializer, CommentSerializer
)
from users.models import CustomUser
from reviews.models import Title, Category, Review
from reviews.models import Genre, Title, Category


class SignUpViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('id')
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
    permission_classes = [AllAuthPermission]

    def get(self, request):
        user = request.user
        serializer = UserMeSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        serializer = UserMeSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [AdminPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    pagination_class = pagination.PageNumberPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            role = serializer.validated_data.get('role')
            if role == 'admin':
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
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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


def check_permissions(view_func):
    def check_view(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role != 'admin':
                return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return view_func(self, request, *args, **kwargs)
    return check_view


class CustomPagination(PageNumberPagination):
    page_size = 10


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = [CustomPermission]
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('name', 'year')
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        queryset = super().get_queryset().order_by('id')
        genre_slug = self.request.query_params.get('genre')
        category_slug = self.request.query_params.get('category')
        if genre_slug:
            queryset = queryset.filter(genre__slug=genre_slug)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BaseViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin
):
    filter_backends = [filters.SearchFilter]
    permission_classes = [CustomPermission]
    search_fields = ('name',)
    lookup_field = 'slug'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs['slug']}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomPagination


class GenreViewSet(BaseViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = CustomPagination


def edit_permissions(view_func):
    """
    Декоратор для проверки:
    Авторизации, Авторства, Админ или Модератор.
    """
    def check_view(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if (request.user.role not in ('admin', 'moderator')
                and self.get_object().author != self.request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return view_func(self, request, *args, **kwargs)
    return check_view


class ReviewViewSet(viewsets.ModelViewSet):
    """Обработка запросов по отзывам."""
    serializer_class = ReviewSerializer
    pagination_class = CustomPagination
    http_method_names = [
        'get', 'post', 'patch', 'delete',
        'head', 'options', 'trace'
    ]

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs['title_id'])
        return title.reviews.all().order_by('id')

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response({'error': 'Вы уже оставили свой отзыв'},
                            status=status.HTTP_400_BAD_REQUEST)

    @author_or_admin_permission
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @author_or_admin_permission
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs['title_id'])
        serializer.save(title=title, author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    """Обработка запросов по комментариям."""
    serializer_class = CommentSerializer
    pagination_class = CustomPagination
    http_method_names = [
        'get', 'post', 'patch', 'delete',
        'head', 'options', 'trace'
    ]

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs['review_id'])
        return review.comments.all().order_by('id')

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response({'error': 'Вы уже оставили свой отзыв'},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @author_or_admin_permission
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @author_or_admin_permission
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        review = get_object_or_404(Review, pk=self.kwargs['review_id'])
        serializer.save(review=review, author=self.request.user)
