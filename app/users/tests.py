from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()


class AuthFlowTests(APITestCase):
    def test_register_returns_tokens(self):
        res = self.client.post(
            '/api/users/',
            {
                'name': 'Ada Lovelace',
                'email': 'ada@example.com',
                'password': 'hunter2',
            },
            format='json',
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertTrue(User.objects.filter(email='ada@example.com').exists())

    def test_login_by_email(self):
        User.objects.create_user(email='bob@example.com', password='secret')
        res = self.client.post(
            '/api/auth/login/',
            {'username': 'BoB@Example.com', 'password': 'secret'},
            format='json',
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIn('access', res.data)

    def test_login_by_phone(self):
        User.objects.create_user(phone='+1234567890', password='secret')
        res = self.client.post(
            '/api/auth/login/',
            {'username': '+1234567890', 'password': 'secret'},
            format='json',
        )
        self.assertEqual(res.status_code, 200, res.data)

    def test_login_bad_credentials(self):
        res = self.client.post(
            '/api/auth/login/',
            {'username': 'nobody@example.com', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(res.status_code, 401)

    def test_me_returns_profile(self):
        user = User.objects.create_user(email='c@example.com', password='pw')
        token = str(AccessToken.for_user(user))
        res = self.client.get(
            '/api/users/me/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['id'], str(user.pk))
        self.assertIn('is_staff', res.data)


class TokenUserIntegrationTests(APITestCase):
    """JWT issued here must resolve request.user to the real User row."""

    def test_access_token_from_this_issuer_yields_local_user(self):
        user = User.objects.create_user(email='d@example.com', password='pw')
        token = str(AccessToken.for_user(user))

        from users.views import me
        from rest_framework.test import APIRequestFactory

        request = APIRequestFactory().get('/api/users/me/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'

        from rest_framework_simplejwt.authentication import JWTAuthentication
        auth = JWTAuthentication()
        authenticated = auth.authenticate(request)
        self.assertIsNotNone(authenticated)
        resolved_user, _ = authenticated
        self.assertEqual(resolved_user.pk, user.pk)
