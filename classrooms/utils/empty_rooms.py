from django.utils import timezone
from django.db.models import Subquery, OuterRef, IntegerField, Value
from django.db.models.functions import Coalesce
from classrooms.models import RoomAvailability, RoomBooking


def is_school_hours():
    """
    Checks if current time is during school hours (weekdays 8 AM to 8 PM).
    Returns:
        tuple: (bool, str) - (is_school_hours, message_if_not)
    """
    now = timezone.localtime(timezone.now())
    weekday = now.weekday()

    if weekday > 4 or not (8 <= now.hour < 20):
        return False, 'All rooms free! ..What are you doing here?'

    return True, None


def get_available_rooms(college=None, buildings=None):
    """Returns list of available rooms with their availability end times."""
    # Use actual current time; comment out for testing
    now = timezone.localtime(timezone.now())
    # Test datetime: Wednesday 2025-10-02 12:00 PM
    # now = timezone.datetime(2025, 10, 2, 12, 0)
    # print(now)

    weekday = now.weekday()
    current_minute_block = (now.hour - 8) * 60 + now.minute

    # Base query for current availabilities
    availabilities = RoomAvailability.objects.filter(
        weekday=weekday,
        minute_block=current_minute_block,
        is_available=True
    )

    # Apply filters using denormalized fields
    if college:
        availabilities = availabilities.filter(college__name=college)
    if buildings:
        availabilities = availabilities.filter(building__name__in=buildings)

    # Annotate with next occupied time using subquery
    next_occupied_subquery = (
        RoomAvailability.objects.filter(
            room=OuterRef('room'),
            weekday=weekday,
            minute_block__gt=current_minute_block,
            is_available=False
        )
        .order_by('minute_block')
        .values('minute_block')[:1]
    )
    availabilities = availabilities.annotate(
        next_occupied=Coalesce(
            Subquery(next_occupied_subquery),
            Value(959),  # Default to 11:59 PM if no next occupied
            output_field=IntegerField()
        )
    ).select_related('room', 'college', 'building')

    # Build results
    available_rooms = []
    for avail in availabilities:
        # Check if room is currently booked
        today = now.date()
        current_time = now.time()

        # Check for bookings that overlap with current time
        booking_exists = RoomBooking.objects.filter(
            room=avail.room,
            booking_date=today,
            start_time__lte=current_time,
            end_time__gte=current_time
        ).exists()

        if not booking_exists:
            end_hour = 8 + avail.next_occupied // 60
            end_min = avail.next_occupied % 60

            # Find the next booking that starts after now
            next_booking = RoomBooking.objects.filter(
                room=avail.room,
                booking_date=today,
                start_time__gt=current_time
            ).order_by('start_time').first()

            # If there's a booking before the class schedule, adjust available_until
            if next_booking is not None and (
                    next_booking.start_time.hour < end_hour or
                    (next_booking.start_time.hour == end_hour and next_booking.start_time.minute < end_min)
            ):
                available_until = f"{next_booking.start_time.hour}:{next_booking.start_time.minute:02d}"
            else:
                available_until = f"{end_hour}:{end_min:02d}"

            available_rooms.append({
                'name': avail.room.name,
                'college': avail.college.name,
                'building': avail.building.name,
                'available_until': available_until
            })

    # return the rooms sorted by which is available the longest
    available_rooms.sort(key=lambda x: x['available_until'], reverse=True)

    return available_rooms
