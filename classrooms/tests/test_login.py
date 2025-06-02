from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core import mail

class LoginTestCase(TestCase):
    """
    Test case for the login functionality.
    """
    
    def setUp(self):
        """
        Set up test data before each test method is run.
        """
        self.client = Client()
        self.login_url = reverse('login')
        self.index_url = reverse('index')
        
        # Create an active user
        self.active_user = User.objects.create_user(
            username='activeuser',
            email='activeuser@example.com',
            password='securepassword123'
        )
        
        # Create an inactive user (for email verification testing)
        self.inactive_user = User.objects.create_user(
            username='inactiveuser',
            email='inactiveuser@example.com',
            password='securepassword123',
            is_active=False
        )
    
    def test_login_page_loads_correctly(self):
        """
        Test that the login page loads correctly with a 200 status code.
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertIsInstance(response.context['form'], AuthenticationForm)
    
    def test_login_successful(self):
        """
        Test that a user can successfully log in with valid credentials.
        """
        response = self.client.post(self.login_url, {
            'username': 'activeuser',
            'password': 'securepassword123'
        }, follow=True)
        
        # Check that the user is redirected to the index page
        self.assertRedirects(response, self.index_url)
        
        # Check that the user is authenticated
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'activeuser')
    
    def test_login_with_invalid_credentials(self):
        """
        Test that login fails with invalid credentials.
        """
        response = self.client.post(self.login_url, {
            'username': 'activeuser',
            'password': 'wrongpassword'
        })
        
        # Check that the user stays on the login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        
        # Check that the form has errors
        self.assertTrue(response.context['form'].errors)
        
        # Check that the user is not authenticated
        self.assertFalse(response.context['user'].is_authenticated)
    
    def test_login_with_inactive_user(self):
        """
        Test that login with an inactive user redirects to resend verification.
        """
        response = self.client.post(self.login_url, {
            'username': 'inactiveuser',
            'password': 'securepassword123'
        }, follow=True)
        
        # Check that the user is redirected to the resend verification page
        self.assertRedirects(response, reverse('resend_verification'))
        
        # Check that the email is stored in the session
        self.assertEqual(self.client.session['resend_email'], 'inactiveuser@example.com')
    
    def test_already_authenticated_user_redirected(self):
        """
        Test that an already authenticated user is redirected to the index page.
        """
        # First login to authenticate
        self.client.login(username='activeuser', password='securepassword123')
        
        # Then try to access the login page
        response = self.client.get(self.login_url)
        
        # Check that the user is redirected to the index page
        self.assertRedirects(response, self.index_url)
    
    def test_csrf_token_present(self):
        """
        Test that the CSRF token is present in the login form.
        """
        response = self.client.get(self.login_url)
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_login_form_validation(self):
        """
        Test form validation for empty fields.
        """
        # Test with empty username
        response = self.client.post(self.login_url, {
            'username': '',
            'password': 'securepassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        
        # Test with empty password
        response = self.client.post(self.login_url, {
            'username': 'activeuser',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        
        # Test with both fields empty
        response = self.client.post(self.login_url, {
            'username': '',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
    
    def test_login_maintains_session(self):
        """
        Test that login creates and maintains a session.
        """
        response = self.client.post(self.login_url, {
            'username': 'activeuser',
            'password': 'securepassword123'
        }, follow=True)
        
        # Check that a session exists
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.active_user.id)