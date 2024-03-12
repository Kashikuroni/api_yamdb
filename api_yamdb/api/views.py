from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg, OuterRef, Subquery
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import filters, pagination, viewsets, mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from api.jwt_utils import create_access_token
from api.permissions import (
    AdminPermission, TitlePermission, ReviewPermission
)
from api.serializers import (
    SignUpSerializer, UserSerializer, UserMeSerializer,
    TitleSerializer, CategorySerializer, GenreSerializer,
    ReviewSerializer, CommentSerializer
)
from users.models import CustomUser
from reviews.models import Title, Category, Review
from reviews.models import Genre, Title, Category


class CustomPagination(PageNumberPagination):
    page_size = 10


class SignUpViewSet(viewsets.ModelViewSet):
    """Регистрация пользователей и отправка кода подтверждения на почту."""
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        username = request.data.get('username')
        user_exst = CustomUser.objects.filter(
            email=email,
            username=username
        ).first()

        if user_exst:
            confirmation_code = default_token_generator.make_token(user_exst)
            user_exst.confirmation_code = confirmation_code
            user_exst.save()
            self.send_confirmation_email(email, confirmation_code)
            return Response(
                {'message': ('Код подтверждения '
                             'был отправлен на ваш email')},
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        confirmation_code = default_token_generator.make_token(user)
        user.confirmation_code = confirmation_code
        user.save()
        self.send_confirmation_email(email, confirmation_code)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def send_confirmation_email(self, email, confirmation_code):
        subject = 'Код подтверждения регистрации'
        message = f'Ваш код подтверждения: {confirmation_code}'
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )


class ObtainTokenAPIView(APIView):
    """Создание и отправка токена авторизации пользователю."""
    def post(self, request, *args, **kwargs):
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

        token = create_access_token(username)
        user.token = token
        user.save()

        return Response({'token': token}, status=status.HTTP_200_OK)


class UserMeAPIView(APIView):
    """Обработка запросов к профилю пользователя."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserMeSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        serializer = UserMeSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """Обработка запросов к Пользователям."""
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [AdminPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    pagination_class = pagination.PageNumberPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get('role')
        if role == 'admin':
            user = serializer.save()
            user.is_staff = True
            user.save()
        else:
            serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user = get_object_or_404(queryset, username=kwargs['pk'])
        self.perform_destroy(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TitleViewSet(viewsets.ModelViewSet):
    """Обработка запросов к Произведениям."""
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = [TitlePermission]
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('name', 'year')
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        queryset = super().get_queryset()
        genre_slug = self.request.query_params.get('genre')
        category_slug = self.request.query_params.get('category')
        if genre_slug:
            queryset = queryset.filter(genre__slug=genre_slug)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        reviews_subquery = Review.objects.filter(
            title_id=OuterRef('pk')
        ).values('title_id').annotate(avg_rating=Avg('score')
                                      ).values('avg_rating')

        return queryset.annotate(rating=Subquery(reviews_subquery[:1]))

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
    """Абстрактный класс для обработки Категорий и Жанров."""
    filter_backends = [filters.SearchFilter]
    permission_classes = [TitlePermission]
    search_fields = ('name',)
    lookup_field = 'slug'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs['slug']}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class CategoryViewSet(BaseViewSet):
    """Обработка запросов к Категориям."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomPagination


class GenreViewSet(BaseViewSet):
    """Обработка запросов к Жанрам."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = CustomPagination


class ReviewViewSet(viewsets.ModelViewSet):
    """Обработка запросов к Отзывам."""
    serializer_class = ReviewSerializer
    permission_classes = [ReviewPermission]
    pagination_class = CustomPagination
    http_method_names = [
        'get', 'post', 'patch', 'delete',
        'head', 'options', 'trace'
    ]

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs['title_id'])
        return title.reviews.all().order_by('id')

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs['title_id'])
        serializer.save(title=title, author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    """Обработка запросов к Комментариям."""
    serializer_class = CommentSerializer
    permission_classes = [ReviewPermission]
    pagination_class = CustomPagination
    http_method_names = [
        'get', 'post', 'patch', 'delete',
        'head', 'options', 'trace'
    ]

    def get_review(self, review_id: int):
        return get_object_or_404(Review, pk=review_id)

    def get_queryset(self):
        review = self.get_review(self.kwargs['review_id'])
        return review.comments.all()

    def perform_create(self, serializer):
        review = self.get_review(self.kwargs['review_id'])
        serializer.save(review=review, author=self.request.user)
