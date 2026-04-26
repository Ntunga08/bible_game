from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AccountApiTests(APITestCase):
    def register_payload(self, **overrides):
        payload = {
            'username': 'paul',
            'email': 'paul@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'avatar': 'scroll',
        }
        payload.update(overrides)
        return payload

    def create_user(self, username='paul', password='StrongPass123!', **extra):
        return User.objects.create_user(
            username=username,
            password=password,
            email=extra.pop('email', f'{username}@example.com'),
            **extra,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_create_account_returns_user_and_tokens(self):
        response = self.client.post(
            reverse('auth-register'),
            self.register_payload(),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'paul')
        self.assertEqual(response.data['user']['email'], 'paul@example.com')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertTrue(User.objects.filter(username='paul').exists())

    def test_read_current_account_requires_authentication(self):
        response = self.client.get(reverse('auth-me'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_read_current_account(self):
        user = self.create_user()
        self.authenticate(user)

        response = self.client.get(reverse('auth-me'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(user.id))
        self.assertEqual(response.data['username'], user.username)

    def test_update_current_account(self):
        user = self.create_user()
        self.authenticate(user)

        response = self.client.patch(
            reverse('auth-me'),
            {'email': 'updated@example.com', 'avatar': 'crown'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, 'updated@example.com')
        self.assertEqual(user.avatar, 'crown')

    def test_delete_current_account(self):
        user = self.create_user()
        user_id = user.id
        self.authenticate(user)

        response = self.client.delete(reverse('auth-me'))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_register_rejects_missing_required_fields(self):
        response = self.client.post(
            reverse('auth-register'),
            {'email': 'missing@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('password', response.data)
        self.assertIn('password2', response.data)

    def test_register_rejects_password_mismatch(self):
        response = self.client.post(
            reverse('auth-register'),
            self.register_payload(password2='DifferentPass123!'),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_rejects_duplicate_username(self):
        self.create_user(username='paul')

        response = self.client.post(
            reverse('auth-register'),
            self.register_payload(email='another@example.com'),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_login_rejects_bad_credentials(self):
        self.create_user(username='paul', password='StrongPass123!')

        response = self.client.post(
            reverse('auth-login'),
            {'username': 'paul', 'password': 'wrong-password'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_invalid_account_url_returns_404(self):
        response = self.client.get('/api/v1/auth/users/not-a-real-id/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
