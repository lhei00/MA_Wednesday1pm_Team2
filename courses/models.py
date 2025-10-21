from django.db import models
from django.conf import settings

class Course(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
    )

    title = models.CharField(max_length=255)
    course_code = models.CharField(max_length=32, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    credit_points = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    duration_weeks = models.PositiveIntegerField(default=12)
    max_students = models.PositiveIntegerField(default=50)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses"
    )

    #new field
    is_draft = models.BooleanField(
        default=True,
        help_text="If true, the course is a draft and not visible to students"
    )
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "course"

    def publish(self, when):
            self.is_draft = False
            self.published_at = when
            self.save(update_fields=["is_draft", "published_at"])

    def save(self, *args, **kwargs):
        # Always enforce 30 credit points per course
        self.credit_points = 30

        existing = Course.objects.filter(pk=self.pk).first() if self.pk else None
        if existing and existing.status == Course.STATUS_INACTIVE:
            self.enrollments.all().delete()

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title
    
class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    date_enrolled = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
                models.UniqueConstraint(fields=["student", "course"], name="unique_enrollment")
            ]

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    lesson_code = models.CharField(max_length=32, blank=True, null=True, help_text="Lesson ID/Code")
    description = models.TextField(blank=True)
    learning_objectives = models.TextField(blank=True, help_text="One per line or paragraph")
    reading_list = models.TextField(blank=True, help_text="References or links, one per line")
    assignments = models.TextField(blank=True)
    duration_hours = models.PositiveIntegerField(default=0)
    credit_points = models.PositiveIntegerField(default=0)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="lessons"
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="unlocks",
        help_text="Select lessons that must be completed before this one"
    )

    class Meta:
        ordering = ["order", "created_at"]
        db_table = "lesson"
        constraints = [
            models.UniqueConstraint(fields=["course", "lesson_code"], name="unique_lesson_code_per_course")
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.course.title})"
    
class LearningMaterial(models.Model):
    TYPE_PDF = "pdf"
    TYPE_VIDEO = "video"
    TYPE_LINK = "link"
    TYPE_CHOICES = [
        (TYPE_PDF, "PDF Document"),
        (TYPE_VIDEO, "Video"),
        (TYPE_LINK, "External Link"),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_LINK)
    file = models.FileField(upload_to="materials/", blank=True, null=True)
    url = models.URLField(blank=True, null=True, help_text="External link (if applicable)")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "learning_material"
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} ({self.get_material_type_display()})"

class LessonProgress(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress"
    )
    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name="progress_records"
    )
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "lesson")
        db_table = "lesson_progress"

    def __str__(self) -> str:
        return f"{self.student} - {self.lesson.title} - {'done' if self.completed else 'not done'}"
    
class LearningMaterialProgress(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="material_progress",
    )
    material = models.ForeignKey(
        "LearningMaterial",
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "material")
        db_table = "learning_material_progress"

    def __str__(self):
        return f"{self.student} - {self.material.title} - {'done' if self.completed else 'not done'}"


class CreditTransaction(models.Model):

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="credit_txns")
    lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE, related_name="credit_txns")
    credits = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "lesson")
        db_table = "credit_transaction"

    def __str__(self):
        return f"{self.student} earned {self.credits} for {self.lesson}"
    
class LessonItemProgress(models.Model):
    SECTION_READING = "reading"
    SECTION_ASSIGNMENT = "assignment"
    SECTION_CHOICES = [
        (SECTION_READING, "Reading"),
        (SECTION_ASSIGNMENT, "Assignment"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_item_progress"
    )
    lesson = models.ForeignKey(
        "Lesson", on_delete=models.CASCADE, related_name="item_progress"
    )
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    item_index = models.PositiveIntegerField() 
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "lesson", "section", "item_index")
        db_table = "lesson_item_progress"

    def __str__(self):
        return f"{self.student} - {self.lesson} - {self.section}[{self.item_index}] -> {'done' if self.completed else 'not'}"
    

class LessonSchedule(models.Model):
    lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE, related_name="lesson_schedules")
    classroom = models.CharField(max_length=100, help_text="Classroom or session name")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=20)

    class Meta:
        db_table = "lesson_schedule"
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.lesson.title} - {self.classroom} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

    @property
    def enrolled_count(self):
        return self.enrollments.count()

    def is_full(self):
        return self.enrolled_count >= self.capacity
