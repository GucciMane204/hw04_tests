from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
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
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post_authorized(self):
        """Проверка что при отправке валидной формы со страницы создания
        поста создаётся новая запись в базе данных;
        """
        # счетчик сейчас равен 1, т.к. мы создали всего 1 тестовый пост выше
        post_count = Post.objects.count()
        form_data = {
            'group': PostCreateFormTests.group.id,
            'text': 'Тестовый текст',
        }
        # делая post запрос автором мы как бы эмулируем нажатие
        # кнопки на сайте "создать пост" и форма как будто бы
        # заполняется соответсвующими значениями из словаря
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostCreateFormTests.user.username},
            ),
        )
        # Проверяем количество постов в базе
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверяем что пост действительно существует в базе
        self.assertTrue(
            Post.objects.filter(
                author=PostCreateFormTests.user,
                group=PostCreateFormTests.group,
                text='Тестовый текст',
            ).exists()
        )


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
        cls.form = PostForm(instance=cls.post)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostEditFormTests.user)

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
        modified_post = Post.objects.get(id=PostEditFormTests.post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(modified_post.text, 'Отредактированный пост')
        self.assertEqual(modified_post.group, PostEditFormTests.new_group)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostEditFormTests.post.id},
            ),
        )
