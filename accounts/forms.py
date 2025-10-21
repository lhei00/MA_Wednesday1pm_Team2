from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "username")
        widgets = {"username": forms.HiddenInput()}

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        if email and not cleaned.get("username"):
            cleaned["username"] = email
            if hasattr(self, "data") and hasattr(self.data, "copy"):
                data = self.data.copy()
                data["username"] = email
                self.data = data
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.username and user.email:
            user.username = user.email
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "title",
            "role",
        )
        widgets = {"username": forms.HiddenInput()}


class StudentSignupForm(UserCreationForm):
    # Hide username; derive it from email
    username = forms.CharField(required=False, widget=forms.HiddenInput())
    email = forms.EmailField(label="Email", widget=forms.EmailInput())

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("title", "first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        if email:
            cleaned["username"] = email
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.email and not user.username:
            user.username = user.email.strip().lower()
        # Ensure role is student on signup
        try:
            user.role = User.Roles.STUDENT
        except Exception:
            pass
        if commit:
            user.save()
        return user

class AdminLoginForm(forms.Form):
    
    username = forms.CharField(
        max_length = 150,
        label = "Email or Username",
        widget = forms.TextInput()
    )
    password = forms.CharField(
        widget = forms.PasswordInput(),
        label = "Password"
    )

class InstructorCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["title", "first_name", "last_name", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.INSTRUCTOR
        if commit:
            user.save()
        return user
    
class InstructorChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("title", "first_name", "last_name", "email", "is_active")
        widgets = {
            "title": forms.Select(attrs={"class": "form-input"}),
            "first_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Enter first name"}),
            "last_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Enter last name"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "name@example.com"}),
            "is_active": forms.CheckboxInput(attrs={}),
        }
