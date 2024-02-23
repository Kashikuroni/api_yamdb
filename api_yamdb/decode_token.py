import jwt

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJvc2UiLCJleHAiOjE3MDg3MTcxNDl9.V4qWJMOYs5nD4JSX5AmIRG0VWRyVE16TVbqCpqTuZz4"
decoded_token = jwt.decode(token, options={"verify_signature": False})  # Декодируем токен без проверки подписи

print(decoded_token)