# from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    ModelSerializer, SlugRelatedField,
    CurrentUserDefault
)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator


from reviews.models import Review, Comment, Title
from users.models import CustomUser


# User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    confirmation_code = serializers.CharField(max_length=20, required=False)
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(queryset=CustomUser.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Поле username должно содержать только буквы, цифры и следующие символы: @ . + -',
            )
        ]
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'confirmation_code']

    # Вызываем родительский метод, чтобы получить базовое представление объекта
    # Затем изменяем значение поля role, чтобы отображалось значение роли CHICES вместо кода
    # def to_representation(self, instance):
        # representation = super().to_representation(instance)
        # representation['role'] = instance.get_role_display()
        # return representation
    
    def validate(self, data):
        # Проверяем наличие email и username в данных
        email = data.get('email')
        username = data.get('username')
        if not email or not username:
            raise serializers.ValidationError({'error': 'Отсутствует обязательное поле email или username'})

        # Проверяем длину поля email
        if len(email) > 254:
            raise serializers.ValidationError({'error': 'Длина поля email не должна превышать 254 символа'})

        # Проверяем длину поля username
        if len(username) > 150:
            raise serializers.ValidationError({'error': 'Длина поля username не должна превышать 150 символов'})
        
        # Проверяем значение поля username
        username = data.get('username')
        if username == 'me':
            raise serializers.ValidationError({'error': 'Недопустимое значение для имени пользователя'})

        return data
    

class ObtainTokenSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CustomUser
        fields = ['username', 'confirmation_code']
    
    def validate(self, data):
        # Проверяем наличие username и confirmation_code в данных
        username = data.get('username')
        confirmation_code = data.get('confirmation_code')

        if not username or not confirmation_code:
            raise serializers.ValidationError({'error': 'Отсутствует обязательное поле username или confirmation_code'})

        # Проверяем длину поля onfirmation_code
        if len(confirmation_code) > 6:
            raise serializers.ValidationError({'error': 'Длина поля confirmation_code не должна превышать 254 символа'})

        # Проверяем длину поля username
        if len(username) > 150:
            raise serializers.ValidationError({'error': 'Длина поля username не должна превышать 150 символов'})

        return data
    
class UserSerializer(serializers.ModelSerializer):
    sername = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(queryset=CustomUser.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Поле username должно содержать только буквы, цифры и следующие символы: @ . + -',
            )
        ]
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'bio', 'role']
        extra_kwargs = {
        'role': {'required': False}
    }
   
    def validate(self, data):
        # Проверяем наличие email и username в данных
        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not email or not username:
            raise serializers.ValidationError({'error': 'Отсутствует обязательное поле email или username'})

        # Проверяем длину поля email
        if len(email) > 254:
            raise serializers.ValidationError({'error': 'Длина поля email не должна превышать 254 символа'})

        # Проверяем длину поля username
        if len(username) > 150:
            raise serializers.ValidationError({'error': 'Длина поля username не должна превышать 150 символов'})
        
        # Проверяем длину поля first_name
        if len(first_name) > 150:
            raise serializers.ValidationError({'error': 'Длина поля first_name не должна превышать 150 символов'})
            
        # Проверяем длину поля last_name
        if len(last_name) > 150:
            raise serializers.ValidationError({'error': 'Длина поля last_name не должна превышать 150 символов'})

        return data


# class BaseSerializer(ModelSerializer):
    # author = SlugRelatedField(
        # queryset=User.objects.all(),
        # default=CurrentUserDefault(),
        # slug_field='username',
        # read_only=True
    # )

    # class Meta:
        # abstract = True
        # read_only_fields = ('author', 'pub_date', 'id')


# class ReviewSerializer(BaseSerializer):
    # title = SlugRelatedField(
        # queryset=Title.objects.all(),
        # slug_field='name'
    # )

    # class Meta(BaseSerializer.Meta):
        # model = Review
        # fields = ('text', 'author', 'pub_date',
                  # 'title', 'score', 'id')


# Аналогично обновляем CommentSerializer
# class CommentSerializer(BaseSerializer):

    # class Meta(BaseSerializer.Meta):
        # model = Comment
        # fields = ('text', 'author', 'pub_date',
                  # 'review', 'id')
