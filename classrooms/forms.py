from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CunySignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def clean_email(self):
        email = self.cleaned_data['email']
        if not email.endswith('.cuny.edu'):
            raise forms.ValidationError("Email must end with .cuny.edu")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already in use")
        return email