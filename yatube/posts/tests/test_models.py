from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
        )

    def test_post_str_returns_trunc_text(self):
        post = self.post
        act = str(post)
        self.assertEqual(act, post.text[:15])

    def test_post_verbose_name(self):
        post = self.post
        field_verboses = {
            'text': 'текст поста',
            'pub_date': 'дата публикации',
            'author': 'автор',
            'group': 'сообщество',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_post_help_text(self):
        post = self.post
        field_help_text = {
            'text': 'текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )


class GroupModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def test_group_str_returns_title(self):
        group = self.group
        act = str(group)
        self.assertEqual(act, group.title)

    def test_group_verbose_name(self):
        group = self.group
        field_verbose = {
            'title': 'заголовок сообщества',
            'description': 'описание сообщества',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value
                )

    def test_group_help_text(self):
        group = self.group
        field_help_text = {
            'title': 'макс. длина 200 символов',
            'slug': 'уникальное поле',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value
                )
