from django.contrib.auth import get_user_model
from django.db.models import Avg

from rest_framework.serializers import (
    ModelSerializer, SlugRelatedField,
    CurrentUserDefault, ValidationError,
    SerializerMethodField
)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator

from reviews.models import (
    Title, Category, Genre,
    Comment, Review
)

from users.models import CustomUser
import datetime as dt

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(queryset=CustomUser.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=('Поле username должно содержать '
                         'только буквы, цифры и следующие символы: @ . + -'),
            )
        ]

    )

    class Meta:
        model = CustomUser
        fields = ['email', 'username']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['role'] = instance.get_role_display()
        return representation

    def validate(self, data):
        role = data.get('role')
        # Проверяем, что роль существует
        if role and role not in ['admin', 'moderator', 'user']:
            raise serializers.ValidationError({'error': 'Несуществующая роль'})

        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not self.partial and (not email or not username):
            raise serializers.ValidationError(
                {'error': ('Отсутствует обязательное поле email или username')}
            )

        if email and len(email) > 254:
            raise serializers.ValidationError(
                {'error': ('Длина поля email '
                           'не должна превышать 254 символа')}
            )

        if username and len(username) > 150:
            raise serializers.ValidationError(
                {'error': ('Длина поля username '
                           'не должна превышать 150 символов')}
            )

        if first_name and len(first_name) > 150:
            raise serializers.ValidationError(
                {'error': ('Длина поля first_name '
                           'не должна превышать 150 символов')}
            )

        if last_name and len(last_name) > 150:
            raise serializers.ValidationError(
                {'error': ('Длина поля last_name '
                           'не должна превышать 150 символов')}
            )

        return data


class SignUpSerializer(BaseUserSerializer):
    def validate(self, data):
        data = super().validate(data)
        username = data.get('username')
        if username == 'me':
            raise serializers.ValidationError(
                {'error': 'Недопустимое значение для имени пользователя'}
            )
        return data

    def to_representation(self, instance):
        # Исключаем поле role из данных перед возвратом
        data = super().to_representation(instance)
        data.pop('role', None)
        return data


class UserSerializer(BaseUserSerializer):
    role = serializers.CharField(required=False)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + [
            'first_name',
            'last_name',
            'bio', 'role'
        ]


class UserMeSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + [
            'first_name',
            'last_name',
            'bio'
        ]


class CategorySerializer(ModelSerializer):
    class Meta:
        fields = ('name', 'slug')
        model = Category


class GenreSerializer(ModelSerializer):
    class Meta:
        fields = ('name', 'slug')
        model = Genre


class TitleSerializer(ModelSerializer):
    genre = GenreSerializer(required=False, many=True)
    category = SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    rating = SerializerMethodField()

    class Meta:
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )
        model = Title

    def get_rating(self, obj):
        scores = Review.objects.filter(title__name=obj.name)
        avg_score = scores.aggregate(Avg('score'))['score__avg']
        if avg_score is not None:
            return int(round(avg_score))
        return None

    def validate_year(self, value):
        if value > dt.datetime.now().year:
            raise ValidationError("Год не может быть больше текущего")
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


class CommentSerializer(BaseReviewSerializer):
    """Сериализация для отзывов."""
    class Meta:
        model = Comment
        fields = ('id', 'review', 'text', 'author', 'pub_date')
        read_only_fields = ('id', 'review',)
