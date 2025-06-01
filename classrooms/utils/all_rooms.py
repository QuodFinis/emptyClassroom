from django.db.models import Subquery, OuterRef, IntegerField, Value
from django.db.models.functions import Coalesce
from classrooms.models import Room


def get_all_rooms(college=None, buildings=None):
    """Returns list of all rooms regardless of availability."""
    
    # Base query for all rooms
    rooms = Room.objects.all().select_related('college', 'building')
    
    # Apply filters
    if college:
        rooms = rooms.filter(college__name=college)
    if buildings:
        rooms = rooms.filter(building__name__in=buildings)
    
    # Build results
    all_rooms = []
    for room in rooms:
        all_rooms.append({
            'name': room.name,
            'college': room.college.name,
            'building': room.building.name,
        })
    
    # Sort rooms by college and building
    all_rooms.sort(key=lambda x: (x['college'], x['building'], x['name']))
    
    return all_rooms