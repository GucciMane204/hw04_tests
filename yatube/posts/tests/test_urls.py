from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем тестового пользователя
        cls.user = User.objects.create_user(username='user')

        # Создаем тестового пользователя-автора
        cls.author = User.objects.create_user(username='Author')

        # Создаём неавторизованный клиент
        cls.guest_client = Client()

        # Создаём клиент для авторизации тестовым пользователем
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # Создаём клиент для авторизации тестовым пользователем-автором
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        # Создаем тестовую группу
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slag",
            description="Тестовое описание",
        )
        # Создаем тестовый пост
        cls.post = Post.objects.create(
            text="Тестовый пост", author=cls.author, group=cls.group
        )

        cls.URLS_ALL_STARS = {
            'INDEX': ('/', 'posts/index.html', HTTPStatus.OK),
            'GROUP': (
                f'/group/{cls.group.slug}/',
                'posts/group_list.html',
                HTTPStatus.OK,
            ),
            'PROFILE': (
                f'/profile/{cls.post.author.username}/',
                'posts/profile.html',
                HTTPStatus.OK,
            ),
            'POST_DETAIL': (
                f'/posts/{cls.post.pk}/',
                'posts/post_detail.html',
                HTTPStatus.OK,
            ),
            'UNEXISTING': (
                '/unexisting_page/',
                'core/404.html',
                HTTPStatus.NOT_FOUND,
            ),
            'POST_CREATE': (
                '/create/',
                'posts/create_post.html',
                HTTPStatus.OK,
            ),
            'POST_EDIT': (
                f'/posts/{cls.post.pk}/edit/',
                'posts/create_post.html',
                HTTPStatus.OK,
            ),
            'POST_COMMENT': (
                f'/posts/{cls.post.pk}/comment/',
                'posts/post_detail.html',
                HTTPStatus.OK,
            ),
            'FOLLOW_INDEX': (
                '/follow/',
                'posts/follow.html',
                HTTPStatus.OK,
            ),
            'FOLLOW': (
                f'/profile/{cls.post.author.username}/follow/',
                'posts/profile.html',
                HTTPStatus.OK,
            ),
            'UNFOLLOW': (
                f'/profile/{cls.post.author.username}/unfollow/',
                'posts/profile.html',
                HTTPStatus.OK,
            ),
        }

        # Доступные адресы для гостя
        cls.URLS_GUEST_ALLOWED = {
            'INDEX': cls.URLS_ALL_STARS['INDEX'],
            'GROUP': cls.URLS_ALL_STARS['GROUP'],
            'PROFILE': cls.URLS_ALL_STARS['PROFILE'],
            'POST_DETAIL': cls.URLS_ALL_STARS['POST_DETAIL'],
            'UNEXISTING': cls.URLS_ALL_STARS['UNEXISTING'],
        }

        # Доступные адресы для авторизованного пользователя
        cls.URLS_AUTHORIZED_ALLOWED = {
            **cls.URLS_GUEST_ALLOWED,
            'POST_CREATE': cls.URLS_ALL_STARS['POST_CREATE'],
            'FOLLOW_INDEX': cls.URLS_ALL_STARS['FOLLOW_INDEX'],
        }

        # Доступные адресы для автора
        cls.URLS_AUTHOR_ALLOWED = {
            **cls.URLS_AUTHORIZED_ALLOWED,
            'POST_EDIT': cls.URLS_ALL_STARS['POST_EDIT'],
        }

        # Адресы, которые редиректят автора
        # на страницу деталей поста
        cls.URLS_AUTHOR_REDIRECT_POST_DETAIL = {
            'POST_COMMENT': cls.URLS_ALL_STARS['POST_COMMENT'],
        }

        # Адресы, которые редиректят авторизованного
        # на страницу деталей поста
        cls.URLS_AUTHORIZED_REDIRECT_POST_DETAIL = {
            **cls.URLS_AUTHOR_REDIRECT_POST_DETAIL,
            'POST_EDIT': cls.URLS_ALL_STARS['POST_EDIT'],
        }

        # Адресы, которые редиректят авторизованного
        # на страницу профиля пользователя
        cls.URLS_AUTHORIZED_REDIRECT_PROFILE = {
            'FOLLOW': cls.URLS_ALL_STARS['FOLLOW'],
            'UNFOLLOW': cls.URLS_ALL_STARS['UNFOLLOW'],
        }

        # Адресы, которые редиректят гостя на авторизацию
        cls.URLS_GUEST_REDIRECT_LOGIN = {
            **cls.URLS_AUTHORIZED_REDIRECT_POST_DETAIL,
            **cls.URLS_AUTHORIZED_REDIRECT_PROFILE,
            'POST_CREATE': cls.URLS_ALL_STARS['POST_CREATE'],
            'FOLLOW_INDEX': cls.URLS_ALL_STARS['FOLLOW_INDEX'],
        }

    def test_available_urls_for_guest_client(self):
        """Проверяем доступные адреса для гостевого пользователя."""
        for url, template, status in self.URLS_GUEST_ALLOWED.values():
            with self.subTest(url=url, template=template, status=status):
                cache.clear()
                response = self.guest_client.get(url, follow=True)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, status)

    def test_redirects_for_guest_client_to_login(self):
        """Проверяем редиректы для гостевого пользователя на авторизацию."""
        for url, _, _ in self.URLS_GUEST_REDIRECT_LOGIN.values():
            with self.subTest(url=url):
                cache.clear()
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, '/auth/login/?next=' + url)

    def test_available_urls_for_authorized_client(self):
        """Проверяем доступные адреса для авторизованного пользователя."""
        for url, template, status in self.URLS_AUTHORIZED_ALLOWED.values():
            with self.subTest(url=url, template=template, status=status):
                cache.clear()
                response = self.authorized_client.get(url, follow=True)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, status)

    def test_redirects_for_authorized_client_to_post_detail(self):
        """Проверяем редиректы для авторизованного пользователя
        на страницу поста.
        """
        for url, _, _ in self.URLS_AUTHORIZED_REDIRECT_POST_DETAIL.values():
            with self.subTest(url=url):
                cache.clear()
                response = self.authorized_client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    self.URLS_ALL_STARS['POST_DETAIL'][settings.POST_URL],
                )

    def test_redirects_for_authorized_client_to_post_profile(self):
        """Проверяем редиректы для авторизованного пользователя
        на страницу профиля.
        """
        for url, _, _ in self.URLS_AUTHORIZED_REDIRECT_PROFILE.values():
            with self.subTest(url=url):
                cache.clear()
                response = self.authorized_client.get(url, follow=True)
                self.assertRedirects(
                    response, self.URLS_ALL_STARS['PROFILE'][settings.POST_URL]
                )

    def test_available_urls_for_author_client(self):
        """Проверяем доступные адреса для автора."""
        for url, template, status in self.URLS_AUTHOR_ALLOWED.values():
            with self.subTest(url=url, template=template, status=status):
                cache.clear()
                response = self.author_client.get(url, follow=True)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, status)

    def test_redirects_for_authorized_client_to_post_detail(self):
        """Проверяем редиректы для автора на страницу поста."""
        for url, _, _ in self.URLS_AUTHOR_REDIRECT_POST_DETAIL.values():
            with self.subTest(url=url):
                cache.clear()
                response = self.author_client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    self.URLS_ALL_STARS['POST_DETAIL'][settings.POST_URL],
                )

    def test_redirects_for_authorized_client_to_post_profile(self):
        """Проверяем редиректы для автора на страницу профиля."""
        for url, _, _ in self.URLS_AUTHORIZED_REDIRECT_PROFILE.values():
            with self.subTest(url=url):
                cache.clear()
                response = self.author_client.get(url, follow=True)
                self.assertRedirects(
                    response, self.URLS_ALL_STARS['PROFILE'][settings.POST_URL]
                )
