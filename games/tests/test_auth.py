from django.test import TestCase
from django.contrib.auth.models import User
from games.models import GuessGame


class AuthTests(TestCase):
    def test_user_registration(self):
        response = self.client.post('/register/', {
            'username': 'newuser',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_password_mismatch(self):
        response = self.client.post('/register/', {
            'username': 'baduser',
            'password': 'StrongPassword123!',
            'password_confirm': 'MismatchPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_user_login_and_logout(self):
        User.objects.create_user(username='testuser', password='Password123!')
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

        logout_response = self.client.get('/logout/')
        self.assertEqual(logout_response.status_code, 302)
        self.assertRedirects(logout_response, '/login/')
