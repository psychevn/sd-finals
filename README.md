# Acadex

A web-based management system built with Django, designed to streamline academic administration and student management processes.

## Key Features

### Student Management
- Admin approval system for new student registrations
- Student profile management with photo upload capability
- Attendance tracking by subject

### Academic Management
- Quiz creation and management
- Exam creation and management
- Question bank system for quizzes and exams
- Automated grading system for objective questions
- Manual grading for subjective questions

### Attendance System
- Subject-based attendance tracking
- Bulk attendance entry
- Status tracking (Present, Absent, Late)
- Attendance statistics and reports
- Student attendance history

### User Roles
- Admin Dashboard with comprehensive overview
- Student Dashboard with personal statistics
- Role-based access control (Admin/Student)
- Permission-based features

### Security Features
- Secure authentication system
- Password encryption
- Admin approval for student accounts
- Role-based access control
- Session management

## Technologies Used

- Backend: Django 5.2
- Frontend: HTML5, CSS3, JavaScript
- Database: PostgreSQL/SQLite
- Forms: Django Forms
- User Authentication: Django Authentication System
- UI Components: Custom CSS with modern design
- Animations: Animate.css
- Fonts: Montserrat, Roboto, Poppins, Noto Sans, Inter, Erica One, Rubik, STIX Two Text

## Setup Instructions

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser (admin account):
```bash
python manage.py createsuperuser
```

6. Add default subjects:
```python
from myapp.models import Subject
subjects = [
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
for subject in subjects:
    Subject.objects.get_or_create(name=subject)
```

7. Start the development server:
```bash
python manage.py runserver
```

Access the application at http://localhost:8000

## Project Structure

```
myapp/
├── templates/
│   ├── panel/         # Admin templates
│   │   ├── dashboard.html
│   │   ├── students.html
│   │   ├── quiz.html
│   │   └── exam.html
│   └── student/       # Student templates
│       ├── dashboard.html
│       ├── quiz.html
│       ├── exam.html
│       └── attendance.html
├── static/
│   ├── css/          # Custom styles
│   └── images/       # Static images
├── views.py          # View logic
├── urls.py           # URL routing
└── models.py         # Database models
```

## Usage

### Admin Features
1. Login to admin panel using credentials
2. Manage students (approve, reject, delete)
3. Create and manage subjects
4. Create and manage quizzes/exams
5. Track attendance statistics
6. View student performance reports

### Student Features
1. Register with email verification
2. Login with approved account
3. Take quizzes and exams
4. Track attendance
5. View academic performance
6. Update personal profile

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Programmers
- Kenneth Hermo
https://github.com/psychevn
- Zed
- Ahldous

## License

This project is licensed under the MIT License - see the LICENSE file for details.
