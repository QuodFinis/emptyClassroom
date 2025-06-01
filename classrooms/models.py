from django.db import models

"""
schedule data format:
college_name,term,subject,course_code,course_name,building,room,start_date,end_date,days,start_time,end_time
City College,2022 Spring,ACCT,ACCT 21000,Principles of Accounting I,Shepard Hall,1,01/31/2022,05/21/2022,MoWeFr,09:00 AM,09:50 AM


to update database after changes run command 
"""
from django.db import models
from django.contrib.auth.models import User

class ScheduleDump(models.Model):
    """
    This model is used to dump the schedule data from the CSV file.
    """
    college_name = models.CharField(max_length=100)
    term = models.CharField(max_length=20)
    subject = models.CharField(max_length=20)
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=100)
    building = models.CharField(max_length=100)
    room = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.college_name} {self.term} {self.course_code} {self.course_name}"


class College(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Building(models.Model):
    name = models.CharField(max_length=100)
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'college')

    def __str__(self):
        return f"{self.name} ({self.college})"


class Room(models.Model):
    name = models.CharField(max_length=20)
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'college', 'building')

    def __str__(self):
        return f"{self.name} ({self.college} - {self.building})"


class Schedule(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    day = models.CharField(max_length=2)
    start_time = models.TimeField()
    end_time = models.TimeField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=['day', 'start_time', 'end_time']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['room']),
        ]
        unique_together = ('room', 'day', 'start_time', 'end_time', 'start_date', 'end_date')

    def __str__(self):
        return f"{self.room} | {self.day} {self.start_time} - {self.end_time} ({self.start_date} to {self.end_date})"


class RoomAvailability(models.Model):
    """Stores weekly availability patterns (Monday-Friday, 8am-8pm)"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    # Using simple integer fields instead of datetimes
    weekday = models.PositiveSmallIntegerField(  # 0=Monday, 4=Friday
        choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
                 (3, 'Thursday'), (4, 'Friday')]
    )
    minute_block = models.PositiveSmallIntegerField(  # Minutes since 8:00am (0-719)
        help_text="Minutes since 8:00am (0-719 for 12h at 5-min intervals)"
    )
    is_available = models.BooleanField()

    class Meta:
        unique_together = ('room', 'weekday', 'minute_block')
        indexes = [
            models.Index(fields=['weekday', 'minute_block', 'is_available']),
        ]

    @property
    def time_display(self):
        """Convert minute_block back to readable time"""
        hours = 8 + self.minute_block // 60
        minutes = self.minute_block % 60
        return f"{hours:02d}:{minutes:02d}"


class RoomBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('room', 'booking_date', 'start_time')
        indexes = [
            models.Index(fields=['room', 'booking_date']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.room} booked by {self.user.username} on {self.booking_date} from {self.start_time} to {self.end_time}"