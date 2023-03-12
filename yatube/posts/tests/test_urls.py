from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user_author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slug",
            description="Тестовое описание"
        )
        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=cls.user_author,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user_author)

    def test_url_exists_at_desired_location(self):
        """Проверка гостевым клиентом доступности страниц без авторизации"""
        status_code_url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.post.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})]
        responses = dict.fromkeys(
            [self.guest_client.get(page) for page in status_code_url_names],
            HTTPStatus.OK)
        for response, code in responses.items():
            with self.subTest(field=response):
                self.assertEqual(response.status_code, code)

    def test_post_edit_url_exist_on_authorized(self):
        """Проверка доступности страницы /post/<int:post_id>/edit/'
        'автору поста"""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_authorized_on_post_detail(self):
        """Проверка, что страница /post/<int:post_id>/edit/ перенаправит'
        'авторизованного пользователя (не автора) на страницу поста"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            follow=True)
        self.assertRedirects(response, f'/posts/{PostURLTests.post.pk}/')

    def test_post_edit_url_redirect_guest_on_login(self):
        """Страница /post/<int:post_id>/edit/ перенаправит неавторизованного'
        'пользователя на авторизацию"""
        response = self.guest_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}), follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostURLTests.post.pk}/edit/'
        )

    def test_post_create_url_redirect_guest_on_login(self):
        """Страница /create/ перенаправит неавторизованного'
        'пользователя на авторизацию"""
        response = self.guest_client.get(
            reverse('posts:post_create'), follow=True)
        self.assertRedirects(
            response, reverse('users:login') + '?next=/create/'
        )

    def test_post_create_url_exist_on_authorized(self):
        """Проверка доступности страницы /create/'
        'для авторизованного пользователя"""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_for_un_existing_page(self):
        """Проверка недоступности несуществующей страницы"""
        response = self.guest_client.get('/un_existing_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """Проверка используемых шаблонов для каждого адреса"""
        templates_url_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.post.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post.author}):
                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}):
                'posts/create_post.html'}
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
