# api_yamdb
api_yamdb

## Описание
YaMDb - платформа для сбора отзывов пользователей на различные произведения, такие как книги, фильмы и музыка.
Пользователи могут оставлять отзывы, комментарии и ставить оценки на произведения.
***Сами произведения в YaMDb не хранятся, здесь нельзя посмотреть фильм или послушать музыку.***

## Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:Kashikuroni/api_yamdb.git
cd api_yamdb
```
Cоздать и активировать виртуальное окружение:
```
python -m venv venv
source venv/Scripts/activate
```
Установить зависимости из файла _requirements.txt_:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Выполнить миграции:
```
python manage.py migrate
```
Запустить проект:
```
python manage.py runserver
```

## Примеры запросов
Получение списка всех произведений:
```
GET
http://127.0.0.1:8000/api/v1/titles/
```
Добавление произведения:
```
POST
http://127.0.0.1:8000/api/v1/titles/
{
  "name": "string",
  "year": 0,
  "description": "string",
  "genre": [
       "string"
  ],
  "category": "string"
}
```
Получение списка всех категорий:
```
GET
http://127.0.0.1:8000/api/v1/categories/
```
Получение списка всех жанров:
```
GET
http://127.0.0.1:8000/api/v1/genres/
```
Получение списка всех отзывов к произведению:
```
GET
http://127.0.0.1:8000/api/v1/titles/{title_id}/reviews/
```
Получение комментария к публикации по id:
```
GET
http://127.0.0.1:8000/api/v1/posts/{post_id}/comments/{id}/
```
Получение отзыва по id:
```
GET
http://127.0.0.1:8000/api/v1/titles/{title_id}/reviews/{review_id}/
```
Получение списка всех комментариев к отзыву:
```
GET
http://127.0.0.1:8000/api/v1/titles/{title_id}/reviews/{review_id}/comments/
```
