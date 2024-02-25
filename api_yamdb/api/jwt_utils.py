from datetime import datetime, timedelta
from django.conf import settings
import jwt
import uuid

from users.models import CustomUser


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(username):

    # Находим пользователя по имени пользователя (username)
    user = CustomUser.objects.get(username=username)
    user_id = user.id
    
    # Время истечения срока действия токена
    expiration_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Время начала действия токена
    issued_at = datetime.utcnow()

    # Уникальный идентификатор токена
    token_id = str(uuid.uuid4())

    # Создаем payload токена
    payload = {
        'token_type': 'access',
        'user_id': user_id,
        'exp': expiration_time,
        'iat': issued_at,
        'jti': token_id
    }

    print("Token Payload:", payload)
    # Генерируем токен с указанным payload
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# def decode_access_token(token: str) -> dict:
    # try:
        # Декодируем токен и получаем payload
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # return payload
    # except jwt.ExpiredSignatureError:
        # В случае истечения срока действия токена, возвращаем ошибку
        # return {'error': 'Срок действия токена истёк'}
    # except jwt.InvalidTokenError:
        # В случае некорректного токена, возвращаем ошибку
        # return {'error': 'Некорректный токен'}
