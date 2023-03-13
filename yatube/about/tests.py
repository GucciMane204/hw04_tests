from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.URLS = {
            '/about/author/': ('about/author.html', HTTPStatus.OK),
            '/about/tech/': ('about/tech.html', HTTPStatus.OK),
        }

    def test_static_urls(self):
        """Проверка доступности и шаблонов статичных адресов."""
        for address, (template, status_code) in self.URLS.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)
                self.assertTemplateUsed(response, template)
