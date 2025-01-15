from django.contrib import admin
from .models import (
    School, Department, Professor, Course, Building, Floor, Room, Schedule
)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'school_name')
    search_fields = ('school_name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'department_name', 'school')
    search_fields = ('department_name',)
    list_filter = ('school',)


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'professor_name', 'rating')
    search_fields = ('professor_name',)
    list_filter = ('school',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'course_code', 'course_name', 'class_number', 'department')
    search_fields = ('course_code', 'course_name')
    list_filter = ('department',)


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('id', 'building_name', 'school')
    search_fields = ('building_name',)
    list_filter = ('school',)


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('id', 'building', 'floor_number')
    list_filter = ('building',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_name', 'floor')
    list_filter = ('floor__building', 'floor__floor_number')
    search_fields = ('room_name',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'section', 'professor', 'room', 'start_time', 'end_time')
    search_fields = ('course__course_code', 'course__course_name', 'section', 'professor__professor_name')
    list_filter = ('course__department', 'room__floor__building', 'start_time', 'end_time')
