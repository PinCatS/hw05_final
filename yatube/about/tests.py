from http import HTTPStatus

from django.test import Client, TestCase


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_exists_at_desired_location(self):
        """Проверка доступности адресов /about/author/ и
        /about/tech/
        """
        urls = ('/about/author/', '/about/tech/')

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """Проверка шаблона для адресов /about/author/ и
        /about/tech/
        """
        url_template_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

        for url, template in url_template_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
