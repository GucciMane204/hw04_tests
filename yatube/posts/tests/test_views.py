from django import forms
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slag",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            text="Тестовый пост", author=cls.user_author, group=cls.group
        )
        cls.post_1 = Post.objects.create(
            text='Пост без группы',
            author=cls.user_author,
        )
        cls.post_2 = Post.objects.create(
            text='Еще один пост', author=cls.user_author, group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostPagesTests.user_author)

    def test_pages_uses_correct_template(self):
        """Тестируем, что URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': PostPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user_author},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': PostPagesTests.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': PostPagesTests.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Тестируем список постов"""
        response = self.author_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj']
        for post in Post.objects.select_related('group', 'author'):
            self.assertIn(post, page_obj)

    def test_group_list_page_show_correct_context(self):
        """Тестируем список постов, отфильтрованный по группе"""
        response = self.author_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': PostPagesTests.group.slug}
            )
        )
        expected_posts = Post.objects.filter(group=PostPagesTests.group)
        posts_in_context = response.context['page_obj'].object_list
        self.assertQuerysetEqual(
            expected_posts, posts_in_context, transform=lambda x: x
        )

    def test_profile_page_show_correct_context(self):
        """Тестируем список постов, отфильтрованных по пользователю"""
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user_author},
            )
        )
        expected_posts = Post.objects.filter(author=PostPagesTests.post.author)
        posts_in_context = response.context['page_obj'].object_list
        self.assertQuerysetEqual(
            expected_posts, posts_in_context, transform=lambda x: x
        )

    def test_post_detail_page_show_correct_context(self):
        """Тестируем один пост, отфильтрованный по id"""
        response = self.guest_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': PostPagesTests.post.pk}
            )
        )
        post_context = response.context['post']
        self.assertEqual(post_context, PostPagesTests.post)

    def test_create_post_page_show_correct_context(self):
        """Тестируем шаблон создания поста"""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Тестируем шаблон редактирования поста"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        response = self.author_client.get(
            reverse(
                'posts:post_edit', kwargs={'post_id': PostPagesTests.post.pk}
            )
        )
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(
            response.context.get('form').initial.get('text'),
            PostPagesTests.post.text,
        )
        self.assertEqual(
            response.context.get('form').initial.get('group'),
            PostPagesTests.post.group.pk,
        )
        is_edit_context = response.context.get('is_edit')
        self.assertTrue(is_edit_context)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.posts = []
        cls.user_author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(
            settings.NUMBER_OF_POSTS + settings.NUMBER_OF_POSTS_PAGE_TWO
        ):
            cls.posts.append(
                Post(
                    author=cls.user_author,
                    text=f'Тест пост #{i+1}',
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.user_author)

    def test_first_page_contains_ten_records(self):
        '''Тестируем первую страницу'''
        pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user_author},
            ),
        ]
        for url in pages_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), settings.NUMBER_OF_POSTS
                )

    def test_second_page_contains_three_records(self):
        '''Тестируем вторую страницу'''
        pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user_author},
            ),
        ]
        for url in pages_names:
            with self.subTest(url=url):
                response = self.client.get(url + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.NUMBER_OF_POSTS_PAGE_TWO,
                )
