from django.db import migrations

def approve_existing_students(apps, schema_editor):
    StudentProfile = apps.get_model('myapp', 'StudentProfile')
    # Set all existing student profiles as approved
    StudentProfile.objects.all().update(is_approved=True)

class Migration(migrations.Migration):
    dependencies = [
        ('myapp', '0013_studentprofile_date_registered_and_more'),
    ]

    operations = [
        migrations.RunPython(approve_existing_students),
    ] 