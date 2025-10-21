from django import forms
from .models import Classroom, Schedule
from accounts.models import User
from courses.models import Lesson


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "course", "supervisor", "duration_weeks", "description", "meeting_link", "class_code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supervisor"].queryset = User.objects.filter(role=User.Roles.INSTRUCTOR)
        self.fields["course"].empty_label = "Select a course"
        duration_field = self.fields["duration_weeks"]
        duration_choices = list(duration_field.choices)
        if duration_choices and duration_choices[0][0] != "":
            duration_field.choices = [("", "Select duration")] + duration_choices

        field_classes = {
            "name": {"placeholder": "Please enter the name of class:", "id": "className"},
            "course": {"id": "course"},
            "supervisor": {"id": "supervisor"},
            "duration_weeks": {"id": "duration"},
            "description": {"placeholder": "Add a description for this class...", "rows": 4, "id": "description"},
            "meeting_link": {"placeholder": "https://example.com/meeting-link", "id": "meetingLink"},
            "class_code": {"placeholder": "Please enter the class access code:", "id": "classCode"},
        }

        labels = {
            "name": "Class Name",
            "course": "Associated Course",
            "supervisor": "Supervisor",
            "duration_weeks": "Class Duration",
            "description": "Class Description (Optional)",
            "meeting_link": "Online Meeting Link (Optional)",
            "class_code": "Class Access Code (Optional)",
        }

        for name, field in self.fields.items():
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_classes + " form-control").strip()
            if name in field_classes:
                field.widget.attrs.update(field_classes[name])
            if name in labels:
                field.label = labels[name]


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ["day", "lesson", "start_time", "end_time"]

    def __init__(self, *args, **kwargs):
        classroom = kwargs.pop("classroom", None)
        super().__init__(*args, **kwargs)

        lesson_field = self.fields["lesson"]
        lesson_field.label_from_instance = lambda obj: obj.title
        if classroom and classroom.course_id:
            lesson_field.queryset = Lesson.objects.filter(course=classroom.course)
        else:
            lesson_field.queryset = Lesson.objects.all()
        lesson_field.empty_label = "Select lesson"

        day_field = self.fields["day"]
        day_choices = list(day_field.choices)
        if day_choices and day_choices[0][0] != "":
            day_field.choices = [("", "Select a day")] + day_choices

        for name, field in self.fields.items():
            extra_class = ""
            if name in ("start_time", "end_time"):
                extra_class = "time-input"
            elif name == "lesson":
                extra_class = "lesson-select"
            existing_classes = field.widget.attrs.get("class", "")
            classes = " ".join(filter(None, [existing_classes, "form-control", extra_class]))
            field.widget.attrs["class"] = classes.strip()

        self.fields["start_time"].widget.input_type = "time"
        self.fields["end_time"].widget.input_type = "time"
        self.fields["start_time"].widget.attrs.setdefault("step", "60")
        self.fields["end_time"].widget.attrs.setdefault("step", "60")

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data
