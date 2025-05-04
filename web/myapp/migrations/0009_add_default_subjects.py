from django.db import migrations

def add_default_subjects(apps, schema_editor):
    Subject = apps.get_model('myapp', 'Subject')
    default_subjects = [
        'Mathematics',
        'Science',
        'English',
        'History',
        'Computer Science',
        'Physical Education',
        'Art',
        'Music',
        'Geography',
        'Economics'
    ]
    
    for subject_name in default_subjects:
        Subject.objects.get_or_create(name=subject_name)

def remove_default_subjects(apps, schema_editor):
    Subject = apps.get_model('myapp', 'Subject')
    default_subjects = [
        'Mathematics',
        'Science',
        'English',
        'History',
        'Computer Science',
        'Physical Education',
        'Art',
        'Music',
        'Geography',
        'Economics'
    ]
    
    Subject.objects.filter(name__in=default_subjects).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('myapp', '0008_alter_choice_options_alter_question_options_and_more'),
    ]

    operations = [
        migrations.RunPython(add_default_subjects, remove_default_subjects),
    ] 