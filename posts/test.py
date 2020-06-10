from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import User, Post, Group, Follow

TEST_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='vasya',
                                             email='vasya@pypkin.com',
                                             password='12345678')
        self.post = Post.objects.create(text='Очень грустные тесты',
                                        author=self.user)
        self.client.force_login(self.user)

    def test_profile_view(self):
        response = self.client.get(reverse(
            'profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        # Авторизованный пользователь может опубликовать пост (new_post)
        response = self.client.get(reverse('new_post'))
        self.assertEqual(response.status_code, 200)

    def test_new_post_for_unauthorized_user(self):
        response = self.client.get(reverse('new_post'), follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_post_index(self):
        # После публикации поста новая запись появляется на главной
        # странице сайта (index)
        self.client.post(reverse('new_post'), {'text': self.post.text})
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.post)

    def test_post_profile(self):
        # После публикации поста новая запись появляется на
        # персональной странице пользователя (profile)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(response, self.post.text)

    def test_post_view(self):
        # После публикации поста новая запись появляется на отдельной
        # странице поста (post_view)
        self.client.force_login(self.user)
        response = self.client.get(reverse('post_view', kwargs={
            'username': self.user.username, 'post_id': self.post.id}))
        self.assertContains(response, self.post.text)

    @override_settings(CACHES=TEST_CACHE)
    def test_post_edit_index(self):
        # Авторизованный пользователь может отредактировать свой пост
        # и его содержимое изменится на главной странице сайта (index)
        self.client.force_login(self.user)
        self.edited_post = 'отредактированный пост'
        self.client.post(f'/{self.user.username}/{self.post.id}/edit/',
                         {'text': self.edited_post})
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.edited_post)

    @override_settings(CACHES=TEST_CACHE)
    def test_post_edit_profile(self):
        # Авторизованный пользователь может отредактировать свой пост и его
        # содержимое изменится на персональной странице пользователя (profile)
        self.client.force_login(self.user)
        self.edited_post = 'отредактированный пост'
        self.client.post(f'/{self.user.username}/{self.post.id}/edit/',
                         {'text': self.edited_post})
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(response, self.edited_post)

    @override_settings(CACHES=TEST_CACHE)
    def test_post_edit_post_view(self):
        # Авторизованный пользователь может отредактировать свой пост и его
        # содержимое изменится на отдельной странице поста (post_view)
        self.client.force_login(self.user)
        self.edited_post = 'отредактированный пост'
        self.client.post(f'/{self.user.username}/{self.post.id}/edit/',
                         {'text': self.edited_post}, follow=False)
        response = self.client.get(reverse('post_view', kwargs={
            'username': self.user.username, 'post_id': self.post.id}))
        self.assertContains(response, self.edited_post)


class FollowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='vasya',
                                              email='vasya@pypkin.com',
                                              password='12345')
        self.user2 = User.objects.create_user(username='nevasya',
                                              email='nevasya@pypkin.com',
                                              password='12345')
        self.user3 = User.objects.create_user(username='dalekonevasya',
                                              email='dalekonevasya@pypkin.com',
                                              password='12345')
        self.post = Post.objects.create(text='4 утра, а ничего не работает :(',
                                        author=self.user2)

    def test_follow(self):
        # Авторизованный пользователь может подписываться
        # на других пользователей
        self.client.force_login(self.user1)
        self.client.get(reverse('profile_follow',
                                kwargs={'username': self.user2.username}))
        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow(self):
        # Авторизованный пользователь может удалять
        # других пользователей из подписок.
        self.client.force_login(self.user1)
        self.client.get(reverse('profile_follow',
                                kwargs={'username': self.user2.username}))
        self.client.get(reverse('profile_unfollow',
                                kwargs={'username': self.user2.username}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_post(self):
        # Новая запись пользователя появляется в ленте тех,
        # кто на него подписан
        self.client.force_login(self.user1)
        self.client.get(reverse('profile_follow',
                                kwargs={'username': self.user2.username}))
        response = self.client.get(reverse('follow_index'))
        self.assertContains(response, self.post.text, status_code=200)
        self.client.force_login(self.user3)
        response = self.client.get(reverse('follow_index'))
        self.assertNotContains(response, self.post.text, status_code=200)


class CommentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='vasya',
                                             email='vasya@pypkin.com',
                                             password='12345')
        self.post = Post.objects.create(text='Какой-то пост',
                                        author=self.user)

    def test_add_comment_no_auth(self):
        # Неавторизированный пользователь не может комментировать посты.
        response = self.client.post(reverse('add_comment', kwargs={
            'username': self.user.username, 'post_id': self.post.id}),
                                    follow=True)
        self.assertRedirects(response,
                             '/auth/login/?next=%2Fvasya%2F1%2Fcomment%2F')

    def test_add_comment(self):
        # Авторизированный пользователь может комментировать посты.
        self.client.force_login(self.user)
        response = self.client.post(reverse('add_comment', kwargs={
            'username': self.user.username, 'post_id': self.post.id}),
                                    {'text': 'какой-то комментарий'},
                                    follow=True)
        self.assertContains(response, 'какой-то комментарий')


class ImageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='TestUser', email='mail@mail.ru', password='pwd111'
        )
        self.client.login(username='TestUser',
                          email='mail@mail.ru',
                          password='pwd111')
        self.group = Group.objects.create(title='TestGroup', slug='testgroup',
                                          description='TestDesc')
        with open('media/posts/test.jpg', 'rb') as fp:
            self.client.post('/new/', {'group': '1', 'text': 'Test post',
                                       'image': fp})

    def test_img_index(self):
        # При публикации поста с изображнием на главной
        # странице есть тег <img>
        response = self.client.get(reverse('index'))
        self.assertContains(response, '<img')

    def test_img_profile(self):
        # При публикации поста с изображнием на странице
        # профайла есть тег <img>
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(response, '<img')

    def test_img_view(self):
        # При публикации поста с изображнием на отдельной странице
        # поста есть тег <img>
        response = self.client.get('/TestUser/1/')
        self.assertContains(response, '<img')

    def test_img_group(self):
        # При публикации поста с изображнием на странице
        # группы есть тег <img>
        response = self.client.get('/group/testgroup/')
        self.assertContains(response, '<img')

    @override_settings(CACHES=TEST_CACHE)
    def test_NoImg(self):
        # Срабатывает защита от загрузки файлов не-графических форматов
        with open('media/posts/test_file', 'rb') as fp:
            self.client.post('/new/',
                             {'group': '1', 'text': 'Test post', 'image': fp})
        post = Post.objects.last()
        with self.assertRaises(ValueError):
            post.image.open()

    def tearDown(self):
        self.client.logout()
