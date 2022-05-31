import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class FormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_request_creates_post(self):
        posts_count = Post.objects.count()
        new_post_data = {
            'text': 'my new test post',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            new_post_data,
        )

        first_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(first_post.text, new_post_data['text'])
        self.assertEqual(first_post.group.id, new_post_data['group'])

    def test_edit_request_updates_post(self):
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.author,
        )

        update_data = {
            'text': 'updated post',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            update_data,
        )

        post.refresh_from_db()

        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, update_data['text'])

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_create_post_with_image_adds_image_to_db(self):
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image_name = 'test.gif'
        uploaded = SimpleUploadedFile(
            name=image_name, content=image, content_type='image/gif'
        )

        new_post_data = {
            'text': 'my new test post',
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            new_post_data,
        )

        first_post = Post.objects.first()
        self.assertEqual(first_post.image, 'posts/' + image_name)


class CommentsFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(text='Мой пост', author=cls.author)
        cls.comment = Comment.objects.create(
            text='Мой коммент', author=cls.author, post=cls.post
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_add_comment_request_creates_comment(self):
        comment_data = {
            'text': 'Мой коммент',
            'author': self.author,
            'post': self.post,
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            comment_data,
        )

        comment = Comment.objects.first()
        self.assertEqual(comment.text, comment_data['text'])
        self.assertEqual(comment.author, comment_data['author'])
        self.assertEqual(comment.post, comment_data['post'])
