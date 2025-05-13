from django.utils import timezone
from django.db.models import Subquery, OuterRef, IntegerField, Value
from django.db.models.functions import Coalesce
from classrooms.models import RoomAvailability


def get_available_rooms(college=None, buildings=None):
    """Returns list of available rooms with their availability end times."""
    # Use actual current time; comment out for testing
    # now = timezone.localtime(timezone.now())
    # Test datetime: Wednesday 2025-10-02 12:00 PM
    now = timezone.datetime(2025, 10, 2, 12, 0)
    print(now)

    weekday = now.weekday()
    if weekday > 4 or not (8 <= now.hour < 20):
        return ['All rooms free! ..What are you doing here?']

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
        end_hour = 8 + avail.next_occupied // 60
        end_min = avail.next_occupied % 60
        available_rooms.append({
            'name': avail.room.name,
            'college': avail.college.name,
            'building': avail.building.name,
            'available_until': f"{end_hour}:{end_min:02d}"
        })

    # return the rooms sorted by which is available the longest
    available_rooms.sort(key=lambda x: x['available_until'], reverse=True)

    return available_rooms