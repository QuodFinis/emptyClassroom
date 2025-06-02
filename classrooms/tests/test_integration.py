from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class IntegrationTestCase(TestCase):
    """
    Integration tests for the login functionality with other parts of the application.
    """
    
    def setUp(self):
        """
        Set up test data before each test method is run.
        """
        self.client = Client()
        self.login_url = reverse('login')
        self.index_url = reverse('index')
        self.profile_url = reverse('profile')
        self.bookings_url = reverse('bookings')
        
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='securepassword123'
        )
    
    def test_login_required_for_profile(self):
        """
        Test that the profile page requires login.
        """
        # Try to access profile without logging in
        response = self.client.get(self.profile_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Login
        self.client.login(username='testuser', password='securepassword123')
        
        # Try to access profile again
        response = self.client.get(self.profile_url)
        
        # Check that the user can access the profile page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
    
    def test_login_required_for_bookings(self):
        """
        Test that the bookings page requires login.
        """
        # Try to access bookings without logging in
        response = self.client.get(self.bookings_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Login
        self.client.login(username='testuser', password='securepassword123')
        
        # Try to access bookings again
        response = self.client.get(self.bookings_url)
        
        # Check that the user can access the bookings page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings.html')
    
    def test_login_logout_flow(self):
        """
        Test the complete login-logout flow.
        """
        # Login
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'securepassword123'
        }, follow=True)
        
        # Check that the user is redirected to the index page
        self.assertRedirects(response, self.index_url)
        
        # Check that the user is authenticated
        self.assertTrue(response.context['user'].is_authenticated)
        
        # Logout
        response = self.client.post(reverse('logout'), follow=True)
        
        # Check that the user is redirected to the index page
        self.assertRedirects(response, self.index_url)
        
        # Check that the user is no longer authenticated
        self.assertFalse(response.context['user'].is_authenticated)