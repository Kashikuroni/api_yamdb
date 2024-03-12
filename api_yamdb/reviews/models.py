from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxValueValidator, MinValueValidator
)

from django.db import models

User = get_user_model()

MINIMAL_SCORE = 0
MAXIMUM_SCORE = 10


class BaseModel(models.Model):
    """Абстрактная базовая модель для Жанров и Категорий."""
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
    """Модель Категорий."""
    class Meta:
        db_table = 'reviews_category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['id']


class Genre(BaseModel):
    """Модель Жанров."""
    class Meta:
        db_table = 'reviews_genre'
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['id']


class Title(models.Model):
    """Модель Произведений."""
    name = models.CharField(
        'Название',
        max_length=256
    )
    year = models.PositiveSmallIntegerField('Год выпуска')
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
        ordering = ['id']

    def __str__(self):
        return f'{self.name} {self.genre}'


class GenreTitle(models.Model):
    """Модель связи ManyToMany Жанров и Произведений."""
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Жанр произведения'
        verbose_name_plural = 'Жанры произведений'
        ordering = ['id']

    def __str__(self):
        return f'{self.title} {self.genre}'


class BaseReviewModel(models.Model):
    """Базовая абстрактная модель для Отзывов и Комментарием."""
    text = models.CharField(
        'Текст',
        max_length=1024
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ['id']

    def __str__(self):
        return f'{self.text} {self.pub_date}'


class Review(BaseReviewModel):
    """Модель отзывов."""
    title = models.ForeignKey(
        Title,
        verbose_name='Произведение',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.PositiveSmallIntegerField(
        'Оценка',
        validators=[
            MinValueValidator(MINIMAL_SCORE),
            MaxValueValidator(MAXIMUM_SCORE)
        ]
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='reviews_authors'
    )

    class Meta:
        db_table = 'reviews'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ('author', 'title')


class Comment(BaseReviewModel):
    """Модель комментарием."""
    review = models.ForeignKey(
        Review,
        verbose_name='Отзыв',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments_authors'
    )

    class Meta:
        db_table = 'reviews_comments'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['id']
