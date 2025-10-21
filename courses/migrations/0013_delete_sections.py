from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0012_alter_course_credit_points_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SectionProgress",
        ),
        migrations.DeleteModel(
            name="Section",
        ),
    ]

