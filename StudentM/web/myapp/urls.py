from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_selection, name='login_selection'),
    path('login/student/', views.login_student, name='login_student'),
    path('login/admin/', views.login_admin, name='login_admin'),
    path('register/student/', views.register_student, name='register_student'),
    path('logout/', views.logout_view, name='logout'),

      # Custom Admin Panel
    path('panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/students/', views.admin_students, name='admin_students'),
    path('panel/attendance/', views.admin_attendance, name='admin_attendance'),
    path('panel/quiz/', views.admin_quiz, name='admin_quiz'),
    path('panel/exam/', views.admin_exam, name='admin_exam'),  

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/quizzes/', views.student_quizzes, name='student_quizzes'),
    path('student/exams/', views.student_exams, name='student_exams'),
]

