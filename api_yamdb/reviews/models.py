from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxValueValidator, MinValueValidator
)

from django.db import models

User = get_user_model()


class BaseModel(models.Model):
    name = models.CharField(
        'Название',
        max_length=256
    )
    slug = models.SlugField(
        max_length=50,
        unique=True
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name


class Category(BaseModel):
    class Meta:
        db_table = 'reviews_category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(BaseModel):
    class Meta:
        db_table = 'reviews_genre'
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    name = models.CharField(
        'Название',
        max_length=256
    )
    year = models.IntegerField('Год выпуска')
    description = models.TextField(
        'Описание',
        blank=True
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True
    )
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        verbose_name='Жанр',
    )

    class Meta:
        db_table = 'reviews_title'
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'


class GenreTitle(models.Model):
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.title} {self.genre}'


class BaseReviewModel(models.Model):
    text = models.CharField(
        'Текст',
        max_length=1024
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f'{self.author} - {self.text}'


class Review(BaseReviewModel):
    title = models.OneToOneField(
        Title,
        verbose_name='Произведение',
        on_delete=models.CASCADE
    )
    score = models.PositiveSmallIntegerField(
        'Оценка',
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ]
    )

    class Meta:
        db_table = 'reviews_review'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class Comment(BaseReviewModel):
    review = models.ForeignKey(
        Review,
        verbose_name='Отзыв',
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'reviews_comment'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
