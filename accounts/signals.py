from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_default_groups(sender, **kwargs):
    # Create default role groups if missing
    student, _ = Group.objects.get_or_create(name="Student")
    instructor, _ = Group.objects.get_or_create(name="Instructor")

    # (Assign permissions of instructors)
    try:
        # Bind permissions for courses.Course specifically
        from courses.models import Course
        ct = ContentType.objects.get_for_model(Course)
        for codename in ("add_course", "change_course", "delete_course", "view_course"):
            perm = Permission.objects.filter(codename=codename, content_type=ct).first()
            if perm:
                instructor.permissions.add(perm)
    except Exception:
        pass