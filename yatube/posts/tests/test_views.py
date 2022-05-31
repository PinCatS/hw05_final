import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.author_other = User.objects.create_user(username='author_other')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тестовый пост', author=cls.author, group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        names_templates_pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            ): 'posts/create_post.html',
        }

        for reverse_name, template in names_templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))

        first_article = response.context['page_obj'].object_list[0]
        self.assertEqual(first_article.text, 'Тестовый пост')
        self.assertEqual(first_article.group, self.group)
        self.assertEqual(first_article.author, self.author)

    def test_group_posts_page_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        page_objects = response.context['page_obj']

        self.assertGreater(len(page_objects), 0)
        for article in page_objects:
            self.assertEqual(article.group, self.group)
        self.assertEqual(response.context['group'], self.group)

    def test_profile_page_shows_only_author_articles(self):
        Post.objects.create(text='Тестовый пост 2', author=self.author_other)
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username},
            )
        )
        page_objects = response.context['page_obj']

        self.assertGreater(len(page_objects), 0)
        for article in page_objects:
            self.assertEqual(article.author, self.author)

    def test_post_detail_page_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            )
        )
        self.assertEqual(response.context['post'], self.post)

    def test_create_post_page_shows_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        response = self.authorized_client.get(reverse('posts:post_create'))

        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        for value, expected in form_fields.items():
            form_field = form.fields.get(value)
            self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['is_edit'], False)

    def test_edit_post_page_shows_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            )
        )

        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['is_edit'], True)
        self.assertEqual(response.context['post_id'], self.post.id)

    def test_create_post_with_group_are_shown_on_three_pages(self):
        post_group = Group.objects.create(
            title='Тестовая группа 3',
            slug='test-slug-3',
            description='Тестовое описание 3',
        )
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            {
                'text': 'my new test post',
                'group': post_group.id,
            },
        )

        # get index page
        response_index = self.authorized_client.get(reverse('posts:index'))

        # post should be there
        first_post_index = response_index.context['page_obj'].object_list[0]
        self.assertEqual(first_post_index.group, post_group)

        # get profile for author
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username},
            )
        )

        # post should be there
        first_post = response.context['page_obj'].object_list[0]
        self.assertEqual(first_post.group, post_group)

        # get group's posts for group
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': post_group.slug},
            )
        )

        # post should be there
        first_post = response.context['page_obj'].object_list[0]
        self.assertEqual(first_post.group, post_group)

    def test_create_post_with_group_are_not_in_another_groups(self):
        new_group = Group.objects.create(
            title='Тестовая группа 3',
            slug='test-slug-3',
            description='Тестовое описание 3',
        )
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            {
                'text': 'my new test post',
                'group': new_group.id,
            },
        )

        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            )
        )

        for post in response.context['page_obj']:
            self.assertNotEqual(post.group, new_group)


class ViewsPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.EXPECTED_ON_SECOND_PAGE = 3
        cls.posts = [
            Post.objects.create(
                text='Тестовый пост', author=cls.author, group=cls.group
            )
            for _ in range(
                settings.POSTS_PER_PAGE + cls.EXPECTED_ON_SECOND_PAGE
            )
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_paginator_works(self):
        page_names = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username},
            ),
        )

        for page_name in page_names:
            with self.subTest(page_name=page_name):
                response = self.authorized_client.get(page_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE,
                )
                response = self.authorized_client.get(page_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.EXPECTED_ON_SECOND_PAGE,
                )


class PostImagesTest(TestCase):
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
        cache.clear()

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_post_with_image_is_passed_to_context(self):
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
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.author,
            image=uploaded,
            group=self.group,
        )

        path_names = (
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username},
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ),
        )

        for name in path_names:
            response = self.client.get(name)
            first_article = response.context['page_obj'].object_list[0]
            self.assertEqual(first_article.image, 'posts/' + image_name)

        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post.id},
            )
        )
        self.assertEqual(response.context['post'].image, 'posts/' + image_name)


class CommentsViewTest(TestCase):
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

    def test_added_comment_shown_on_page_details(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            )
        )

        first_comment = response.context['comments'][0]
        self.assertEqual(first_comment, self.comment)


class CachingViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(text='Мой пост', author=cls.author)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_posts_cached_on_index_page(self):
        # cache index
        self.authorized_client.get(reverse('posts:index'))

        # check that there is no any records anymore in db
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        # check that response.content still has records
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(self.post.text, response.content.decode())
        self.assertIn(self.post.author.username, response.content.decode())

        cache.clear()

        # check that no we don't have any records in response too
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotIn(self.post, response.context['page_obj'])


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.author_post = Post.objects.create(
            text='Пост автора', author=cls.author
        )
        cls.user_post = Post.objects.create(text='Пост юзера', author=cls.user)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_user_sees_author_posts_if_follows(self):
        Follow.objects.create(user=self.user, author=self.author)

        response = self.authorized_user.get(reverse('posts:follow_index'))
        first_post = response.context['page_obj'].object_list[0]
        self.assertEqual(first_post, self.author_post)

    def test_user_dont_see_author_posts_if_dont_follows(self):
        Follow.objects.create(user=self.user, author=self.author)

        response = self.authorized_author.get(reverse('posts:follow_index'))
        following_posts_count = len(response.context['page_obj'].object_list)
        self.assertEqual(following_posts_count, 0)

    def test_user_can_follow_author(self):
        self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username},
            )
        )

        response = self.authorized_user.get(reverse('posts:follow_index'))
        first_post = response.context['page_obj'].object_list[0]
        self.assertEqual(first_post, self.author_post)

    def test_user_can_unfollow_author(self):
        Follow.objects.create(user=self.user, author=self.author)
        self.authorized_user.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username},
            )
        )

        response = self.authorized_user.get(reverse('posts:follow_index'))
        following_posts_count = len(response.context['page_obj'].object_list)
        self.assertEqual(following_posts_count, 0)

    def test_user_redirected_to_author_page_after_follow(self):
        response = self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username},
            )
        )

        self.assertRedirects(response, f'/profile/{self.author.username}/')

    def test_user_redirected_to_author_page_after_unfollow(self):
        response = self.authorized_user.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username},
            )
        )

        self.assertRedirects(response, f'/profile/{self.author.username}/')
