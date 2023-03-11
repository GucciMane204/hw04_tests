from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user, text='Первый тестовый пост', group=cls.group
        )
        cls.post_count = Post.objects.count()
        cls.form_data = {
            'group': PostCreateFormTests.group.id,
            'text': 'Тестовый текст',
        }
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Проверка создания поста гостем и
        авторизованным пользователем.
        """
        clients = [self.guest_client, self.authorized_client]
        expected_post_count = [self.post_count, self.post_count + 1]
        for i in range(len(clients)):
            client = clients[i]
            count = expected_post_count[i]
            with self.subTest(client=client):
                response = client.post(
                    reverse('posts:post_create'), data=self.form_data
                )
                if client == self.guest_client:
                    self.assertRedirects(
                        response, '/auth/login/?next=/create/'
                    )
                    self.assertFalse(
                        Post.objects.filter(
                            author=self.user,
                            group=self.group,
                            text=self.form_data['text'],
                        ).exists()
                    )
                else:
                    self.assertRedirects(
                        response,
                        reverse(
                            'posts:profile', kwargs={'username': self.user}
                        ),
                    )
                    self.assertTrue(
                        Post.objects.filter(
                            author=self.user,
                            group=self.group,
                            text=self.form_data['text'],
                        ).exists()
                    )
                self.assertEqual(Post.objects.count(), count)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)


class PostEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Тестовая группа новая',
            slug='new-slug',
            description='Тестовое описание новой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user, text='Тестовое содержание поста', group=cls.group
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostEditFormTests.user)

    def test_edit_post_authorized(self):
        '''Тестируем редактирования поста авторизованным пользователем'''
        posts_count = Post.objects.count()
        form_data = {
            'group': PostEditFormTests.new_group.id,
            'text': 'Отредактированный пост',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostEditFormTests.post.id},
            ),
            data=form_data,
            follow=True,
        )
        PostEditFormTests.post.refresh_from_db()
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(PostEditFormTests.post.text, form_data['text'])
        self.assertEqual(
            PostEditFormTests.post.group, PostEditFormTests.new_group
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostEditFormTests.post.id},
            ),
        )
