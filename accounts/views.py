import math

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.shortcuts import render, redirect, resolve_url, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required,user_passes_test
from django.utils.decorators import method_decorator
from .forms import InstructorCreationForm, InstructorChangeForm, AdminLoginForm
from .forms import StudentSignupForm
from .models import User
from django.contrib.auth import logout as auth_logout
from django.contrib import messages as dj_messages
from django.db.models import Count, Sum

from django.views.decorators.http import require_POST
from courses.models import Course, LessonProgress, CreditTransaction


class RoleSelectView(TemplateView):
    template_name = "accounts/role_select.html"

class StudentSignupView(View):
    def get(self, request):
        form = StudentSignupForm()
        return render(
            request,
            "accounts/student_login.html",
            {"signup_form": form, "role": "Student", "show_signup": True, "open_register": True},
        )

    def post(self, request):
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Add to Student group if available
            try:
                student_group = Group.objects.get(name="Student")
                user.groups.add(student_group)
            except Group.DoesNotExist:
                pass

            messages.success(request, "Account created. Please log in.")
            return redirect("login_student")
        return render(
            request,
            "accounts/student_login.html",
            {"signup_form": form, "role": "Student", "show_signup": True, "open_register": True},
        )

class LoginStudentView(LoginView):
    template_name = "accounts/student_login.html"
    extra_context = {"role": "Student", "show_signup": True, "open_register": False}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("signup_form", StudentSignupForm())
        return ctx

    def get_success_url(self):
        return reverse("student_dashboard")

    def form_valid(self, form):
        user = form.get_user()
        if getattr(user, "role", None) != User.Roles.STUDENT:
            messages.error(self.request, "Invalid email or password.")
            return redirect("login_student")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password.")
        return super().form_invalid(form)

class LoginInstructorView(LoginView):
    template_name = "accounts/instructor_login.html"
    extra_context = {"role": "Instructor", "show_signup": False}

    def get_success_url(self):
        return reverse("instructor_dashboard")

    def form_valid(self, form):
        user = form.get_user()
        if getattr(user, "role", None) != User.Roles.INSTRUCTOR:
            messages.error(self.request, "Invalid email or password.")
            return redirect("login_instructor")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password.")
        return super().form_invalid(form)
    
def is_admin(user):
    return user.is_authenticated and user.role == User.Roles.ADMIN

def is_student(user):
    return user.is_authenticated and user.role == User.Roles.STUDENT

def admin_login(request):

    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)

            if user is not None and getattr(user, "role", None) == User.Roles.ADMIN:
                auth_login(request, user)
                messages.success(request, "Welcome, Admin!")
                return redirect("admin_dashboard")
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = AdminLoginForm()
    return render(request, "accounts/admin_login.html", {"form": form})

@login_required
@user_passes_test(lambda u: getattr(u, "role", None) == User.Roles.ADMIN)
def admin_dashboard(request):
    ctx = {
        "form": InstructorCreationForm(),
        "show_instructor_form": False,
    }
    return render(request, "accounts/admin-menu.html", ctx)

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    return render(request, "accounts/student-menu.html")

def logout_view(request):
    """Custom logout that allows GET and POST, then redirects to role select."""
    auth_logout(request)
    # Clear any queued messages so they don't appear after logout
    storage = dj_messages.get_messages(request)
    for _ in storage:
        pass
    storage.used = True
    return redirect("role_select")

@login_required
@user_passes_test(is_admin)
def create_instructor(request):
    if request.method == "POST":
        form = InstructorCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Instructor account created successfully.")
            return redirect("admin_dashboard")
        # If coming from embedded form on dashboard, re-render dashboard with errors
        if request.POST.get("from_dashboard"):
            return render(
                request,
                "accounts/admin-menu.html",
                {"form": form, "show_instructor_form": True},
            )
    else:
        form = InstructorCreationForm()

    return render(request, "accounts/create_instructor.html", {"form": form})

@login_required
@user_passes_test(is_admin)
def edit_instructor(request, instructor_id):
    instructor = get_object_or_404(User, id=instructor_id, role=User.Roles.INSTRUCTOR)

    if request.method == "POST":
        form = InstructorChangeForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, "Instructor updated successfully.")
            return redirect("admin_dashboard")
    else:
        form = InstructorChangeForm(instance=instructor)

    return render(request, "accounts/edit_instructor.html", {"form": form, "instructor": instructor})


@login_required
@user_passes_test(is_admin)
def manage_instructors(request):
    instructors = (
        User.objects.filter(role=User.Roles.INSTRUCTOR)
        .annotate(course_count=Count("courses"))
        .order_by("id")
    )
    return render(request, "accounts/manage_instructor.html", {"instructors": instructors})


@login_required
@user_passes_test(is_admin)
@require_POST
def set_instructor_status(request, instructor_id: int):
    instructor = get_object_or_404(User, id=instructor_id, role=User.Roles.INSTRUCTOR)
    action = request.POST.get("action")
    if action == "activate":
        instructor.is_active = True
        instructor.save(update_fields=["is_active"])
        messages.success(request, f"Activated {instructor.get_full_name() or instructor.email}.")
    elif action == "deactivate":
        instructor.is_active = False
        instructor.save(update_fields=["is_active"])
        messages.success(request, f"Deactivated {instructor.get_full_name() or instructor.email}.")
    else:
        messages.error(request, "Invalid action.")
    return redirect("manage_instructors")

@login_required
def instructor_dashboard(request):
    if getattr(request.user, "role", None) != User.Roles.INSTRUCTOR:
        messages.error(request, "Access denied. Instructors only.")
        return redirect("role_select")
    return render(request, "accounts/instructor-menu.html")

@login_required
def instructor_courses(request):
    if getattr(request.user, "role", None) != User.Roles.INSTRUCTOR:
        messages.error(request, "Access denied. Instructors only.")
        return redirect("role_select")
    # Provide courses context for instructor's own courses
    from courses.models import Course
    from django.db.models import Count

    courses = (
        Course.objects.filter(instructor=request.user)
        .annotate(student_count=Count("enrollments"))
        .prefetch_related("lessons")
        .order_by("-created_at")
    )
    return render(request, "courses/courses-instructor.html", {"courses": courses})


@login_required
def student_profile(request):
    user = request.user

    if user.role != User.Roles.STUDENT:
        return redirect("home") 
    
    courses = Course.objects.filter(enrollments__student=user,status=Course.STATUS_ACTIVE).distinct()


    return render(request, "accounts/student_profile.html", {"student": user, "courses": courses})


@login_required
def student_overall_report(request):
    student = request.user

    enrolled_courses = (
        Course.objects.filter(enrollments__student=student)
        .select_related("instructor")
        .prefetch_related("lessons")
    )

    courses_data = []
    total_lessons = 0
    total_completed = 0
    total_credits = 0

    for course in enrolled_courses:
        lessons = course.lessons.all()
        lesson_count = lessons.count()

        completed_count = LessonProgress.objects.filter(
            student=student, lesson__in=lessons, completed=True
        ).count()

        credits_earned = (
            CreditTransaction.objects.filter(student=student, lesson__in=lessons)
            .aggregate(total=Sum("credits"))["total"] or 0
        )

        course_progress = round((completed_count / lesson_count) * 100, 1) if lesson_count else 0

        courses_data.append({
            "id": course.id,
            "code": course.course_code or f"C{course.id:03}",
            "name": course.title,
            "status": "In Progress" if course_progress < 100 else "Completed",
            "completed_lessons": completed_count,
            "total_lessons": lesson_count,
            "credits_earned": credits_earned,
            "total_credits": course.credit_points,
            "active_classrooms": course.lessons.count(),  
            "progress": course_progress,
        })

        total_lessons += lesson_count
        total_completed += completed_count
        total_credits += credits_earned

    overall_progress = (total_credits / 120 * 100) if total_credits else 0
    overall_progress = max(0.0, min(round(overall_progress, 1), 100.0))
    lessons_remaining = total_lessons - total_completed
    circle_radius = 60
    progress_circumference = round(2 * math.pi * circle_radius, 2)
    progress_ratio = overall_progress / 100 if overall_progress else 0
    progress_offset = round(progress_circumference * (1 - progress_ratio), 2)
    last_updated = timezone.now()

    context = {
        "student": student,
        "overall_progress": overall_progress,
        "total_credits": total_credits,
        "lessons_completed": total_completed,
        "total_lessons": total_lessons,
        "active_courses": len(courses_data),
        "lessons_remaining": lessons_remaining,
        "courses": courses_data,
        "progress_circumference": progress_circumference,
        "progress_offset": progress_offset,
        "last_updated": last_updated,
    }

    return render(request, "reports/student_overall_report.html", context)
