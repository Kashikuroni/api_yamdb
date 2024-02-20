from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxValueValidator, MinValueValidator
)

from django.db import models

User = get_user_model()


class Title(models.Model):
    class Meta:
        db_table = 'reviews_title'
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'


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
    title = models.ForeignKey(
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
