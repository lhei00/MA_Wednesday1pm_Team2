from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("classrooms", "0002_scheduleenrollment"),
    ]

    operations = [
        migrations.AddField(
            model_name="classroom",
            name="meeting_link",
            field=models.URLField(
                blank=True,
                null=True,
                help_text="Optional link for online meetings",
            ),
        ),
    ]

