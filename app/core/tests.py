"""
Tests de l'authentification par les tokens du SSO (core/sso.py).
"""
import time
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase
from rest_framework.test import APIClient

from core.sso import SSO_ISSUER, SSOUser

SSO_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
FORGED_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
USER_ID = '8051a92c-bbd3-464e-9137-9e89dc02fd6e'


def make_token(key=SSO_KEY, **claims):
    payload = {
        'sub': USER_ID,
        'email': 'student@qavaa.com',
        'roles': ['student'],
        'iss': SSO_ISSUER,
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600,
        **claims,
    }
    return jwt.encode(payload, key, algorithm='RS256', headers={'kid': 'test-kid'})


class FakeSigningKey:
    key = SSO_KEY.public_key()


@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class SSOAuthenticationTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_valid_token_gives_access_to_cart(self, _):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token()}')
        res = self.client.get('/api/carts/my-cart/')
        self.assertEqual(res.status_code, 200)

    def test_token_in_cookie_is_accepted(self, _):
        self.client.cookies['access_token'] = make_token()
        res = self.client.get('/api/carts/my-cart/')
        self.assertEqual(res.status_code, 200)

    def test_forged_token_is_rejected(self, _):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token(key=FORGED_KEY)}')
        res = self.client.get('/api/carts/my-cart/')
        self.assertIn(res.status_code, (401, 403))

    def test_expired_token_is_rejected(self, _):
        token = make_token(exp=int(time.time()) - 10)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get('/api/carts/my-cart/')
        self.assertIn(res.status_code, (401, 403))

    def test_wrong_issuer_is_rejected(self, _):
        token = make_token(iss='https://evil.example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get('/api/carts/my-cart/')
        self.assertIn(res.status_code, (401, 403))

    def test_role_headers_are_ignored(self, _):
        """Les anciens en-têtes X-User-Id / X-User-Role ne donnent plus aucun droit."""
        res = self.client.post(
            '/api/tags/', {'name': 'hack'},
            HTTP_X_USER_ID=USER_ID, HTTP_X_USER_ROLE='admin',
        )
        self.assertIn(res.status_code, (401, 403))

    def test_student_cannot_create_tag(self, _):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token()}')
        res = self.client.post('/api/tags/', {'name': 'tag'})
        self.assertEqual(res.status_code, 403)


class SSOUserTests(TestCase):

    def test_roles_mapping(self):
        admin = SSOUser({'sub': USER_ID, 'roles': ['student', 'admin']})
        self.assertTrue(admin.is_admin)
        self.assertTrue(admin.is_instructor)
        self.assertEqual(admin.role, 'admin')

        instructor = SSOUser({'sub': USER_ID, 'roles': ['instructor']})
        self.assertFalse(instructor.is_admin)
        self.assertTrue(instructor.is_instructor)

        student = SSOUser({'sub': USER_ID, 'roles': ['student']})
        self.assertFalse(student.is_instructor)
        self.assertEqual(student.role, 'student')
