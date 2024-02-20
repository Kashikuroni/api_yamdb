from django.db import models

class Review(models.Model):
  class Meta:
    db_tbale = 'reviews_review'
    verbose_name = 'Отзыв'
    verbose_name_plural = 'Отзывы'

  def __str__(self) -> str:
    return super().__str__()


class Comment(models.Model):
  class Meta:
    db_tbale = 'reviews_comment'
    verbose_name = 'Комментарий'
    verbose_name_plural = 'Комментарии'

  def __str__(self) -> str:
    return super().__str__()


class Rating(models.Model):
  class Meta:
    db_tbale = 'reviews_rating'
    verbose_name = 'Рейтинг'
    verbose_name_plural = 'Рейтинги'

  def __str__(self) -> str:
    return super().__str__()
