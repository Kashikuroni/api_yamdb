from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator

from users.models import CustomUser


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

        if not self.partial:
            if not email or not username:
                raise serializers.ValidationError(
                    {'error': ('Отсутствует обязательное поле '
                               'email или username')}
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
