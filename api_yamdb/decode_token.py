import jwt

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA4ODYzMjk5LCJpYXQiOjE3MDg4NjI5OTksImp0aSI6ImJlNGFhNDJkNGE0OTRiNDk4Y2RjYzRhODM3MmY5NjU4IiwidXNlcl9pZCI6N30.bW4Xicczzx1P61x4KV4A45PTM293_7eHWbPmucZTiQA"
decoded_token = jwt.decode(token, options={"verify_signature": False})  # Декодируем токен без проверки подписи

print(decoded_token)

import datetime

# Unix time, полученный из токена
exp_unix_time = 1708896519

# Преобразование Unix time в объект datetime
exp_datetime = datetime.datetime.utcfromtimestamp(exp_unix_time)

print("Время истечения срока действия токена:", exp_datetime)
