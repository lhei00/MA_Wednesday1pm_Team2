from django.db import models
from datetime import timedelta
from courses.models import Course, Lesson
from django.conf import settings


class Classroom(models.Model):

    DURATION_CHOICES = [
        (2, "2 weeks"),
        (3, "3 weeks"),
        (4, "4 weeks"),
    ]

    name = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="classrooms")
    supervisor = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,limit_choices_to={"role": "INSTRUCTOR"}, related_name="supervised_classrooms")
    duration_weeks = models.PositiveIntegerField(choices=DURATION_CHOICES)
    description = models.TextField(blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True, help_text="Optional link for online meetings")
    class_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def end_date(self):
        return self.created_at.date() + timedelta(weeks=self.duration_weeks)

    def __str__(self):
        return f"{self.name} - {self.course.name}"


class Schedule(models.Model):
    DAYS = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
    ]

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="schedules")
    day = models.CharField(max_length=20, choices=DAYS)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="schedules")  
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.classroom.name} - {self.day} ({self.lesson})"
    
class ScheduleEnrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="schedule_enrollments"
    )
    schedule = models.ForeignKey(
        "classrooms.Schedule", on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "schedule")

    def __str__(self):
        return f"{self.student} enrolled in {self.schedule}"
