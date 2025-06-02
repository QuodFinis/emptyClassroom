from django import forms
from django.utils import timezone

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CunySignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label="CUNY Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data['email'].lower()  # Normalize to lowercase
        # if not email.endswith('.cuny.edu'):
        #     raise forms.ValidationError("You must use a CUNY email address ending with .cuny.edu")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


from .models import RoomBooking

class RoomBookingForm(forms.ModelForm):
    class Meta:
        model = RoomBooking
        fields = ['booking_date', 'start_time', 'end_time']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract next_class_time from kwargs if provided
        self.next_class_time = kwargs.pop('next_class_time', None)
        super().__init__(*args, **kwargs)

        # Format time fields to not show seconds
        if 'start_time' in self.initial:
            self.initial['start_time'] = self.initial['start_time'].replace(second=0, microsecond=0)
        if 'end_time' in self.initial:
            self.initial['end_time'] = self.initial['end_time'].replace(second=0, microsecond=0)

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if not booking_date or not start_time or not end_time:
            return cleaned_data

        # Get current time
        now = timezone.localtime(timezone.now())

        # Validate booking date is today
        if booking_date != now.date():
            raise forms.ValidationError("Bookings can only be made for today.")

        # Convert datetime.time objects to datetime.datetime for comparison
        current_time = now.time()
        current_datetime = timezone.datetime.combine(now.date(), current_time)
        start_datetime = timezone.datetime.combine(now.date(), start_time)
        end_datetime = timezone.datetime.combine(now.date(), end_time)

        # Calculate 10 minutes from now
        ten_min_from_now = now + timezone.timedelta(minutes=10)

        # Validate start time is between now and 10 minutes from now
        if start_datetime < current_datetime:
            raise forms.ValidationError("Start time cannot be in the past.")
        if start_datetime > ten_min_from_now:
            raise forms.ValidationError("Start time must be within the next 10 minutes.")

        # Validate end time is no more than 1 hour after start time
        max_end_time = start_datetime + timezone.timedelta(hours=1)
        if end_datetime > max_end_time:
            raise forms.ValidationError("Booking duration cannot exceed 1 hour.")

        # Validate end time doesn't exceed next class time if provided
        if self.next_class_time:
            next_class_datetime = timezone.datetime.combine(now.date(), self.next_class_time)
            if end_datetime > next_class_datetime:
                raise forms.ValidationError(f"Booking must end before the next class starts at {self.next_class_time.strftime('%H:%M')}.")

        return cleaned_data
