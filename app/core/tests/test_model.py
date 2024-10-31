"""tests for models"""

from django.test import TestCase
from django.contrib.auth import get_user_model


def create_user(email='user@example.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTest(TestCase):
    """Test case"""

    def test_create_user(self):
        """test creating a user"""
        email = 'test@example.com'
        password = 'password123'
        user = create_user(email, password)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.email, email)

    def test_create_super_user(self):
        """test if creating superuser correct"""
        user = get_user_model().objects.create_superuser(
            'test1@examle.com',
            'test123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_new_user_with_email_raises_error(self):
        """Test if creating user without email is an error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')
