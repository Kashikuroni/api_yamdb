from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    ModelSerializer, SlugRelatedField,
    CurrentUserDefault
)
from rest_framework import serializers

from reviews.models import Review, Comment, Title
from users.models import CustomUser


User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=CustomUser.ROLE_CHOICES)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'bio', 'role']

    # Вызываем родительский метод, чтобы получить базовое представление объекта
    # Затем изменяем значение поля role, чтобы отображалось значение роли CHICES вместо кода
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['role'] = instance.get_role_display()
        return representation


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
