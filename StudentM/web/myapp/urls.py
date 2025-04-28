from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_selection, name='login_selection'),
    path('login/admin/', views.login_admin, name='login_admin'),
    path('login/student/', views.login_student, name='login_student'),
    path('register/student/', views.register_student, name='register_student'),
    path('logout/', views.logout_view, name='logout'),

    # Admin Panel
    path('panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/students/', views.admin_students, name='admin_students'),
    path('panel/attendance/', views.admin_attendance, name='admin_attendance'),
    
    # Admin Quiz
    path('panel/quiz/', views.admin_quiz, name='admin_quiz'),
    path('panel/quiz/create/', views.quiz_question_bank, name='quiz_question_bank'),
    path('panel/quiz/<int:quiz_id>/edit/', views.quiz_question_bank, name='quiz_edit'),
    path('panel/quiz/<int:quiz_id>/responses/', views.quiz_responses, name='quiz_responses'),
    path('panel/quiz/<int:quiz_id>/responses/<int:result_id>/grade/', views.grade_quiz, name='grade_quiz'),
    
    # Admin Exam
    path('panel/exam/', views.admin_exam, name='admin_exam'),
    path('panel/exam/create/', views.exam_create, name='exam_create'),
    path('panel/exam/<int:exam_id>/edit/', views.exam_add_questions, name='exam_edit'),
    path('panel/exam/<int:exam_id>/responses/', views.exam_responses, name='exam_responses'),
    path('panel/exam/<int:exam_id>/responses/<int:result_id>/grade/', views.grade_exam, name='grade_exam'),

    # Student Views
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/quiz/', views.student_quizzes, name='student_quiz'),
    path('student/quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('student/exam/', views.student_exams, name='student_exam'),
    path('student/exam/<int:exam_id>/take/', views.take_exam, name='take_exam'),
]