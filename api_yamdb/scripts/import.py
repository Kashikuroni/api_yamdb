import csv
from pprint import pprint as pp

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.conf import settings

from reviews.models import Genre, Category, Title, Review, GenreTitle, Comment

User = get_user_model()

IMPORT_PATH = str(settings.BASE_DIR) + '/static/data/'
IMPORT_FILES_MODELS = (
    ('users.csv', 'User', 'users'),
    ('genre.csv', 'Genre', 'reviews'),
    ('category.csv', 'Category', 'reviews'),
    ('titles.csv', 'Title', 'reviews'),
    ('review.csv', 'Review', 'reviews'),
    ('comments.csv', 'Comment', 'reviews'),
    # ('genre_title.csv', 'GenreTitle'),
)


def run():
    import_users('users.csv')
    import_genre('genre.csv')
    import_category('category.csv')
    import_titles('titles.csv')
    import_review('review.csv')
    import_comments('comments.csv')
    import_genre_title('genre_title.csv')
    pp(connection.queries)
    pp(len(connection.queries))
    total_time = sum(float(query['time']) for query in connection.queries)
    print(f"Общее время выполнения запросов: {total_time} секунд")


def import_users(file_name: str) -> None:
    """SQL Оптимизированная функция по добавлению Пользователей."""
    with open(IMPORT_PATH + file_name,
              newline='',
              encoding='utf-8') as csvfile:
        users_exists = {
            user.id: user for user in User.objects.all()
        }
        with transaction.atomic():
            reader = csv.DictReader(csvfile)
            to_be_created = []
            for row in reader:
                if int(row['id']) not in users_exists:
                    to_be_created.append(User(**row))

            User.objects.bulk_create(to_be_created)


def import_genre(file_name: str) -> None:
    """SQL Оптимизированная функция по добавлению Жанров."""
    with open(IMPORT_PATH + file_name,
              newline='',
              encoding='utf-8') as csvfile:
        genres_exists = {
            genre.id: genre for genre in Genre.objects.all()
        }
        with transaction.atomic():
            reader = csv.DictReader(csvfile)
            to_be_created = []
            for row in reader:
                if int(row['id']) not in genres_exists:
                    to_be_created.append(Genre(**row))

            Genre.objects.bulk_create(to_be_created)


def import_category(file_name: str) -> None:
    """SQL Оптимизированная функция по добавлению Произведений."""
    with open(IMPORT_PATH + file_name,
              newline='',
              encoding='utf-8') as csvfile:
        category_exists = {
            category.id: category for category in Category.objects.all()
        }

        with transaction.atomic():
            reader = csv.DictReader(csvfile)
            to_be_created = []
            for row in reader:
                if int(row['id']) not in category_exists:
                    to_be_created.append(Category(**row))

            Category.objects.bulk_create(to_be_created)


def import_titles(file_name: str) -> None:
    """SQL Оптимизированная функция по добавлению Произведений."""
    with open(IMPORT_PATH + file_name,
              newline='',
              encoding='utf-8') as csvfile:
        category_dict = {
            category.id: category for category in Category.objects.all()
        }
        title_exists = {title.id: title for title in Title.objects.all()}

        with transaction.atomic():
            reader = csv.DictReader(csvfile)
            to_be_created = []
            for row in reader:
                category_id = int(row.pop('category'))
                row.update(category=category_dict.get(category_id))

                if (row['category'] and (int(row['id'])) not in title_exists):
                    to_be_created.append(Title(**row))

            Title.objects.bulk_create(to_be_created)


def import_review(file_name: str) -> None:
    """SQL Оптимизированная функция по добавлению Отзывов."""
    with open(IMPORT_PATH + file_name,
              newline='',
              encoding='utf-8') as csvfile:

        titles_dict = {title.id: title for title in Title.objects.all()}
        users_dict = {user.id: user for user in User.objects.all()}
        review_exists = {review.id: review for review in Review.objects.all()}

        with transaction.atomic():
            reader = csv.DictReader(csvfile)
            to_be_created = []
            for row in reader:
                title_id = int(row.pop('title_id'))
                author_id = int(row.pop('author'))

                row.update(title=titles_dict.get(title_id))
                row.update(author=users_dict.get(author_id))

                if (row['title'] and row['author']
                        and (int(row['id'])) not in review_exists):
                    to_be_created.append(Review(**row))

            Review.objects.bulk_create(to_be_created)


def import_comments(file_name: str) -> None:
    """SQL Оптимизированная функция по добавлению Комментарием."""
    with open(IMPORT_PATH + file_name,
              newline='',
              encoding='utf-8') as csvfile:

        # Создаем словари с объектами из базы
        # чтобы не делать лишних SQL запросов.
        reviews_dict = {review.id: review for review in Review.objects.all()}
        users_dict = {user.id: user for user in User.objects.all()}
        comments_exists = {
            comment.id: comment for comment in Comment.objects.all()
        }

        with transaction.atomic():
            reader = csv.DictReader(csvfile)
            to_be_created = []
            for row in reader:
                review_id = int(row.pop('review_id'))
                author_id = int(row.pop('author'))

                row.update(review=reviews_dict.get(review_id))
                row.update(author=users_dict.get(author_id))

                if (row['review'] and row['author']
                        and (int(row['id'])) not in comments_exists):
                    to_be_created.append(Comment(**row))

            Comment.objects.bulk_create(to_be_created)


def import_genre_title(file_name: str) -> None:
    """
    SQL Оптимизированная функция по добавлению
    ManyToMany Жанров и Произведений.
    """
    with open(IMPORT_PATH + file_name,
              newline='',
              encoding='utf-8') as csvfile:
        titles_dict = {title.id: title for title in Title.objects.all()}
        genre_dict = {genre.id: genre for genre in Genre.objects.all()}
        genre_title_exists = {
            (gt.title_id, gt.genre_id): gt for gt in GenreTitle.objects.all()
        }

        with transaction.atomic():
            reader = csv.DictReader(csvfile)
            to_be_created = []
            for row in reader:
                title_id = int(row.pop('title_id'))
                genre_id = int(row.pop('genre_id'))

                row.update(title=titles_dict.get(title_id))
                row.update(genre=genre_dict.get(genre_id))

                if (row['title'] and row['genre']
                        and (title_id, genre_id) not in genre_title_exists):
                    to_be_created.append(GenreTitle(**row))

            GenreTitle.objects.bulk_create(to_be_created)


if __name__ == 'builtins':
    run()
