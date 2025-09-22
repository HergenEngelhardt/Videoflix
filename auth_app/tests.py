"""
Unit tests for authentication functionality.

This module contains comprehensive tests for user authentication,
registration, login/logout, and JWT token management.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import CustomUser
from .authentication import CustomJWTAuthentication

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Test cases for CustomUser model."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_creation(self):
        """Test user creation with email as username."""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'test@example.com')
        self.assertFalse(user.is_active)  # Default is inactive
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_superuser_creation(self):
        """Test superuser creation."""
        user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_user_string_representation(self):
        """Test user string representation."""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_email_uniqueness(self):
        """Test email uniqueness constraint."""
        CustomUser.objects.create_user(**self.user_data)
        
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(**self.user_data)


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.client = APIClient()
    
    def test_user_registration(self):
        """Test user registration endpoint."""
        url = reverse('register')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email='test@example.com').exists())
        
        # Check that user is created but inactive
        user = CustomUser.objects.get(email='test@example.com')
        self.assertFalse(user.is_active)
    
    def test_user_login_valid_credentials(self):
        """Test user login with valid credentials."""
        # Create active user
        user = CustomUser.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        
        url = reverse('login')
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials."""
        url = reverse('login')
        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_login_inactive_user(self):
        """Test login attempt with inactive user."""
        # Create inactive user
        CustomUser.objects.create_user(**self.user_data)
        
        url = reverse('login')
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Test JWT token refresh functionality."""
        # Create active user and get tokens
        user = CustomUser.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        
        # Login to get refresh token
        login_url = reverse('login')
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Test token refresh
        refresh_url = reverse('token-refresh')
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_logout(self):
        """Test user logout functionality."""
        # Create active user and login
        user = CustomUser.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        
        # Login first
        self.client.force_authenticate(user=user)
        
        # Test logout
        url = reverse('logout')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_password_reset_request(self):
        """Test password reset request."""
        # Create active user
        user = CustomUser.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        
        url = reverse('password-reset')
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CustomJWTAuthenticationTest(TestCase):
    """Test cases for custom JWT authentication."""
    
    def setUp(self):
        """Set up test data."""
        self.auth = CustomJWTAuthentication()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
    
    def test_authentication_class_exists(self):
        """Test that custom authentication class exists."""
        self.assertIsNotNone(self.auth)
        self.assertTrue(hasattr(self.auth, 'authenticate'))
