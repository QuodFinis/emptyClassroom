from django.db import models
from django.db.utils import IntegrityError


class School(models.Model):
    school_name = models.CharField(max_length=64)

    def __str__(self):
        return self.school_name


class Department(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    department_name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.department_name} ({self.school.school_name})"


class Professor(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='professors')
    professor_name = models.CharField(max_length=64)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    def __str__(self):
        # TODO: Get all departments professor is in
        departments=''
        return f"{self.professor_name} ({departments})"


class Course(models.Model):
    course_code = models.CharField(max_length=16, null=True, blank=True)
    course_name = models.CharField(max_length=64)
    class_number = models.CharField(max_length=16, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses', null=True, blank=True)

    def __str__(self):
        return f"{self.department} - {self.course_code} {self.course_name}"


class Building(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='buildings')
    building_name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.building_name} ({self.school.school_name})"


class Floor(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.IntegerField()

    def __str__(self):
        return f"{self.building.building_name}, Floor {self.floor_number}"


class Room(models.Model):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_name = models.CharField(max_length=64)

    def __str__(self):
        return f"Room {self.room_name} ({self.floor.building.building_name}, Floor {self.floor.floor_number})"


class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)
    section = models.CharField(max_length=16)
    days = models.CharField(
        choices=(
            ('M', 'Monday'),
            ('Tu', 'Tuesday'),
            ('W', 'Wednesday'),
            ('Th', 'Thursday'),
            ('F', 'Friday'),
            ('Sa', 'Saturday'),
            ('Su', 'Sunday'),
        ),
        max_length=12,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='schedules')

    def __str__(self):
        return f"{self.course.course_code} Section {self.section} - {self.days} {self.start_time}-{self.end_time} in {self.room}"


class UploadedFileStatus(models.Model):
    blob_url = models.URLField()  # URL of the file in Azure Blob Storage
    status = models.CharField(
        max_length=16,
        choices=[('Pending', 'Pending'), ('Processing', 'Processing'), ('Completed', 'Completed'), ('Failed', 'Failed')],
        default='Pending'
    )
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
