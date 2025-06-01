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
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required

from emptyClassroom.settings import DEFAULT_FROM_EMAIL
from .forms import CunySignupForm
from classrooms.models import College, Building, Room, RoomAvailability
from classrooms.utils.empty_rooms import get_available_rooms, is_school_hours
from classrooms.utils.all_rooms import get_all_rooms

from django.db.models import Q
from classrooms.models import RoomBooking
from classrooms.forms import RoomBookingForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404


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

    # Check if it's during school hours
    is_during_school_hours, message = is_school_hours()

    # Fetch available rooms only if it's during school hours
    if is_during_school_hours:
        available_rooms = get_available_rooms(
            college=selected_college if selected_college else None,
            buildings=selected_buildings if selected_buildings else None
        )
    else:
        available_rooms = []  # Empty list so count shows 0

    return render(request, 'index.html', {
        'colleges': colleges,
        'buildings': buildings,
        'available_rooms': available_rooms,
        'message': message,  # Pass the message to the template
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


@require_http_methods(["GET"])
def building_rooms(request, college_name, building_name):
    # Get the college object
    try:
        college = College.objects.get(name=college_name)
    except College.DoesNotExist:
        messages.error(request, f"College '{college_name}' not found.")
        return redirect('colleges')

    # Get the building object
    try:
        building = Building.objects.filter(college=college, name=building_name).first()
        if not building:
            raise Building.DoesNotExist
    except Building.DoesNotExist:
        messages.error(request, f"Building '{building_name}' not found in {college_name}.")
        return redirect('college_buildings', college_name=college_name)

    # Fetch all rooms for this building
    rooms = get_all_rooms(college=college_name, buildings=[building_name])

    return render(request, 'building_rooms.html', {
        'college': college,
        'building': building,
        'rooms': rooms,
    })

@require_http_methods(["GET", "POST"])
def room_details(request, college_name, building_name, room_name):
    # Get the college object
    try:
        college = College.objects.get(name=college_name)
    except College.DoesNotExist:
        messages.error(request, f"College '{college_name}' not found.")
        return redirect('colleges')

    # Get the building object
    try:
        building = Building.objects.filter(college=college, name=building_name).first()
        if not building:
            raise Building.DoesNotExist
    except Building.DoesNotExist:
        messages.error(request, f"Building '{building_name}' not found in {college_name}.")
        return redirect('college_buildings', college_name=college_name)

    # Get the room object
    try:
        room = Room.objects.filter(college=college, building=building, name=room_name).first()
        if not room:
            raise Room.DoesNotExist
    except Room.DoesNotExist:
        messages.error(request, f"Room '{room_name}' not found in {building_name}, {college_name}.")
        return redirect('building_rooms', college_name=college_name, building_name=building_name)

    # Initialize variables
    now = timezone.localtime(timezone.now())
    today = now.date()
    current_bookings = None
    is_available = None
    next_available_time = None

    # Get booking-related data only if user is authenticated
    if request.user.is_authenticated:
        # Get current bookings for this room
        current_bookings = RoomBooking.objects.filter(
            room=room,
            booking_date=today
        ).order_by('start_time')

        # Check if room is currently available
        is_available = True
        for booking in current_bookings:
            if booking.start_time <= now.time() <= booking.end_time:
                is_available = False
                break

        # Get next available time
        if not is_available and current_bookings:
            for booking in current_bookings:
                if booking.end_time > now.time():
                    next_available_time = booking.end_time
                    break

    # Check if it's during school hours
    is_during_school_hours, message = is_school_hours()

    # Handle booking form only if user is authenticated and it's during school hours
    form = None
    if request.user.is_authenticated and is_during_school_hours:
        # Calculate next class start time
        next_class_time = None
        weekday = now.weekday()
        current_minute_block = (now.hour - 8) * 60 + now.minute

        # Find the next time when the room is not available (next class)
        next_occupied = RoomAvailability.objects.filter(
            room=room,
            weekday=weekday,
            minute_block__gt=current_minute_block,
            is_available=False
        ).order_by('minute_block').first()

        if next_occupied:
            # Convert minute_block to time
            next_hour = 8 + next_occupied.minute_block // 60
            next_minute = next_occupied.minute_block % 60
            next_class_time = timezone.datetime.strptime(f"{next_hour}:{next_minute}", "%H:%M").time()

        if request.method == 'POST':
            form = RoomBookingForm(request.POST, next_class_time=next_class_time)
            if form.is_valid():
                # Check if room is already booked for this time
                booking_date = form.cleaned_data['booking_date']
                start_time = form.cleaned_data['start_time']
                end_time = form.cleaned_data['end_time']

                existing_bookings = RoomBooking.objects.filter(
                    room=room,
                    booking_date=booking_date,
                ).filter(
                    (Q(start_time__lte=start_time) & Q(end_time__gte=start_time)) |
                    (Q(start_time__lte=end_time) & Q(end_time__gte=end_time)) |
                    (Q(start_time__gte=start_time) & Q(end_time__lte=end_time))
                )

                if existing_bookings.exists():
                    messages.error(request, "This room is already booked for the selected time.")
                else:
                    booking = form.save(commit=False)
                    booking.user = request.user
                    booking.room = room
                    booking.college = college
                    booking.building = building
                    booking.save()
                    messages.success(request, f"Room {room.name} booked successfully!")
                    return redirect('room_details', college_name=college_name, building_name=building_name,
                                    room_name=room_name)
        else:
            # Pre-fill form with current date and time
            # Remove seconds from start time
            start_time = now.time().replace(second=0, microsecond=0)

            # Calculate end time (1 hour later or next class time, whichever is sooner)
            one_hour_later = (now + timezone.timedelta(hours=1)).time().replace(second=0, microsecond=0)
            default_end_time = timezone.datetime.strptime("20:00", "%H:%M").time()

            # Ensure end time is after start time
            if one_hour_later.hour < start_time.hour:  # Handle day boundary case
                end_time = default_end_time
            else:
                end_time = one_hour_later

            if next_class_time:
                # Ensure next_class_time is after start_time
                if (next_class_time.hour > start_time.hour or 
                    (next_class_time.hour == start_time.hour and next_class_time.minute > start_time.minute)):
                    end_time = min(end_time, next_class_time)
                else:
                    # If next_class_time is before start_time, use one_hour_later
                    end_time = one_hour_later

            initial_data = {
                'booking_date': today,
                'start_time': start_time,
                'end_time': end_time
            }
            form = RoomBookingForm(initial=initial_data, next_class_time=next_class_time)

    return render(request, 'room_details.html', {
        'college': college,
        'building': building,
        'room': room,
        'form': form,
        'current_bookings': current_bookings,
        'is_available': is_available,
        'next_available_time': next_available_time,
        'user_bookings': RoomBooking.objects.filter(room=room, user=request.user, booking_date__gte=today).order_by(
            'booking_date', 'start_time') if request.user.is_authenticated else None,
        'is_during_school_hours': is_during_school_hours,
        'message': message,
    })


@login_required
def bookings(request):
    user = request.user
    now = timezone.localtime(timezone.now())
    today = now.date()

    # Get filter parameters
    college_filter = request.GET.get('college', None)
    building_filter = request.GET.get('building', None)
    room_filter = request.GET.get('room', None)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)

    # Base query for all user bookings (only active bookings)
    bookings_query = RoomBooking.objects.filter(user=user, active=True)

    # Apply filters if provided
    if college_filter:
        bookings_query = bookings_query.filter(college__name=college_filter)
    if building_filter:
        bookings_query = bookings_query.filter(building__name=building_filter)
    if room_filter:
        bookings_query = bookings_query.filter(room__name=room_filter)
    if date_from:
        try:
            date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            bookings_query = bookings_query.filter(booking_date__gte=date_from)
        except ValueError:
            pass
    if date_to:
        try:
            date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            bookings_query = bookings_query.filter(booking_date__lte=date_to)
        except ValueError:
            pass

    # Get active bookings (current date and time falls within booking time)
    active_booking = bookings_query.filter(
        booking_date=today,
        start_time__lte=now.time(),
        end_time__gte=now.time()
    ).first()  # Limit to 1 active booking

    # Get future bookings (bookings that haven't started yet)
    future_query = bookings_query.filter(
        Q(booking_date__gt=today) | 
        Q(booking_date=today, start_time__gt=now.time())
    ).order_by('booking_date', 'start_time')

    # Get historical bookings (past bookings or completed today)
    historical_query = bookings_query.exclude(id=active_booking.id if active_booking else 0).filter(
        Q(booking_date__lt=today) | 
        Q(booking_date=today, end_time__lt=now.time())
    ).order_by('-booking_date', '-end_time')

    # Pagination for historical bookings
    page = request.GET.get('page', 1)
    paginator = Paginator(historical_query, 5)  # Show 5 historical bookings per page

    try:
        historical_bookings = paginator.page(page)
    except PageNotAnInteger:
        historical_bookings = paginator.page(1)
    except EmptyPage:
        historical_bookings = paginator.page(paginator.num_pages)

    # Get all colleges, buildings, and rooms for filters
    colleges = College.objects.all()
    buildings = Building.objects.all()
    rooms = Room.objects.all()

    # If a college is selected, filter buildings
    if college_filter:
        buildings = buildings.filter(college__name=college_filter)

    # If a building is selected, filter rooms
    if building_filter:
        rooms = rooms.filter(building__name=building_filter)

    return render(request, 'bookings.html', {
        'active_booking': active_booking,
        'future_bookings': future_query,
        'historical_bookings': historical_bookings,
        'colleges': colleges,
        'buildings': buildings,
        'rooms': rooms,
        'college_filter': college_filter,
        'building_filter': building_filter,
        'room_filter': room_filter,
        'date_from': date_from,
        'date_to': date_to,
        'has_more': historical_bookings.has_next() if historical_bookings else False,
        'current_page': int(page),
    })


@login_required
def cancel_booking(request, booking_id):
    """
    View to handle cancellation of a booking.
    Only allows cancellation of future bookings or currently active bookings.
    """
    try:
        # Get the booking and ensure it belongs to the current user
        booking = RoomBooking.objects.get(id=booking_id, user=request.user)

        # Check if the booking is already inactive
        if not booking.active:
            messages.error(request, "This booking has already been cancelled.")
            return redirect('bookings')

        # Get current time
        now = timezone.localtime(timezone.now())
        today = now.date()

        # Check if the booking is in the past (can't cancel past bookings)
        if booking.booking_date < today or (booking.booking_date == today and booking.end_time < now.time()):
            messages.error(request, "Cannot cancel a booking that has already ended.")
            return redirect('bookings')

        # Mark the booking as inactive (cancelled)
        booking.active = False
        booking.save()

        messages.success(request, f"Booking for {booking.room.name} on {booking.booking_date} has been cancelled.")

    except RoomBooking.DoesNotExist:
        messages.error(request, "Booking not found or you don't have permission to cancel it.")

    return redirect('bookings')
