from django.urls import path
from . import views
from .views import (
    CourseCreateView,
    CourseListView,
    CourseDetailView,
    course_enroll,
    course_instructor_list,
    CourseUpdateView,
    course_delete,
    student_courses,
    available_courses,
    LessonCreateView,
    LessonDetailView,
    LessonUpdateView,
    lesson_delete,
    CoursePreviewInstructorView,
    CoursePreviewStudentView,
    toggle_lesson_progress
)

urlpatterns = [
    path("instructor/courses/new/", CourseCreateView.as_view(), name="course_create"),
    path("instructor/courses/", course_instructor_list, name="instructor_courses"),
    path("instructor/courses/<int:pk>/edit/", CourseUpdateView.as_view(), name="course_edit"),
    path("instructor/courses/<int:pk>/delete/", course_delete, name="course_delete"),
    path("instructor/courses/<int:course_id>/lessons/new/", LessonCreateView.as_view(), name="lesson_create"),
    path("instructor/lessons/<int:pk>/edit/", LessonUpdateView.as_view(), name="lesson_edit"),
    path("instructor/lessons/<int:lesson_id>/delete/", lesson_delete, name="lesson_delete"),
    path("lessons/<int:pk>/", LessonDetailView.as_view(), name="lesson_detail"),
    path("courses/<int:pk>/", CourseDetailView.as_view(), name="course_detail"),
    path("courses/<int:course_id>/enroll/", course_enroll, name="course_enroll"),
    path("student/courses/", student_courses, name="student_courses"),
    path("student/courses/available/", available_courses, name="available_courses"),
    path("instructor/courses/<int:pk>/preview/",CoursePreviewInstructorView.as_view(),name="course_preview_instructor"),
    path("student/courses/<int:pk>/preview/", CoursePreviewStudentView.as_view(), name="student_course_preview"),
    path("lessons/<int:lesson_id>/toggle-progress/", toggle_lesson_progress, name="toggle_lesson_progress"),
    path("lesson-schedule/<int:schedule_id>/enroll/", views.enroll_schedule, name="enroll_schedule"),
    path("unenroll/<int:schedule_id>/", views.unenroll_schedule, name="unenroll_schedule"),



]
