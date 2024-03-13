from datetime import datetime, timedelta
import uuid

from django.conf import settings
import jwt

from users.models import CustomUser


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(username):

    # Находим пользователя по имени пользователя (username)
    user = CustomUser.objects.get(username=username)
    user_id = user.id

    # Время истечения срока действия токена
    expiration_time = (datetime.utcnow()
                       + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                       )

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

    # Генерируем токен с указанным payload
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token
