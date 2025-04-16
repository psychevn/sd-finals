from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db.models import Count, Avg
from django.forms import formset_factory
from datetime import datetime

from .models import (
    CustomUser, StudentProfile, Subject, AttendanceRecord, 
    Assessment, Quiz, Exam, Question, Choice, QuizResult, ExamResult
)
from .forms import (
    StudentProfileForm, SubjectForm, AttendanceRecordForm, BulkAttendanceForm,
    QuizForm, ExamForm, QuestionForm, ChoiceForm, ChoiceFormSet,
    QuizResultForm, ExamResultForm
)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm

# Login selection
def login_selection(request):
    return render(request, 'login_selection.html')

# Student login
def login_student(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_student:
                login(request, user)
                return redirect('student_dashboard')
        else:
            return render(request, 'login_student.html', {'form': form, 'error': 'Invalid credentials or role'})
    else:
        return render(request, 'login_student.html', {'form': AuthenticationForm()})

# Admin login
def login_admin(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_admin:
                login(request, user)
                return redirect('admin_dashboard')
        else:
            return render(request, 'login_admin.html', {'form': form, 'error': 'Invalid credentials or role'})
    else:
        return render(request, 'login_admin.html', {'form': AuthenticationForm()})

# Student registration
def register_student(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_student = True
            user.save()
            return redirect('login_student')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register_student.html', {'form': form})

# Logout
def logout_view(request):
    logout(request)
    return redirect('login_selection')

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_admin

# Helper function to check if user is student
def is_student(user):
    return user.is_authenticated and user.is_student

# Admin Dashboard
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get count statistics
    total_students = StudentProfile.objects.count()
    subjects = Subject.objects.annotate(student_count=Count('attendancerecord__student', distinct=True))
    recent_attendance = AttendanceRecord.objects.order_by('-date')[:5]
    recent_quizzes = Quiz.objects.order_by('-created_at')[:5]
    recent_exams = Exam.objects.order_by('-created_at')[:5]
    
    # Get average scores for quizzes and exams
    quiz_stats = QuizResult.objects.aggregate(avg_score=Avg('score'))
    exam_stats = ExamResult.objects.aggregate(avg_score=Avg('score'))
    
    context = {
        'total_students': total_students,
        'subjects': subjects,
        'recent_attendance': recent_attendance,
        'recent_quizzes': recent_quizzes,
        'recent_exams': recent_exams,
        'quiz_avg': quiz_stats['avg_score'] if quiz_stats['avg_score'] else 0,
        'exam_avg': exam_stats['avg_score'] if exam_stats['avg_score'] else 0,
    }
    return render(request, 'admin/dashboard.html', context)

# Student Management
@login_required
@user_passes_test(is_admin)
def student_list(request):
    students = StudentProfile.objects.all().order_by('user__last_name')
    return render(request, 'admin/students/list.html', {'students': students})

@login_required
@user_passes_test(is_admin)
def student_detail(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    attendance = AttendanceRecord.objects.filter(student=student).order_by('-date')
    quiz_results = QuizResult.objects.filter(student=student).order_by('-date_taken')
    exam_results = ExamResult.objects.filter(student=student).order_by('-date_taken')
    
    context = {
        'student': student,
        'attendance': attendance,
        'quiz_results': quiz_results,
        'exam_results': exam_results
    }
    return render(request, 'admin/students/detail.html', context)

@login_required
@user_passes_test(is_admin)
def student_edit(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student information updated successfully.')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentProfileForm(instance=student)
    
    return render(request, 'admin/students/edit.html', {'form': form, 'student': student})

# Attendance Management
@login_required
@user_passes_test(is_admin)
def attendance_list(request):
    attendance_records = AttendanceRecord.objects.all().order_by('-date')
    subjects = Subject.objects.all()
    return render(request, 'admin/attendance/list.html', {
        'attendance_records': attendance_records,
        'subjects': subjects
    })

@login_required
@user_passes_test(is_admin)
def attendance_add(request):
    if request.method == 'POST':
        form = AttendanceRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance record added successfully.')
            return redirect('attendance_list')
    else:
        form = AttendanceRecordForm(initial={'date': datetime.now().date()})
    
    return render(request, 'admin/attendance/add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def attendance_bulk_add(request):
    if request.method == 'POST':
        form = BulkAttendanceForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            date = form.cleaned_data['date']
            status = form.cleaned_data['status']
            remarks = form.cleaned_data['remarks']
            students = form.cleaned_data['students']
            
            # Create attendance records for each selected student
            for student in students:
                AttendanceRecord.objects.create(
                    student=student,
                    subject=subject,
                    date=date,
                    status=status,
                    remarks=remarks
                )
            
            messages.success(request, f'Added attendance records for {len(students)} students.')
            return redirect('attendance_list')
    else:
        form = BulkAttendanceForm(initial={'date': datetime.now().date()})
    
    return render(request, 'admin/attendance/bulk_add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def attendance_edit(request, pk):
    attendance = get_object_or_404(AttendanceRecord, pk=pk)
    if request.method == 'POST':
        form = AttendanceRecordForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance record updated successfully.')
            return redirect('attendance_list')
    else:
        form = AttendanceRecordForm(instance=attendance)
    
    return render(request, 'admin/attendance/edit.html', {'form': form, 'attendance': attendance})

# Quiz Management
@login_required
@user_passes_test(is_admin)
def quiz_list(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, 'admin/quiz/list.html', {'quizzes': quizzes})

@login_required
@user_passes_test(is_admin)
def quiz_create(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Quiz created successfully. Now add questions.')
            return redirect('quiz_add_questions', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    return render(request, 'admin/quiz/create.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def quiz_detail(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = Question.objects.filter(quiz=quiz)
    results = QuizResult.objects.filter(quiz=quiz).order_by('-date_taken')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'results': results
    }
    return render(request, 'admin/quiz/detail.html', context)

@login_required
@user_passes_test(is_admin)
def quiz_add_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.quiz = quiz
            question.question_type = 'quiz'
            question.save()
            
            # Process the choices
            choice_formset = ChoiceFormSet(request.POST, instance=question)
            if choice_formset.is_valid():
                choice_formset.save()
                messages.success(request, 'Question added successfully.')
                
                # Check if the user wants to add another question
                if 'add_another' in request.POST:
                    return redirect('quiz_add_questions', quiz_id=quiz.id)
                else:
                    return redirect('quiz_detail', pk=quiz.id)
    else:
        question_form = QuestionForm(initial={'question_type': 'quiz'})
        choice_formset = ChoiceFormSet()
    
    context = {
        'quiz': quiz,
        'question_form': question_form,
        'choice_formset': choice_formset
    }
    return render(request, 'admin/quiz/add_questions.html', context)

@login_required
@user_passes_test(is_admin)
def quiz_edit_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    quiz = question.quiz
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        if question_form.is_valid():
            question = question_form.save()
            
            choice_formset = ChoiceFormSet(request.POST, instance=question)
            if choice_formset.is_valid():
                choice_formset.save()
                messages.success(request, 'Question updated successfully.')
                return redirect('quiz_detail', pk=quiz.id)
    else:
        question_form = QuestionForm(instance=question)
        choice_formset = ChoiceFormSet(instance=question)
    
    context = {
        'quiz': quiz,
        'question': question,
        'question_form': question_form,
        'choice_formset': choice_formset
    }
    return render(request, 'admin/quiz/edit_question.html', context)

# Exam Management
@login_required
@user_passes_test(is_admin)
def exam_list(request):
    exams = Exam.objects.all().order_by('-created_at')
    return render(request, 'admin/exam/list.html', {'exams': exams})

@login_required
@user_passes_test(is_admin)
def exam_create(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, 'Exam created successfully. Now add questions.')
            return redirect('exam_add_questions', exam_id=exam.id)
    else:
        form = ExamForm()
    
    return render(request, 'admin/exam/create.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def exam_detail(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    questions = Question.objects.filter(exam=exam)
    results = ExamResult.objects.filter(exam=exam).order_by('-date_taken')
    
    context = {
        'exam': exam,
        'questions': questions,
        'results': results
    }
    return render(request, 'admin/exam/detail.html', context)

@login_required
@user_passes_test(is_admin)
def exam_add_questions(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.exam = exam
            question.question_type = 'exam'
            question.save()
            
            # Process the choices
            choice_formset = ChoiceFormSet(request.POST, instance=question)
            if choice_formset.is_valid():
                choice_formset.save()
                messages.success(request, 'Question added successfully.')
                
                # Check if the user wants to add another question
                if 'add_another' in request.POST:
                    return redirect('exam_add_questions', exam_id=exam.id)
                else:
                    return redirect('exam_detail', pk=exam.id)
    else:
        question_form = QuestionForm(initial={'question_type': 'exam'})
        choice_formset = ChoiceFormSet()
    
    context = {
        'exam': exam,
        'question_form': question_form,
        'choice_formset': choice_formset
    }
    return render(request, 'admin/exam/add_questions.html', context)

@login_required
@user_passes_test(is_admin)
def exam_edit_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    exam = question.exam
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        if question_form.is_valid():
            question = question_form.save()
            
            choice_formset = ChoiceFormSet(request.POST, instance=question)
            if choice_formset.is_valid():
                choice_formset.save()
                messages.success(request, 'Question updated successfully.')
                return redirect('exam_detail', pk=exam.id)
    else:
        question_form = QuestionForm(instance=question)
        choice_formset = ChoiceFormSet(instance=question)
    
    context = {
        'exam': exam,
        'question': question,
        'question_form': question_form,
        'choice_formset': choice_formset
    }
    return render(request, 'admin/exam/edit_question.html', context)

#student dashboard
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    attendance = AttendanceRecord.objects.filter(student=student).order_by('-date')[:5]
    quiz_results = QuizResult.objects.filter(student=student).order_by('-date_taken')[:5]
    exam_results = ExamResult.objects.filter(student=student).order_by('-date_taken')[:5]

    context = {
        'student': student,
        'attendance': attendance,
        'quiz_results': quiz_results,
        'exam_results': exam_results,
    }
    return render(request, 'student/dashboard.html', context)

#student profile
@login_required
@user_passes_test(is_student)
def student_profile(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    return render(request, 'student/profile.html', {'student': student})
#student attendance
@login_required
@user_passes_test(is_student)
def student_attendance(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    records = AttendanceRecord.objects.filter(student=student).order_by('-date')
    return render(request, 'student/attendance.html', {'records': records})
#student quizzes
@login_required
@user_passes_test(is_student)
def student_quizzes(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    quizzes = Quiz.objects.all().order_by('-created_at')
    quiz_results = QuizResult.objects.filter(student=student)
    taken_quiz_ids = quiz_results.values_list('quiz_id', flat=True)

    context = {
        'quizzes': quizzes,
        'quiz_results': quiz_results,
        'taken_quiz_ids': taken_quiz_ids,
    }
    return render(request, 'student/quiz/list.html', context)
#student exams
@login_required
@user_passes_test(is_student)
def student_exams(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    exams = Exam.objects.all().order_by('-created_at')
    exam_results = ExamResult.objects.filter(student=student)
    taken_exam_ids = exam_results.values_list('exam_id', flat=True)

    context = {
        'exams': exams,
        'exam_results': exam_results,
        'taken_exam_ids': taken_exam_ids,
    }
    return render(request, 'student/exam/list.html', context)