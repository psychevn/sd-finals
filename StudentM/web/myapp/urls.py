from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_selection, name='login_selection'),
    path('login/student/', views.login_student, name='login_student'),
    path('login/admin/', views.login_admin, name='login_admin'),
    path('register/student/', views.register_student, name='register_student'),
    path('logout/', views.logout_view, name='logout'),

    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', views.student_list, name='student_list'),
    path('admin/students/<int:pk>/', views.student_detail, name='student_detail'),  # Show student details
    path('admin/students/<int:pk>/edit/', views.student_edit, name='student_edit'),  # Edit student details
    path('admin/attendance/', views.attendance_list, name='attendance_list'),
    path('admin/attendance/add/', views.attendance_add, name='attendance_add'),
    path('admin/attendance/bulk_add/', views.attendance_bulk_add, name='attendance_bulk_add'),
    path('admin/attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('admin/quiz/', views.quiz_list, name='quiz_list'),
    path('admin/quiz/create/', views.quiz_create, name='quiz_create'),
    path('admin/quiz/<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('admin/quiz/<int:quiz_id>/add_questions/', views.quiz_add_questions, name='quiz_add_questions'),
    path('admin/quiz/question/<int:question_id>/edit/', views.quiz_edit_question, name='quiz_edit_question'),
    path('admin/exam/', views.exam_list, name='exam_list'),
    path('admin/exam/create/', views.exam_create, name='exam_create'),
    path('admin/exam/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('admin/exam/<int:exam_id>/add_questions/', views.exam_add_questions, name='exam_add_questions'),
    path('admin/exam/question/<int:question_id>/edit/', views.exam_edit_question, name='exam_edit_question'),

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/quizzes/', views.student_quizzes, name='student_quizzes'),
    path('student/exams/', views.student_exams, name='student_exams'),
]

