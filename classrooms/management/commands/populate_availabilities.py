from django.utils import timezone
from datetime import datetime, timedelta, time

from django.core.management.base import BaseCommand
from classrooms.models import Room, Schedule, RoomAvailability


class Command(BaseCommand):
    help = 'Generates weekly availability patterns (5-minute resolution)'

    def handle(self, *args, **options):
        RoomAvailability.objects.all().delete()

        rooms = Room.objects.select_related('building', 'college').all()
        total_minutes = 12 * 60  # 8am-8pm = 12 hours
        interval = 5  # 5-minute resolution

        # Monday=0 to Friday=4
        for weekday in range(5):
            day_code = ['Mo', 'Tu', 'We', 'Th', 'Fr'][weekday]

            for minute in range(0, total_minutes, interval):
                # Find scheduled rooms at this time
                scheduled_rooms = Schedule.objects.filter(
                    day=day_code,
                    start_time__lte=time(8 + minute // 60, minute % 60),
                    end_time__gte=time(8 + minute // 60, minute % 60)
                ).values_list('room_id', flat=True)

                # Create availability records
                RoomAvailability.objects.bulk_create([
                    RoomAvailability(
                        room=room,
                        building=room.building,
                        college=room.college,
                        weekday=weekday,
                        minute_block=minute,
                        is_available=room.id not in scheduled_rooms
                    )
                    for room in rooms
                ], batch_size=1000)

                if minute % 60 == 0:  # Log hourly progress
                    self.stdout.write(f"Processed {day_code} {8 + minute // 60}:00")

        self.stdout.write(self.style.SUCCESS(
            f"Created weekly patterns with {RoomAvailability.objects.count()} entries"
        ))