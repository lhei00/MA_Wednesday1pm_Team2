from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [

    path(
        "instructor/",
        views.instructor_report_list,
        name="instructor_report_list",
    ),

    path(
        "courses/<int:course_id>/students/<int:student_id>/",
        views.student_course_report,
        name="student_course_report",
    ),

    path(
        "instructor/students/",
        views.instructor_student_list,
        name="instructor_student_list",
    ),

    path(
        "instructor/students/<int:student_id>/",
         views.instructor_student_profile,
         name="student_profile",
    ),
]
