from django.db import models

class TestUser(models.Model):
    pass

class Title(models.Model):
    pass

class BaseReviewModel(models.Model):
    text = models.CharField('Текст', max_length=1024)
    author = models.ForeignKey(TestUser, verbose_name='Автор', on_delete=models.CASCADE)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f'{self.author} - {self.text}'


class Review(BaseReviewModel):
    title = models.ForeignKey(Title, verbose_name='Произведение', on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField('Оценка')

    class Meta:
        db_table = 'reviews_review'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class Comment(BaseReviewModel):
    review = models.ForeignKey(Review, verbose_name='Отзыв', on_delete=models.CASCADE)

    class Meta:
        db_table = 'reviews_comment'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
