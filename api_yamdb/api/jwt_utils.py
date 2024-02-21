from datetime import datetime, timedelta
from django.conf import settings
import jwt

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(username: str) -> str:
    # Создаем payload токена
    payload = {
        'sub': username,
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    # Генерируем токен с указанным payload
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_access_token(token: str) -> dict:
    try:
        # Декодируем токен и получаем payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # В случае истечения срока действия токена, возвращаем ошибку
        return {'error': 'Срок действия токена истёк'}
    except jwt.InvalidTokenError:
        # В случае некорректного токена, возвращаем ошибку
        return {'error': 'Некорректный токен'}
