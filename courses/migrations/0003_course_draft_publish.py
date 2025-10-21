from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='is_draft',
            field=models.BooleanField(
                default=True,
                help_text="If true, the course is a draft and not visible to students"
            ),
        ),
        migrations.AddField(
            model_name='course',
            name='published_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]