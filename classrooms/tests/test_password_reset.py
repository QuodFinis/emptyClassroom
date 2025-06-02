from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail

class PasswordResetTestCase(TestCase):
    """
    Test case for the password reset functionality.
    """
    
    def setUp(self):
        """
        Set up test data before each test method is run.
        """
        self.client = Client()
        self.forgot_password_url = reverse('password_reset')
        self.login_url = reverse('login')
        
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='securepassword123'
        )
    
    def test_forgot_password_page_loads(self):
        """
        Test that the forgot password page loads correctly.
        """
        response = self.client.get(self.forgot_password_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forgot_password.html')
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_forgot_password_valid_email(self):
        """
        Test that submitting a valid email sends a password reset email.
        """
        response = self.client.post(self.forgot_password_url, {
            'email': 'testuser@example.com'
        }, follow=True)
        
        # Check that the user is redirected to the login page
        self.assertRedirects(response, self.login_url)
        
        # Check that a success message is shown
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Password reset email sent.")
        
        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['testuser@example.com'])
        self.assertEqual(mail.outbox[0].subject, 'Reset your password')
    
    def test_forgot_password_invalid_email(self):
        """
        Test that submitting an invalid email shows an error message.
        """
        response = self.client.post(self.forgot_password_url, {
            'email': 'nonexistent@example.com'
        }, follow=True)
        
        # Check that the user stays on the forgot password page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forgot_password.html')
        
        # Check that an error message is shown
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "No account found with this email.")
        
        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)