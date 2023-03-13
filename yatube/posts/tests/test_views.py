import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.guest_client = Client()
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slug",
            description="Тестовое описание",
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=cls.author,
            group=cls.group,
            image=uploaded
        )
        cls.post_1 = Post.objects.create(
            text='Пост без группы',
            author=cls.author,
            image=uploaded
        )
        cls.post_2 = Post.objects.create(
            text='Еще один пост',
            author=cls.author,
            group=cls.group,
            image=uploaded
        )
        cls.post_index = reverse('posts:index')
        cls.post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostPagesTests.post.pk},
        )
        cls.templates_guest = (
            (
                reverse('posts:index'),
                'posts/index.html',
                Post.objects.select_related('group', 'author'),
            ),
            (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug},
                ),
                'posts/group_list.html',
                Post.objects.filter(group=PostPagesTests.group),
            ),
            (
                reverse(
                    'posts:profile',
                    kwargs={'username': PostPagesTests.author},
                ),
                'posts/profile.html',
                Post.objects.filter(author=PostPagesTests.post.author),
            ),
            (
                cls.post_detail,
                'posts/post_detail.html',
                Post.objects.filter(pk=PostPagesTests.post.pk),
            ),
        )
        cls.templates_author = (
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.pk},
                ),
                'posts/create_post.html',
            ),
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_views_guest_client(self):
        """Тестируем адреса для гостя"""
        for name, template, filt in self.templates_guest:
            with self.subTest(name=name, template=template, filt=filt):
                response = self.guest_client.get(name)
                self.assertQuerysetEqual(
                    response.context['page_obj']
                    if 'page_obj' in response.context
                    else [response.context['post']],
                    filt,
                    transform=lambda x: x,
                )

    def test_views_author_client(self):
        """Тестируем адреса для автора"""
        for name, template in self.templates_author:
            for value, expected in self.form_fields.items():
                with self.subTest(name=name, template=template):
                    response = self.author_client.get(name)
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)
                if 'edit' in name:
                    self.assertEqual(
                        response.context.get('form').initial.get('text'),
                        self.post.text,
                    )
                    self.assertEqual(
                        response.context.get('form').initial.get('group'),
                        self.post.group.pk,
                    )
                    self.assertEqual(
                        response.context.get('form').initial.get('image'),
                        self.post.image,
                    )
                    is_edit_context = response.context.get('is_edit')
                    self.assertTrue(is_edit_context)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.posts = []
        cls.author = User.objects.create_user(username='Author')
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
                    author=cls.author,
                    text=f'Тест пост #{i+1}',
                    group=cls.group,
                )
            )
        cls.pages = (
            (
                reverse('posts:index'),
                (settings.NUMBER_OF_POSTS, settings.NUMBER_OF_POSTS_PAGE_TWO),
            ),
            (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug},
                ),
                (settings.NUMBER_OF_POSTS, settings.NUMBER_OF_POSTS_PAGE_TWO),
            ),
            (
                reverse(
                    'posts:profile',
                    kwargs={'username': PaginatorViewsTest.author},
                ),
                (settings.NUMBER_OF_POSTS, settings.NUMBER_OF_POSTS_PAGE_TWO),
            ),
        )

    def test_pagination(self):
        '''Тестируем паджинатор'''
        for url, page_count in self.pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), page_count[0]
                )
                if page_count[1]:
                    response = self.client.get(url + '?page=2')
                    self.assertEqual(
                        len(response.context['page_obj']), page_count[1]
                    )
