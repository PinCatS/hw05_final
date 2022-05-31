from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_pages_exist_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        pages_available_to_all_users = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author.username}/',
            f'/posts/{self.post.id}/',
        )

        for url in pages_available_to_all_users:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_returns_404(self):
        """Обращение к не существующей странице вернёт 404
        любому пользователю.
        """
        response = self.guest_client.get('/unknown-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexisting_page_uses_custom_404_template(self):
        response = self.guest_client.get('/unknown-page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_create_page_exist_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_redirect_unauth_user(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_page_available_for_authed_author(self):
        """Страница по адресу /posts/<post-id>/edit доступна
        для автора поста
        """
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_redirect_for_not_author(self):
        """Пользователь перенаправляется на /posts/<post-id>/
        при обращении к /posts/<post-id>/edit если он не автора поста
        """
        user = User.objects.create_user(username='not_author')
        not_author_logged_in = Client()
        not_author_logged_in.force_login(user)

        response = not_author_logged_in.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )

        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_edit_page_redirect_for_unauthed(self):
        """Анонимный пользователь перенаправляется на страницу логина
        при обращении к странице редактирования
        """
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/edit/'
        )

    def test_urls_uses_correct_template(self):
        url_template_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

        for url, template in url_template_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_commenting_unauth_user_redirected_to_logon_page(self):
        response = self.guest_client.post(
            f'/posts/{self.post.pk}/comment/',
            {'text': 'это коммент', 'post': self.post},
        )

        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )

    def test_add_comment_redirects_to_post_details(self):
        comment_data = {
            'text': 'Мой коммент',
            'author': self.author,
            'post': self.post,
        }

        response = self.authorized_client.post(
            f'/posts/{self.post.pk}/comment/',
            comment_data,
        )

        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_authed_user_can_access_followers_page(self):
        response = self.authorized_client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauthed_user_cant_access_followers_page(self):
        response = self.guest_client.get('/follow/')
        self.assertRedirects(response, '/auth/login/?next=/follow/')
