from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    ModelSerializer, SlugRelatedField,
    CurrentUserDefault
)
from reviews.models import Review, Comment, Title


User = get_user_model()

class BaseSerializer(ModelSerializer):
    author = SlugRelatedField(
        queryset=User.objects.all(),
        default=CurrentUserDefault(),
        slug_field='username',
        read_only=True
    )

    class Meta:
        abstract = True
        read_only_fields = ('author', 'pub_date', 'id')


class ReviewSerializer(BaseSerializer):
    title = SlugRelatedField(
        queryset=Title.objects.all(),
        slug_field='name'
    )

    class Meta(BaseSerializer.Meta):
        model = Review
        fields = ('text', 'author', 'pub_date',
                  'title', 'score', 'id')

# Аналогично обновляем CommentSerializer
class CommentSerializer(BaseSerializer):

    class Meta(BaseSerializer.Meta):
        model = Comment
        fields = ('text', 'author', 'pub_date',
                  'review', 'id')
