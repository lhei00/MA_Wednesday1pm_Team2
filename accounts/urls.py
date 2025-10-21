from django.urls import path
from django.contrib.auth.views import LoginView
from . import views
from .views import (
    LoginStudentView,
    LoginInstructorView,
    RoleSelectView,
    StudentSignupView,
)

urlpatterns = [
    path("", RoleSelectView.as_view(), name="role_select"),
    path("login/student/", LoginStudentView.as_view(), name="login_student"),
    path("signup/student/", StudentSignupView.as_view(), name="signup_student"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("login/instructor/", LoginInstructorView.as_view(), name="login_instructor"),
    path("logout/", views.logout_view, name="logout"),
    path("admin/login/", views.admin_login, name="login_admin"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/create-instructor/", views.create_instructor, name="create_instructor"),
    path("admin/edit-instructor/<int:instructor_id>/", views.edit_instructor, name="edit_instructor"),
    path("admin/instructors/", views.manage_instructors, name="manage_instructors"),
    path("admin/instructors/<int:instructor_id>/status/", views.set_instructor_status, name="set_instructor_status"),
    path("instructor/dashboard/", views.instructor_dashboard, name="instructor_dashboard"),
    path("instructor/courses/", views.instructor_courses, name="instructor_courses"),
    path("profile/", views.student_profile, name="student_profile"),
    path("report/", views.student_overall_report, name="student_overall_report"),

]
