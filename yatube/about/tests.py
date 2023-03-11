from http import HTTPStatus
from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_exists_at_desired_location(self):
        """Проверка доступности статичных адресов."""
        status_code_url_names = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for address, status_code in status_code_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_url_uses_correct_template(self):
        """Проверка шаблонов статичных адресов."""
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
