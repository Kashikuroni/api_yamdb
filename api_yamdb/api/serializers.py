from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework.serializers import (
    ModelSerializer, SlugRelatedField,
    CurrentUserDefault, ValidationError,
    SerializerMethodField
)
from reviews.models import Review, Comment, Title, Category, Genre

import datetime as dt

User = get_user_model()


class CategorySerializer(ModelSerializer):
    class Meta:
        fields = ('name', 'slug')
        model = Category


class GenreSerializer(ModelSerializer):
    class Meta:
        fields = ('name', 'slug')
        model = Genre


class TitleSerializer(ModelSerializer):
    genre = SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug'
    )
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
        return scores.aggregate(Avg('score'))

    def validate_year(self, value):
        if value > dt.datetime.now().year:
            raise ValidationError("Год не может быть больше текущего")
        return value


class BaseSerializer(ModelSerializer):
    author = SlugRelatedField(
        queryset=User.objects.all(),
        default=CurrentUserDefault(),
        slug_field='username',
        read_only=True
    )

    class Meta:
        abstract = True
        read_only_fields = ('author', 'pub_date', 'id')


class ReviewSerializer(BaseSerializer):
    title = SlugRelatedField(
        queryset=Title.objects.all(),
        slug_field='name'
    )

    class Meta(BaseSerializer.Meta):
        model = Review
        fields = ('text', 'author', 'pub_date',
                  'title', 'score', 'id')


# Аналогично обновляем CommentSerializer
class CommentSerializer(BaseSerializer):

    class Meta(BaseSerializer.Meta):
        model = Comment
        fields = ('text', 'author', 'pub_date',
                  'review', 'id')
