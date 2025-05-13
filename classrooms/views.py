import sys
from io import StringIO

from django.core.management import call_command
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
import random

from django.core.mail import send_mail
from .forms import CunySignupForm
from .models import EmailVerification

from classrooms.models import College, Building
from classrooms.utils.empty_rooms import get_available_rooms

@require_http_methods(["GET", "POST"])
def index(request):
    selected_college = request.GET.get('college', None)
    selected_buildings = request.GET.getlist('buildings', None)

    # Fetch colleges for the filter
    colleges = College.objects.all()

    # Fetch buildings based on the selected college
    if selected_college:
        buildings = Building.objects.filter(college__name=selected_college)
    else:
        buildings = Building.objects.all()

    # Fetch available rooms based on filters
    available_rooms = get_available_rooms(
        college=selected_college if selected_college else None,
        buildings=selected_buildings if selected_buildings else None
    )

    return render(request, 'index.html', {
        'colleges': colleges,
        'buildings': buildings,
        'available_rooms': available_rooms,
        'selected_college': selected_college,
        'selected_buildings': selected_buildings,
    })


def signup(request):
    if request.method == "POST":
        form = CunySignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until verified
            user.save()
            code = f"{random.randint(100000, 999999)}"
            EmailVerification.objects.create(user=user, code=code)
            send_mail(
                "Your Verification Code",
                f"Your code is: {code}",
                "noreply@yourdomain.com",
                [form.cleaned_data['email']],
            )
            messages.success(request, "Check your email for a verification code.")
            return redirect('verify_email')
    else:
        form = CunySignupForm()
    return render(request, 'signup.html', {'form': form})


def verify_email(request):
    if request.method == "POST":
        email = request.POST.get('email')
        code = request.POST.get('code')
        try:
            user = User.objects.get(email=email)
            verification = EmailVerification.objects.get(user=user)
            if verification.code == code:
                user.is_active = True
                user.save()
                verification.is_verified = True
                verification.save()
                messages.success(request, "Email verified! You can now log in.")
                return redirect('login')
            else:
                messages.error(request, "Invalid code.")
        except (User.DoesNotExist, EmailVerification.DoesNotExist):
            messages.error(request, "Invalid email or code.")
    return render(request, 'verify_email.html')

@require_http_methods(["GET", "POST"])
def login(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('index')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def import_data(request):
    if request.method == 'POST':
        try:
            # Capture command output
            out = StringIO()
            sys.stdout = out

            # Run the import command
            call_command('import_schedule', stdout=out)

            # Reset stdout
            sys.stdout = sys.__stdout__

            # Get command output
            result = out.getvalue()

            messages.success(request, f"Data import successful! {result}")
        except Exception as e:
            messages.error(request, f"Error importing data: {str(e)}")
        return redirect('import_data')

    return render(request, 'import_data.html')