from django.contrib.auth.models import AbstractUser
from django.db import models
from django.shortcuts import render




class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        STUDENT = "STUDENT", "Student"

    # Override to make email unique (AbstractUser's default isn't unique)
    email = models.EmailField(unique=True)

    TITLE_CHOICES = [("MR", "Mr"), ("MRS", "Mrs"), ("MS", "Ms"), ("DR", "Dr")]
    title = models.CharField(max_length=5, choices=TITLE_CHOICES, blank=True, null=True)

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)
    student_id = models.CharField(
        max_length=7,
        unique=True,
        blank=True,
        null=True,
        editable=False,
    )

    STUDENT_ID_PREFIX = "stu"
    STUDENT_ID_PADDING = 4

    def save(self, *args, **kwargs):
        # Always keep username in sync with email (lowercased)
        if self.email:
            self.email = self.email.strip().lower()
            self.username = self.email

        if self.is_superuser or self.is_staff:
            self.role = self.Roles.ADMIN

        if self.role == self.Roles.STUDENT and not self.student_id:
            self.student_id = self._generate_student_id()

        super().save(*args, **kwargs)

    @classmethod
    def _generate_student_id(cls):
        prefix = cls.STUDENT_ID_PREFIX
        width = cls.STUDENT_ID_PADDING

        existing_ids = (
            cls.objects.filter(student_id__startswith=prefix)
            .exclude(student_id__isnull=True)
            .values_list("student_id", flat=True)
        )

        max_number = 0
        for sid in existing_ids:
            suffix = sid[len(prefix):]
            if suffix.isdigit():
                max_number = max(max_number, int(suffix))

        next_number = max_number + 1
        candidate = f"{prefix}{next_number:0{width}d}"

        while cls.objects.filter(student_id=candidate).exists():
            next_number += 1
            candidate = f"{prefix}{next_number:0{width}d}"

        return candidate
