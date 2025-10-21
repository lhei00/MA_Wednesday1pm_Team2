from django import forms

from .models import Lesson, Course
from django.db.models import Sum


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "lesson_code",
            "title",
            "description",
            "learning_objectives",
            "reading_list",
            "prerequisites",
            "assignments",
            "duration_hours",
            "credit_points",
            "order",
        ]

    def __init__(self, *args, **kwargs):
        course = kwargs.pop("course", None)
        super().__init__(*args, **kwargs)
        prereq_field = self.fields["prerequisites"]
        prereq_field.widget = forms.CheckboxSelectMultiple(attrs={"class": "checkbox-grid"})
        if course is not None:
            prereq_field.queryset = (
                course.lessons.exclude(pk=self.instance.pk).order_by("order", "title")
            )
        else:
            prereq_field.queryset = prereq_field.queryset.exclude(pk=self.instance.pk).order_by("order", "title")
        prereq_field.help_text = "Tick lessons that must be completed before this one."
        self._course_ctx = course

    def clean_credit_points(self):
        cp = self.cleaned_data.get("credit_points") or 0
        if cp < 0:
            raise forms.ValidationError("Credit points cannot be negative.")
        return cp

    def clean(self):
        cleaned = super().clean()
        course = self._course_ctx or getattr(self.instance, "course", None)
        if not course:
            return cleaned
        new_cp = cleaned.get("credit_points") or 0
        qs = Lesson.objects.filter(course=course)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        existing_sum = qs.aggregate(total=Sum("credit_points"))['total'] or 0
        if existing_sum + new_cp > 30:
            self.add_error(
                "credit_points",
                f"Total lesson credits would be {existing_sum + new_cp}, exceeding the 30-credit course limit."
            )
        return cleaned

