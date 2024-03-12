import datetime as dt
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.serializers import (
    ModelSerializer, SlugRelatedField,
    CurrentUserDefault, ValidationError,
    ReadOnlyField, CharField
)
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator

from reviews.models import (
    Title, Category, Genre,
    Comment, Review
)

User = get_user_model()


class BaseUserSerializer(ModelSerializer):
    """
    Абстрактный Сериализатор для работы с Пользователем и его Авторизацией.
    """
    username = CharField(
        max_length=150,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=('Поле username должно содержать '
                         'только буквы, цифры и следующие символы: @ . + -'),
            )
        ]

    )

    class Meta:
        model = User
        fields = ['email', 'username']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['role'] = instance.get_role_display()
        return representation

    def validate(self, data):
        role = data.get('role')
        if role and role not in ['admin', 'moderator', 'user']:
            raise ValidationError({'error': 'Несуществующая роль'})

        email = data.get('email')
        username = data.get('username')

        if not self.partial and (not email or not username):
            raise ValidationError(
                {'error': ('Отсутствует обязательное поле email или username')}
            )

        return data


class SignUpSerializer(BaseUserSerializer):
    """Сериализатор авторизации."""
    def validate(self, data):
        data = super().validate(data)
        username = data.get('username')
        if username == 'me':
            raise ValidationError(
                {'error': 'Недопустимое значение для имени пользователя'}
            )
        return data

    def to_representation(self, instance):
        # Исключаем поле role из данных перед возвратом
        data = super().to_representation(instance)
        data.pop('role', None)
        return data


class UserSerializer(BaseUserSerializer):
    """Сериализатор Пользователя."""
    role = CharField(required=False)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + [
            'first_name',
            'last_name',
            'bio', 'role'
        ]


class UserMeSerializer(BaseUserSerializer):
    """Сериализатор Профиля пользователя."""
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + [
            'first_name',
            'last_name',
            'bio'
        ]


class CategorySerializer(ModelSerializer):
    """Сериализатор Категорий."""
    class Meta:
        fields = ('name', 'slug')
        model = Category


class GenreSerializer(ModelSerializer):
    """Сериализатор Жанров."""
    class Meta:
        fields = ('name', 'slug')
        model = Genre


class TitleSerializer(ModelSerializer):
    """Сериализатор Произведений."""
    genre = SlugRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        slug_field='slug',
        required=False
    )
    category = SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
    )
    rating = ReadOnlyField()

    class Meta:
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )
        model = Title

    def to_representation(self, instance):
        representation = super(
            TitleSerializer, self
        ).to_representation(instance)
        representation['category'] = CategorySerializer(instance.category).data
        representation['genre'] = GenreSerializer(
            instance.genre, many=True
        ).data
        return representation

    def validate_year(self, value):
        if value > dt.datetime.now().year:
            raise ValidationError('Год не может быть больше текущего')
        return value


class BaseReviewSerializer(ModelSerializer):
    """
    Этот сериализатор является абстрактным базовым классом
    и предназначен только для наследования
    сериализаторами Отзывов и Комментариев.
    """
    author = SlugRelatedField(
        default=CurrentUserDefault(),
        slug_field='username',
        read_only=True
    )


class ReviewSerializer(BaseReviewSerializer):
    """Сериализация для отзывов."""

    class Meta:
        model = Review
        fields = ('id', 'title', 'score', 'text', 'author', 'pub_date')
        read_only_fields = ('id', 'title',)

    def validate(self, data):
        """
        Проверка, что пользователь уже оставлял комментарий
        при создании нового отзыва.
        """
        user = self.context['request'].user

        if not user.is_authenticated:
            raise ValidationError("Пользователь не авторизован.")

        if not self.instance:
            title_id = self.context['request'
                                    ].parser_context['kwargs']['title_id']
            title = get_object_or_404(Title, pk=title_id)

            if Review.objects.filter(author=user, title=title).exists():
                raise ValidationError('Вы уже оставили свой отзыв.')
        return data


class CommentSerializer(BaseReviewSerializer):
    """Сериализация для отзывов."""
    class Meta:
        model = Comment
        fields = ('id', 'review', 'text', 'author', 'pub_date')
        read_only_fields = ('id', 'review',)
