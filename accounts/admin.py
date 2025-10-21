from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ("email", "student_id", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active", "groups")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "title", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    # You can set role after creation or via actions
                    "is_staff",
                    "is_active",
                    "groups",
                ),
            },
        ),
    )

    actions = [
        "make_student",
        "make_instructor",
        "make_admin_role",
    ]

    def _ensure_group(self, name: str) -> Group:
        try:
            return Group.objects.get(name=name)
        except Group.DoesNotExist:
            return Group.objects.create(name=name)

    @admin.action(description="Mark selected as Student and add to Student group")
    def make_student(self, request, queryset):
        student_group = self._ensure_group("Student")
        instructor_group = self._ensure_group("Instructor")
        updated = 0
        for user in queryset:
            user.role = User.Roles.STUDENT
            user.is_staff = user.is_staff  # no change
            user.save()
            user.groups.add(student_group)
            user.groups.remove(instructor_group)
            updated += 1
        self.message_user(request, f"Updated {updated} user(s) to Student.")

    @admin.action(description="Mark selected as Instructor and add to Instructor group")
    def make_instructor(self, request, queryset):
        instructor_group = self._ensure_group("Instructor")
        student_group = self._ensure_group("Student")
        updated = 0
        for user in queryset:
            user.role = User.Roles.INSTRUCTOR
            user.is_staff = True  # instructors can access instructor areas; adjust if undesired
            user.save()
            user.groups.add(instructor_group)
            user.groups.remove(student_group)
            updated += 1
        self.message_user(request, f"Updated {updated} user(s) to Instructor.")

    @admin.action(description="Mark selected as Admin role (does not change superuser)")
    def make_admin_role(self, request, queryset):
        updated = 0
        for user in queryset:
            user.role = User.Roles.ADMIN
            user.is_staff = True
            user.save()
            updated += 1
        self.message_user(request, f"Updated {updated} user(s) to Admin role.")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Keep group membership in sync with role
        try:
            student_group = self._ensure_group("Student")
            instructor_group = self._ensure_group("Instructor")
            if obj.role == User.Roles.INSTRUCTOR:
                obj.groups.add(instructor_group)
                obj.groups.remove(student_group)
            elif obj.role == User.Roles.STUDENT:
                obj.groups.add(student_group)
                obj.groups.remove(instructor_group)
        except Exception:
            pass
