from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Count, Q

from .forms import ClassroomForm, ScheduleForm
from .models import Classroom, Schedule
from courses.models import Course



def _lessons_by_course():
    courses = Course.objects.prefetch_related("lessons").order_by("title")
    return {
        str(course.id): [
            {"id": lesson.id, "label": lesson.title}
            for lesson in course.lessons.all()
        ]
        for course in courses
    }


def is_instructor(user):
    return user.is_authenticated and getattr(user, "role", None) == getattr(user.__class__, "Roles").INSTRUCTOR


@login_required
def classrooms(request):
    base_queryset = (
        Classroom.objects.select_related("course", "supervisor")
        .annotate(student_count=Count("course__enrollments__student", distinct=True))
        .order_by("name")
    )

    try:
        Roles = getattr(request.user.__class__, "Roles")
        role = getattr(request.user, "role", None)
        role_is_instructor = (role == Roles.INSTRUCTOR)
        role_is_student = (role == Roles.STUDENT)
    except Exception:
        role_is_instructor = False
        role_is_student = False

    if role_is_instructor:
        classrooms_qs = base_queryset.filter(
            Q(course__instructor=request.user) | Q(supervisor=request.user)
        ).distinct()
        template = "classrooms/classroom_preview_instructors.html"
        editable_ids = set(
            Classroom.objects.filter(course__instructor=request.user).values_list("id", flat=True)
        )
        context_extra = {"editable_classrooms": editable_ids}
    elif role_is_student:
        classrooms_qs = base_queryset.filter(
            course__enrollments__student=request.user
        ).distinct()
        template = "classrooms/classroom_preview_students.html"
        context_extra = {}
    else:
        classrooms_qs = base_queryset
        template = "classrooms/classroom_preview_students.html"
        context_extra = {}

    context = {"classrooms": classrooms_qs}
    context.update(context_extra)
    return render(request, template, context)


@login_required
def classroom_preview(request, classroom_id):
    classroom = (
        Classroom.objects.select_related("course", "supervisor")
        .annotate(student_count=Count("schedules__enrollments__student", distinct=True))
        .get(id=classroom_id)
    )
    schedules = classroom.schedules.all()
    return render(
        request,
        "classrooms/classroom_preview.html",
        {"classroom": classroom, "schedules": schedules},
    )


@login_required
@user_passes_test(is_instructor)
def create_classroom(request):
    ScheduleFormSet = modelformset_factory(Schedule, form=ScheduleForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = ClassroomForm(request.POST)
        form_valid = form.is_valid()
        classroom_instance = form.save(commit=False) if form_valid else None
        formset = ScheduleFormSet(
            request.POST,
            queryset=Schedule.objects.none(),
            form_kwargs={"classroom": classroom_instance},
        )

        if form_valid and formset.is_valid():
            classroom = form.save()
            schedules = formset.save(commit=False)
            for schedule in schedules:
                schedule.classroom = classroom
                schedule.save()
            for schedule in formset.deleted_objects:
                schedule.delete()
            formset.save_m2m()
            messages.success(request, "Classroom created successfully!")
            return redirect("classrooms")
    else:
        form = ClassroomForm()
        formset = ScheduleFormSet(
            queryset=Schedule.objects.none(),
            form_kwargs={"classroom": None},
        )

    lessons_by_course = _lessons_by_course()

    context = {
        "form": form,
        "formset": formset,
        "page_title": "Create New Classroom",
        "page_subtitle": "Fill in the details below to create a new classroom for your students",
        "submit_label": "Create Classroom",
        "submit_icon": "bx bx-check",
        "back_label": "Back to Classrooms",
        "cancel_label": "Cancel",
        "back_url": reverse("classrooms"),
        "cancel_url": reverse("classrooms"),
        "show_draft": True,
        "is_edit": False,
        "delete_url": None,
        "classroom": None,
        "lessons_by_course": lessons_by_course,
    }
    return render(request, "classrooms/classroom_form.html", context)


@login_required
@user_passes_test(is_instructor)
def manage_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    ScheduleFormSet = modelformset_factory(Schedule, form=ScheduleForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=classroom)
        form_valid = form.is_valid()
        classroom_instance = form.save(commit=False) if form_valid else classroom
        formset = ScheduleFormSet(
            request.POST,
            queryset=classroom.schedules.all(),
            form_kwargs={"classroom": classroom_instance},
        )

        if form_valid and formset.is_valid():
            classroom = form.save()
            schedules = formset.save(commit=False)
            for schedule in schedules:
                schedule.classroom = classroom
                schedule.save()
            for schedule in formset.deleted_objects:
                schedule.delete()
            formset.save_m2m()
            messages.success(request, "Classroom updated successfully!")
            return redirect("classrooms")
    else:
        form = ClassroomForm(instance=classroom)
        formset = ScheduleFormSet(
            queryset=classroom.schedules.all(),
            form_kwargs={"classroom": classroom},
        )

    lessons_by_course = _lessons_by_course()

    context = {
        "form": form,
        "formset": formset,
        "page_title": f"Edit {classroom.name}",
        "page_subtitle": "Update the classroom's details and schedule below.",
        "submit_label": "Save Changes",
        "submit_icon": "bx bx-save",
        "back_label": "Back to Classrooms",
        "cancel_label": "Discard Changes",
        "back_url": reverse("classrooms"),
        "cancel_url": reverse("classrooms"),
        "show_draft": False,
        "is_edit": True,
        "delete_url": reverse("delete_classroom", args=[classroom.id]),
        "classroom": classroom,
        "lessons_by_course": lessons_by_course,
    }
    return render(request, "classrooms/classroom_form.html", context)


@login_required
@user_passes_test(is_instructor)
def delete_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    if request.method == "POST":
        classroom.delete()
        return redirect("classrooms")
    return redirect("classrooms")
