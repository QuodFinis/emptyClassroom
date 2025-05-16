from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CunySignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label="CUNY Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data['email'].lower()  # Normalize to lowercase
        if not email.endswith('.cuny.edu'):
            raise forms.ValidationError("You must use a CUNY email address ending with .cuny.edu")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user