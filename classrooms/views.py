import sys
from io import StringIO

from django.contrib.sites.shortcuts import get_current_site
from django.core.management import call_command
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login, get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required

from emptyClassroom.settings import DEFAULT_FROM_EMAIL
from .forms import CunySignupForm
from classrooms.models import College, Building, Room
from classrooms.utils.empty_rooms import get_available_rooms
from classrooms.utils.all_rooms import get_all_rooms



User = get_user_model()
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

@require_http_methods(["GET", "POST"])
def signup(request):
    if request.method == "POST":
        print("POST data:", request.POST)  # Debug what's being submitted
        form = CunySignupForm(request.POST)
        if form.is_valid():
            print("Form cleaned data:", form.cleaned_data)  # Debug cleaned data
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            print("User created:", user.username, user.email)  # Debug created user

            # Send verification email
            send_verification_email(request, user)

            res = messages.success(request, "Please check your email to verify your account.")
            print(res)  # Debugging
            return redirect('login')
    else:
        form = CunySignupForm()
    return render(request, 'signup.html', {'form': form})


@require_http_methods(["GET", "POST"])
def send_verification_email(request, user):
    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        current_site = get_current_site(request)
        mail_subject = 'Activate your account'

        context = {
            'user': user,
            'domain': current_site.domain,
            'uid': uid,
            'token': token,
            'protocol': 'https' if request.is_secure() else 'http',
        }

        text_message = render_to_string('verification_email.txt', context)
        html_message = render_to_string('verification_email.html', context)

        email_sent = send_mail(
            mail_subject,
            text_message,
            DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        if email_sent == 1:
            print(f"Verification email sent to {user.email}")
        else:
            print(f"Failed to send email to {user.email}")

    except Exception as e:
        print(f"Error sending verification email: {str(e)}")


def verify_email(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your email has been verified! You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "The verification link was invalid or has expired.")
        return redirect('signup')


@require_http_methods(["GET", "POST"])
def resend_verification(request):
    email = request.session.pop('resend_email', None)

    if request.method == "POST":
        email = request.POST.get('email')

    if email:
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                send_verification_email(request, user)  # Same token gets re-used
                messages.info(request, f"A verification email has been sent to {email}.")
            else:
                messages.info(request, "Account is already active. Please log in.")
                return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")

    return render(request, 'resend_verification.html', {'email': email})

@require_http_methods(["GET", "POST"])
def login(request):
    if request.user.is_authenticated:
        return redirect('index')

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('index')
        else:
            # Check if the error is due to inactive user
            username = form.cleaned_data.get('username')
            if username:
                try:
                    user = User.objects.get(username=username)
                    if not user.is_active:
                        # User exists but isn't active due to email verification
                        request.session['resend_email'] = user.email
                        return redirect('resend_verification')
                except User.DoesNotExist:
                    pass

    return render(request, 'login.html', {'form': form})


def send_password_reset_email(request, user):
    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        current_site = get_current_site(request)
        mail_subject = 'Reset your password'

        context = {
            'user': user,
            'domain': current_site.domain,
            'uid': uid,
            'token': token,
            'protocol': 'https' if request.is_secure() else 'http',
        }

        text_message = render_to_string('password_reset_email.txt', context)
        html_message = render_to_string('password_reset_email.html', context)

        email_sent = send_mail(
            mail_subject,
            text_message,
            DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        if email_sent == 1:
            print(f"Password reset email sent to {user.email}")
        else:
            print(f"Failed to send email to {user.email}")

    except Exception as e:
        print(f"Error sending password reset email: {str(e)}")

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user:
                # Send password reset email
                send_password_reset_email(request, user)
                messages.success(request, "Password reset email sent.")
                return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
    return render(request, 'forgot_password.html')


@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'profile.html', context)

class CustomPasswordChangeView(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('profile')
    template_name = 'change_password.html'


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


@require_http_methods(["GET", "POST"])
def all_rooms(request):
    selected_college = request.GET.get('college', None)
    selected_buildings = request.GET.getlist('buildings', None)

    # Fetch colleges for the filter
    colleges = College.objects.all()

    # Fetch buildings based on the selected college
    if selected_college:
        buildings = Building.objects.filter(college__name=selected_college)
    else:
        buildings = Building.objects.all()

    # Fetch all rooms based on filters
    all_rooms_list = get_all_rooms(
        college=selected_college if selected_college else None,
        buildings=selected_buildings if selected_buildings else None
    )

    return render(request, 'all_rooms.html', {
        'colleges': colleges,
        'buildings': buildings,
        'all_rooms': all_rooms_list,
        'selected_college': selected_college,
        'selected_buildings': selected_buildings,
    })

@require_http_methods(["GET"])
def colleges(request):
    # Fetch all colleges
    all_colleges = College.objects.all()

    return render(request, 'colleges.html', {
        'colleges': all_colleges,
    })

@require_http_methods(["GET"])
def college_buildings(request, college_name):
    # Get the college object
    try:
        college = College.objects.get(name=college_name)
    except College.DoesNotExist:
        messages.error(request, f"College '{college_name}' not found.")
        return redirect('colleges')

    # Fetch all buildings for this college
    buildings = Building.objects.filter(college=college)

    return render(request, 'college_buildings.html', {
        'college': college,
        'buildings': buildings,
    })
