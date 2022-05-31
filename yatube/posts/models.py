from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        'заголовок сообщества',
        max_length=200,
        help_text='макс. длина 200 символов',
    )
    slug = models.SlugField(unique=True, help_text='уникальное поле')
    description = models.TextField('описание сообщества')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('текст поста', help_text='текст нового поста')
    pub_date = models.DateTimeField('дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='сообщество',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField('картинка', upload_to='posts/', blank=True)

    class Meta:
        ordering = ('-pub_date', 'author')

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    text = models.TextField('текст комментария')
    created = models.DateTimeField(
        'дата и время публикации', auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='автор',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='пост',
    )

    class Meta:
        ordering = ('-created', 'author')

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='автор',
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик',
    )
