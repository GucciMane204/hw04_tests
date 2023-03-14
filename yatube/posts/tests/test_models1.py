from django.test import TestCase

from ..models import Comment, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем тестового пользователя
        cls.author = User.objects.create_user(username='author')
        # Создаем тестовую группу
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        # Создаем тестовый пост
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост длина символов больше пятнадцати',
            group=cls.group,
        )
        # Создаем комментарий
        cls.comment = Comment.objects.create(
            post=cls.post, author=cls.author, text='это комментарий'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group_post = {
            str(self.group): 'Тестовая группа',
            str(self.post): self.post.text[: 15],
            str(self.comment): 'это комментарий',
        }
        for field, expected_value in group_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)

    def test_field_labels_and_help_text(self):
        """
        Проверяем, что verbose_name и help_text совпадает с ожидаемым
        """
        post = self.post
        field_data = {
            'text': {
                'verbose_name': 'Текст поста',
                'help_text': 'Текст нового поста',
            },
            'group': {
                'verbose_name': 'Группа',
                'help_text': 'Группа, к которой будет относиться пост',
            },
            'image': {'verbose_name': 'Картинка', 'help_text': ''},
        }

        for field_name, expected_data in field_data.items():
            with self.subTest(field_name=field_name):
                field = post._meta.get_field(field_name)
                self.assertEqual(
                    field.verbose_name, expected_data['verbose_name']
                )
                self.assertEqual(field.help_text, expected_data['help_text'])
