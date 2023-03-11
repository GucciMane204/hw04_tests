from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем тестового пользователя
        cls.user = User.objects.create_user(username='username')
        # Создаем тестовую группу
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        # Создаем тестовый пост
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, длина символов больше пятнадцати',
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group_post = {
            str(PostModelTest.group): 'Тестовая группа',
            str(PostModelTest.post):
            'Тестовый пост, длина символов больше пятнадцати'[:15],
        }
        for field, expected_value in group_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
