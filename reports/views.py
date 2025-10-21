from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Prefetch, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from accounts.models import User
from classrooms.models import Schedule
from courses.models import Course, Enrollment, LessonProgress, CreditTransaction

@login_required
def instructor_report_list(request):
    """Show instructor overview of all students and their progress."""
    instructor = request.user
    try:
        is_instructor = getattr(instructor, "role", None) == instructor.__class__.Roles.INSTRUCTOR
    except Exception:
        is_instructor = False

    if not is_instructor:
        return HttpResponseForbidden("Instructor role required")

    courses = Course.objects.filter(instructor=instructor).prefetch_related("enrollments__student")

    course_reports = []
    all_students_map: dict[int, dict] = {}
    total_progress_sum = 0
    total_students_count = 0

    student_ids = set(
        Enrollment.objects.filter(course__in=courses).values_list("student_id", flat=True)
    )
    student_credit_totals = {
        row["student"]: row["total"] or 0
        for row in CreditTransaction.objects.filter(student_id__in=student_ids)
        .values("student")
        .annotate(total=Sum("credits"))
    }

    for course in courses:
        students = []
        enrollments = (
            Enrollment.objects.filter(course=course)
            .select_related("student")
            .order_by("student__first_name", "student__last_name", "student__email")
        )

        for enrollment in enrollments:
            student = enrollment.student

            total_credits = student_credit_totals.get(student.id, 0)

            # Compute overall progress out of 120 credits
            progress_percent = round((total_credits / 120) * 100, 1)
            progress_percent = max(0.0, min(progress_percent, 100.0))

            if student.id not in all_students_map:
                total_progress_sum += progress_percent
                total_students_count += 1
                all_students_map[student.id] = {
                    "id": student.id,
                    "name": student.get_full_name() or student.email,
                    "email": student.email,
                    "credits": total_credits,
                    "progress_percent": progress_percent,
                    "courses": set(),
                }
            else:
                # Keep latest aggregated stats up to date
                all_students_map[student.id]["credits"] = total_credits
                all_students_map[student.id]["progress_percent"] = progress_percent

            students.append({
                "id": student.id,
                "name": student.get_full_name() or student.email,
                "email": student.email,
                "credits": total_credits,
                "progress_percent": progress_percent,
            })

            all_students_map[student.id]["courses"].add(course.title)

        course_reports.append({
            "course": course,
            "students": students
        })

    avg_progress = round(total_progress_sum / total_students_count, 1) if total_students_count else 0
    avg_progress = max(0.0, min(avg_progress, 100.0))

    all_students_list = []
    for data in all_students_map.values():
        courses_list = sorted(data["courses"])
        all_students_list.append({
            "id": data["id"],
            "name": data["name"],
            "email": data["email"],
            "credits": data["credits"],
            "progress_percent": data["progress_percent"],
            "courses": courses_list,
            "courses_display": ", ".join(courses_list) if courses_list else "—",
            "courses_count": len(courses_list),
        })

    all_students_list.sort(key=lambda s: (s["name"] or "").lower())

    context = {
        "course_reports": course_reports,
        "all_students": all_students_list,
        "summary": {
            "total_students": len(all_students_map),
            "courses_taught": courses.count(),
            "avg_progress": avg_progress,
        },
    }

    return render(request, "reports/instructor_report_list.html", context)


@login_required
def student_course_report(request, course_id: int, student_id: int):
    course = get_object_or_404(Course, pk=course_id)
    student = get_object_or_404(User, pk=student_id)
    user = request.user

    # Determine roles
    user_role = getattr(user, "role", None)
    is_instructor = user_role == User.Roles.INSTRUCTOR
    is_student = user_role == User.Roles.STUDENT

    # Access control
    if is_instructor:
        if course.instructor_id != user.id:
            return HttpResponseForbidden("You can only view reports for your own courses.")
    elif is_student:
        if student.id != user.id:
            return HttpResponseForbidden("You can only view your own report.")
    else:
        return HttpResponseForbidden("Access denied.")

    if student.role != User.Roles.STUDENT:
        return HttpResponseForbidden("Only student reports are available.")

    # Ensure the student is enrolled
    enrollment = get_object_or_404(Enrollment, course=course, student=student)

    origin = request.GET.get("origin")
    back_link = None
    if is_instructor:
        if origin == "course_detail":
            back_link = {
                "url": reverse("course_detail", args=[course.id]),
                "label": "Back to Course Details",
            }
        else:
            back_link = {
                "url": reverse("reports:instructor_report_list"),
                "label": "Back to Reports",
            }
    elif is_student:
        back_link = {
            "url": reverse("student_overall_report"),
            "label": "Back to My overall report",
        }

    # Query data
    enrolled_classrooms_qs = (
        course.classrooms.select_related("supervisor")
        .filter(schedules__enrollments__student=student)
        .prefetch_related(
            Prefetch(
                "schedules",
                queryset=Schedule.objects.filter(enrollments__student=student).order_by("day", "start_time"),
                to_attr="enrolled_schedules",
            )
        )
        .order_by("name")
        .distinct()
    )
    enrolled_classrooms = list(enrolled_classrooms_qs)

    completed_lessons_qs = (
        LessonProgress.objects.filter(
            student=student,
            lesson__course=course,
            completed=True,
        )
        .select_related("lesson")
        .order_by("-updated_at")
    )

    lessons_total = course.lessons.count()
    completed_lessons_count = completed_lessons_qs.count()
    completion_percent = (
        round((completed_lessons_count / lessons_total) * 100)
        if lessons_total
        else 0
    )

    credits_total = (
        CreditTransaction.objects.filter(
            student=student,
            lesson__course=course,
        ).aggregate(total=Coalesce(Sum("credits"), 0))
    )["total"]

    completed_lessons = [
        {
            "code": lp.lesson.lesson_code or f"L{lp.lesson.id:03d}",
            "title": lp.lesson.title,
            "completed_on": lp.updated_at,
        }
        for lp in completed_lessons_qs
    ]

    classroom_cards = []
    for classroom in enrolled_classrooms:
        schedules = [
            f"{s.get_day_display()[:3]} {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
            for s in getattr(classroom, "enrolled_schedules", [])
        ]
        schedule_label = schedules[0] if schedules else "Schedule not set"
        if len(schedules) > 1:
            schedule_label = f"{schedule_label} (+{len(schedules) - 1} more)"
        classroom_cards.append(
            {
                "name": classroom.name,
                "code": classroom.class_code,
                "schedule": schedule_label,
                "supervisor": classroom.supervisor,
            }
        )

    progress = {
        "lessons_total": lessons_total,
        "completed_lessons": completed_lessons_count,
        "completion_percent": completion_percent,
        "enrolled_classrooms": len(enrolled_classrooms),
        "students_total": course.enrollments.count(),
        "credits_earned": credits_total,
        "remaining_lessons": max(lessons_total - completed_lessons_count, 0),
        "completed_lessons_percent": completion_percent,
        "overall_percent": completion_percent,
    }

    context = {
        "course": course,
        "student": student,
        "enrollment": enrollment,
        "classrooms": enrolled_classrooms,
        "progress_available": lessons_total > 0,
        "progress": progress,
        "completed_lessons": completed_lessons,
        "classroom_cards": classroom_cards,
        "back_link": back_link,
    }

    return render(request, "reports/student_report.html", context)

@login_required
def instructor_student_list(request):
    user = request.user
    if getattr(user, "role", None) != User.Roles.INSTRUCTOR:
        return HttpResponseForbidden("Instructor role required")

    courses = Course.objects.filter(instructor=user).order_by("title")
    search_query = request.GET.get("q", "").strip()
    selected_course = request.GET.get("course", "").strip()

    students = User.objects.filter(
        enrollments__course__instructor=user,
        role=User.Roles.STUDENT,
    ).distinct()

    course_id: int | None = None
    if selected_course:
        try:
            course_id = int(selected_course)
        except (TypeError, ValueError):
            course_id = None
        if course_id and courses.filter(id=course_id).exists():
            students = students.filter(enrollments__course_id=course_id)
        else:
            selected_course = ""

    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(student_id__icontains=search_query)
        )

    students = students.order_by("first_name", "last_name", "email").distinct()

    context = {
        "students": students,
        "courses": courses,
        "search_query": search_query,
        "selected_course": selected_course,
    }
    return render(request, "reports/instructor_student_list.html", context)

@login_required
def instructor_student_profile(request, student_id):
    user = request.user
    try:
        is_instructor = getattr(user, "role", None) == user.__class__.Roles.INSTRUCTOR
    except Exception:
        is_instructor = False
    if not is_instructor:
        return HttpResponseForbidden("Instructor role required")

    student = get_object_or_404(User, id=student_id)
    courses = Course.objects.filter(instructor=user, enrollments__student=student).distinct()

    context = {
        "student": student,
        "courses": courses,
    }
    return render(request, "reports/student_profile.html", context)
