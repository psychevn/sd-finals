from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db.models import Count, Avg
from django.forms import formset_factory
from datetime import datetime
from django.contrib.auth.hashers import make_password
from .models import (
    CustomUser, StudentProfile, Subject, AttendanceRecord, 
    Assessment, Quiz, Exam, Question, Choice, QuizResult, ExamResult,
    StudentAnswer
)
from .forms import (
    StudentProfileForm, SubjectForm, AttendanceRecordForm, BulkAttendanceForm,
    QuizForm, ExamForm, QuestionForm, ChoiceForm, ChoiceFormSet,
    QuizResultForm, ExamResultForm
)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser, StudentProfile
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
import json
from django.utils import timezone

# Login selection
def login_selection(request):
    return render(request, 'login_selection.html')

# Student login
def login_student(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if user exists first
        try:
            user_exists = CustomUser.objects.get(email=email)
            print(f"User found: {user_exists.email}")
            
            # Check if student profile is approved
            if hasattr(user_exists, 'studentprofile') and not user_exists.studentprofile.is_approved:
                messages.error(request, "Your account is pending approval. Please wait for admin verification.")
                return render(request, 'login_student.html')
            
            # Now try authentication
            user = authenticate(request, email=email, password=password)
            
            if user is None:
                messages.error(request, "Password is incorrect.")
            elif not user.is_student:
                messages.error(request, "This account doesn't have student permissions.")
            else:
                login(request, user)
                return redirect('student_dashboard')
                
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with this email.")
    
    return render(request, 'login_student.html')

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
        # Get form data
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        middle_name = request.POST.get('middle_name')
        student_number = request.POST.get('student_number')
        section = request.POST.get('section')
        course = request.POST.get('course')
        birthday = request.POST.get('birthday')

        # Basic validation
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
        elif StudentProfile.objects.filter(student_number=student_number).exists():
            messages.error(request, "Student number is already in use.")
        else:
            username = request.POST.get('username')

            user = CustomUser.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_student=True,
                password=password,
            )
            StudentProfile.objects.create(
                user=user,
                middle_name=middle_name,
                student_number=student_number,
                section=section,
                course=course,
                birthday=birthday,
                is_approved=False  # Set as pending by default
            )
            messages.success(request, "Registration successful! Please wait for admin approval.")

    return render(request, 'register_student.html')

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
    
    # Get today's attendance count
    today = datetime.now().date()
    students_attended_today = AttendanceRecord.objects.filter(
        date=today,
        status='Present'
    ).values('student').distinct().count()
    
    # Get pending tasks (quizzes and exams that need grading)
    pending_quiz_grades = QuizResult.objects.filter(
        is_completed=True,
        is_graded=False
    ).count()
    
    pending_exam_grades = ExamResult.objects.filter(
        is_completed=True,
        is_graded=False
    ).count()
    
    total_pending_tasks = pending_quiz_grades + pending_exam_grades

    # Get pending student approvals
    pending_students = StudentProfile.objects.filter(is_approved=False).order_by('-date_registered')
    
    # Get other statistics
    subjects = Subject.objects.annotate(student_count=Count('attendancerecord__student', distinct=True))
    recent_attendance = AttendanceRecord.objects.order_by('-date')[:5]
    recent_quizzes = Quiz.objects.order_by('-created_at')[:5]
    recent_exams = Exam.objects.order_by('-created_at')[:5]
    
    # Get average scores for quizzes and exams
    quiz_stats = QuizResult.objects.aggregate(avg_score=Avg('score'))
    exam_stats = ExamResult.objects.aggregate(avg_score=Avg('score'))
    
    context = {
        'total_students': total_students,
        'students_attended_today': students_attended_today,
        'total_pending_tasks': total_pending_tasks,
        'subjects': subjects,
        'recent_attendance': recent_attendance,
        'recent_quizzes': recent_quizzes,
        'recent_exams': recent_exams,
        'quiz_avg': quiz_stats['avg_score'] if quiz_stats['avg_score'] else 0,
        'exam_avg': exam_stats['avg_score'] if exam_stats['avg_score'] else 0,
        'pending_students': pending_students,  # Add pending students to context
    }
    return render(request, 'panel/dashboard.html', context)

# Student Management
@login_required
@user_passes_test(is_admin)
def admin_students(request):
    students = StudentProfile.objects.all().order_by('user__last_name')
    return render(request, 'panel/students.html', {'students': students})

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

# Attendance Page (Admin)
@login_required
@user_passes_test(is_admin)
def admin_attendance(request):
    if request.method == 'POST':
        form = AttendanceRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance record added successfully.')
            return redirect('admin_attendance')
    else:
        form = AttendanceRecordForm(initial={'date': datetime.now().date()})

    # Get filter parameters
    subject_filter = request.GET.get('subject')
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')

    # Base queryset
    attendances = AttendanceRecord.objects.all().order_by('-date')

    # Apply filters
    if subject_filter:
        attendances = attendances.filter(subject_id=subject_filter)
    if date_filter:
        attendances = attendances.filter(date=date_filter)
    if status_filter:
        attendances = attendances.filter(status=status_filter)

    # Calculate statistics
    present_count = attendances.filter(status='Present').count()
    absent_count = attendances.filter(status='Absent').count()
    late_count = attendances.filter(status='Late').count()

    context = {
        'attendances': attendances,
        'form': form,
        'subjects': Subject.objects.all(),
        'selected_subject': subject_filter,
        'selected_date': date_filter,
        'selected_status': status_filter,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
    }
    return render(request, 'panel/attendance.html', context)

# Quiz Page (Admin)
@login_required
@user_passes_test(is_admin)
def admin_quiz(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    subjects = Subject.objects.all()
    return render(request, 'panel/quiz.html', {
        'quizzes': quizzes,
        'subjects': subjects
    })

# Exam Page (Admin)
@login_required
@user_passes_test(is_admin)
def admin_exam(request):
    exams = Exam.objects.all().order_by('-created_at')
    context = {
        'exams': exams
    }
    return render(request, 'panel/exam.html', context)

# Attendance Management
@login_required
@user_passes_test(is_admin)
def attendance_list(request):
    attendance_records = AttendanceRecord.objects.all().order_by('-date')
    subjects = Subject.objects.all()
    return render(request, 'panel/attendance-list.html', {
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
    
    return render(request, 'panel/attendance-add.html', {'form': form})

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
    
    return render(request, 'panel/attendance-bulk_add.html', {'form': form})

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
    
    return render(request, 'panel/attendance-edit.html', {'form': form, 'attendance': attendance})

# Quiz Management
@login_required
@user_passes_test(is_admin)
def quiz_list(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, 'panel/quiz-list.html', {'quizzes': quizzes})

@login_required
@user_passes_test(is_admin)
def quiz_question_bank(request, quiz_id=None):
    if quiz_id:
        quiz = get_object_or_404(Quiz, pk=quiz_id)
    else:
        quiz = None

    if request.method == 'POST':
        if quiz:
            form = QuizForm(request.POST, instance=quiz)
        else:
            form = QuizForm(request.POST)
        
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.is_published = True
            quiz.is_active = True
            quiz.save()  # First save to get a primary key
            
            # Delete existing questions if editing
            if quiz_id:
                quiz.questions.all().delete()
            
            # Process questions if they exist in the request
            questions_data = request.POST.get('questions')
            if questions_data:
                try:
                    questions_data = json.loads(questions_data)
                    for q_data in questions_data:
                        question = Question.objects.create(
                            quiz=quiz,
                            question_type=q_data['type'],
                            content=q_data['text'],
                            points=q_data.get('points', 1),
                            order=q_data.get('order', 0)
                        )
                        
                        if q_data['type'] == 'multiple_choice':
                            for c_data in q_data['choices']:
                                Choice.objects.create(
                                    question=question,
                                    text=c_data['text'],
                                    is_correct=c_data['is_correct']
                                )
                        elif q_data['type'] == 'short_answer':
                            # For short answer questions, create a choice with the correct answer
                            Choice.objects.create(
                                question=question,
                                text=q_data.get('correct_answer', ''),
                                is_correct=True
                            )
                except json.JSONDecodeError as e:
                    messages.error(request, f'Error processing questions: {str(e)}')
                    return redirect('admin_quiz')
            
            # Update total questions count and points
            quiz.total_questions = quiz.questions.count()
            quiz.total_points = sum(question.points for question in quiz.questions.all())
            quiz.save()
            
            messages.success(request, 'Quiz saved and published successfully!')
            return HttpResponseRedirect(reverse('admin_quiz'))
        else:
            messages.error(request, 'Please correct the errors below.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        if quiz:
            form = QuizForm(instance=quiz)
        else:
            form = QuizForm(initial={
                'is_published': True,
                'is_active': True,
                'time_limit': 30
            })
    
    context = {
        'form': form,
        'subjects': Subject.objects.all(),
        'quiz': quiz
    }
    return render(request, 'panel/quiz-question-bank.html', context)

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
    return render(request, 'panel/quiz-detail.html', context)

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
    return render(request, 'panel/quiz-add-questions.html', context)

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
    return render(request, 'panel/exam-list.html', {'exams': exams})

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
    
    return render(request, 'panel/exam-question-bank.html', {'form': form})

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
    return render(request, 'panel/exam-detail.html', context)

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
    return render(request, 'panel/exam-question-bank.html', context)

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
    return render(request, 'panel/exam-edit-question.html', context)

@login_required
@user_passes_test(is_admin)
def exam_responses(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    results = ExamResult.objects.filter(
        exam=exam
    ).select_related(
        'student',
        'student__user',
        'exam'
    ).order_by('-date_taken')
    
    context = {
        'exam': exam,
        'results': results
    }
    return render(request, 'panel/exam-responses.html', context)

@login_required
@user_passes_test(is_admin)
def grade_exam(request, exam_id, result_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    result = get_object_or_404(ExamResult, pk=result_id)
    
    # Fetch all answers with related data
    answers = StudentAnswer.objects.filter(
        exam_result=result
    ).select_related(
        'question',
        'selected_choice',
        'question__exam'
    ).prefetch_related(
        'question__choices'
    ).order_by('question__order')
    
    # For multiple choice questions, set is_correct based on selected choice
    for answer in answers:
        if answer.question.question_type == 'multiple_choice':
            answer.is_correct = answer.selected_choice.is_correct if answer.selected_choice else False
            answer.points_earned = answer.question.points if answer.is_correct else 0
    
    if request.method == 'POST':
        for answer in answers:
            if answer.question.question_type == 'short_answer':
                is_correct = request.POST.get(f'correct_{answer.id}') == 'true'
                answer.is_correct = is_correct
                answer.points_earned = answer.question.points if is_correct else 0
                answer.feedback = request.POST.get(f'feedback_{answer.id}', '')
                answer.save()
        
        # Update total score
        total_score = sum(answer.points_earned for answer in answers)
        result.score = total_score
        result.is_graded = True
        result.save()
        
        messages.success(request, 'Exam graded successfully!')
        return redirect('exam_responses', exam_id=exam_id)
    
    context = {
        'exam': exam,
        'result': result,
        'answers': answers
    }
    return render(request, 'panel/exam-student-response.html', context)

#student dashboard
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    attendance = AttendanceRecord.objects.filter(student=student).order_by('-date')[:5]
    quiz_results = QuizResult.objects.filter(student=student).order_by('-date_taken')[:5]
    exam_results = ExamResult.objects.filter(student=student).order_by('-date_taken')[:5]

    # Calculate attendance statistics
    total_classes = AttendanceRecord.objects.filter(student=student).count()
    present_count = AttendanceRecord.objects.filter(student=student, status='Present').count()
    absent_count = AttendanceRecord.objects.filter(student=student, status='Absent').count()
    late_count = AttendanceRecord.objects.filter(student=student, status='Late').count()
    
    # Calculate attendance percentage
    attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0

    context = {
        'student': student,
        'attendance': attendance,
        'quiz_results': quiz_results,
        'exam_results': exam_results,
        'total_classes': total_classes,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'attendance_percentage': attendance_percentage,
    }
    return render(request, 'student/dashboard.html', context)

#student profile
@login_required
@user_passes_test(is_student)
def student_profile(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    user = student.user
    if request.method == 'POST':
        # Update user fields
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip() or user.email
        phone = request.POST.get('phone', '').strip() or student.phone
        birthday = request.POST.get('birthday', '').strip() or student.birthday
        section = request.POST.get('section', '').strip() or student.section
        course = request.POST.get('course', '').strip() or student.course
        profile_picture = request.FILES.get('profile_picture')

        # Split full name into first and last name (simple split)
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            user.first_name = name_parts[0]
            user.last_name = ' '.join(name_parts[1:])
        elif len(name_parts) == 1:
            user.first_name = name_parts[0]
            user.last_name = user.last_name  # keep old last name

        user.email = email
        user.save()

        # Update student profile fields
        student.phone = phone
        student.section = section
        student.course = course
        if birthday:
            student.birthday = birthday
        if profile_picture:
            student.profile_picture = profile_picture
        student.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('student_profile')
    return render(request, 'student/profile.html', {'student': student})

#student attendance
@login_required
@user_passes_test(is_student)
def student_attendance(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    
    # Get filter parameters
    subject_filter = request.GET.get('subject')
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')

    # Base queryset
    records = AttendanceRecord.objects.filter(student=student).order_by('-date')

    # Apply filters
    if subject_filter:
        records = records.filter(subject_id=subject_filter)
    if date_filter:
        records = records.filter(date=date_filter)
    if status_filter:
        records = records.filter(status=status_filter)
    
    # Calculate statistics
    total_classes = records.count()
    present_count = records.filter(status='Present').count()
    absent_count = records.filter(status='Absent').count()
    late_count = records.filter(status='Late').count()
    
    # Calculate percentages
    present_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
    absent_percentage = (absent_count / total_classes * 100) if total_classes > 0 else 0
    late_percentage = (late_count / total_classes * 100) if total_classes > 0 else 0
    
    context = {
        'student': student,  # Add student to context
        'records': records,
        'subjects': Subject.objects.all(),
        'selected_subject': subject_filter,
        'selected_date': date_filter,
        'selected_status': status_filter,
        'total_classes': total_classes,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'present_percentage': present_percentage,
        'absent_percentage': absent_percentage,
        'late_percentage': late_percentage,
    }
    return render(request, 'student/attendance.html', context)

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
    
    # Create a dictionary of exam results keyed by exam ID
    exam_results_dict = {result.exam_id: result for result in exam_results}

    context = {
        'student': student,  # Add student to context
        'exams': exams,
        'exam_results': exam_results_dict,
        'taken_exam_ids': taken_exam_ids,
    }
    return render(request, 'student/exam.html', context)

@login_required
@user_passes_test(is_student)
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, is_published=True, is_active=True)
    student = get_object_or_404(StudentProfile, user=request.user)
    
    # Check if student has already taken this exam
    if ExamResult.objects.filter(exam=exam, student=student).exists():
        messages.warning(request, 'You have already taken this exam.')
        return redirect('student_exam')
    
    # Fetch questions with their choices
    questions = Question.objects.filter(
        exam=exam
    ).prefetch_related(
        'choices'
    ).order_by('order')
    
    context = {
        'exam': exam,
        'questions': questions
    }
    return render(request, 'student/exam-take.html', context)

@login_required
@user_passes_test(is_student)
def submit_exam(request, exam_id):
    if request.method == 'POST':
        exam = get_object_or_404(Exam, pk=exam_id)
        student = get_object_or_404(StudentProfile, user=request.user)
        
        # Check if student has already taken this exam
        if ExamResult.objects.filter(exam=exam, student=student).exists():
            messages.error(request, 'You have already taken this exam.')
            return redirect('student_exam')
        
        # Create a new exam result
        exam_result = ExamResult.objects.create(
            exam=exam,
            student=student,
            date_taken=timezone.now(),
            score=0,  # Initialize score to 0
            is_completed=True
        )
        
        # Process each question's answer
        total_score = 0
        for question in exam.questions.all():
            if question.question_type == 'multiple_choice':
                choice_id = request.POST.get(f'question_{question.id}')
                if choice_id:
                    choice = get_object_or_404(Choice, pk=choice_id)
                    is_correct = choice.is_correct
                    points_earned = question.points if is_correct else 0
                    StudentAnswer.objects.create(
                        exam_result=exam_result,
                        question=question,
                        selected_choice=choice,
                        is_correct=is_correct,
                        points_earned=points_earned
                    )
                    total_score += points_earned
            else:  # short_answer
                answer_text = request.POST.get(f'question_{question.id}')
                if answer_text:
                    StudentAnswer.objects.create(
                        exam_result=exam_result,
                        question=question,
                        answer_text=answer_text,
                        points_earned=0  # Initialize to 0, will be updated during grading
                    )
        
        # Update the exam result with the total score
        exam_result.score = total_score
        exam_result.save()
        
        messages.success(request, 'Exam submitted successfully!')
        return redirect('student_exam')
    
    return redirect('student_exam')

@login_required
@user_passes_test(is_student)
def exam_result(request, result_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    exam_result = get_object_or_404(ExamResult, pk=result_id, student=student)
    answers = StudentAnswer.objects.filter(
        exam_result=exam_result
    ).select_related(
        'question',
        'selected_choice',
        'question__exam'
    ).prefetch_related(
        'question__choices'
    ).order_by('question__order')
    
    context = {
        'exam_result': exam_result,
        'answers': answers
    }
    return render(request, 'student/exam-result.html', context)

@login_required
@user_passes_test(is_student)
def student_quiz(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    quizzes = Quiz.objects.filter(is_published=True, is_active=True)
    quiz_results = QuizResult.objects.filter(student=student)
    completed_quizzes = Quiz.objects.filter(
        quizresult__student=student,
        quizresult__is_completed=True
    ).distinct()

    context = {
        'student': student,
        'quizzes': quizzes,
        'quiz_results': quiz_results,
        'completed_quizzes': completed_quizzes,
    }
    return render(request, 'student/quiz.html', context)

@login_required
@user_passes_test(is_student)
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_published=True, is_active=True)
    student = get_object_or_404(StudentProfile, user=request.user)
    
    # Check if student has already taken the quiz
    existing_result = QuizResult.objects.filter(quiz=quiz, student=student).first()
    if existing_result and existing_result.is_completed:
        messages.warning(request, 'You have already completed this quiz.')
        return redirect('student_quiz')
    
    if request.method == 'POST':
        # Create or get quiz result
        quiz_result = existing_result or QuizResult.objects.create(
            quiz=quiz,
            student=student,
            total_points=quiz.total_points
        )
        
        # Process answers
        for question in quiz.questions.all():
            if question.question_type == 'multiple_choice':
                selected_choice_id = request.POST.get(f'choice_{question.id}')
                if selected_choice_id:
                    selected_choice = Choice.objects.get(pk=selected_choice_id)
                    StudentAnswer.objects.create(
                        quiz_result=quiz_result,
                        question=question,
                        selected_choice=selected_choice
                    )
            else:
                answer_text = request.POST.get(f'answer_{question.id}')
                if answer_text:
                    StudentAnswer.objects.create(
                        quiz_result=quiz_result,
                        question=question,
                        answer_text=answer_text
                    )
        
        quiz_result.is_completed = True
        quiz_result.date_submitted = timezone.now()
        quiz_result.save()
        
        messages.success(request, 'Quiz submitted successfully!')
        return redirect('student_quiz')
    
    context = {
        'quiz': quiz,
        'questions': quiz.questions.order_by('order')
    }
    return render(request, 'student/quiz-take.html', context)

@login_required
@user_passes_test(is_admin)
def quiz_responses(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    results = QuizResult.objects.filter(quiz=quiz, is_completed=True).select_related('student__user')
    
    context = {
        'quiz': quiz,
        'results': results
    }
    return render(request, 'panel/quiz-responses.html', context)

@login_required
@user_passes_test(is_admin)
def grade_quiz(request, quiz_id, result_id):
    quiz_result = get_object_or_404(QuizResult, pk=result_id, quiz_id=quiz_id)
    
    if request.method == 'POST':
        for answer in quiz_result.answers.all():
            if answer.question.question_type == 'short_answer':
                is_correct = request.POST.get(f'correct_{answer.id}') == 'true'
                answer.is_correct = is_correct
                answer.points_earned = answer.question.points if is_correct else 0
                answer.feedback = request.POST.get(f'feedback_{answer.id}', '')
                answer.save()
        
        quiz_result.is_graded = True
        quiz_result.save()
        
        messages.success(request, 'Quiz graded successfully!')
        return redirect('quiz_responses', quiz_id=quiz_id)
    
    context = {
        'quiz_result': quiz_result,
        'answers': quiz_result.answers.select_related('question', 'selected_choice').order_by('question__order')
    }
    return render(request, 'panel/quiz-student-response.html', context)

@login_required
@user_passes_test(is_admin)
def exam_question_bank(request, exam_id=None):
    if exam_id:
        exam = get_object_or_404(Exam, pk=exam_id)
    else:
        exam = None

    # Get all subjects ordered by name
    subjects = Subject.objects.all().order_by('name')
    print(f"Number of subjects: {subjects.count()}")
    print(f"Subjects: {[{'id': s.id, 'name': s.name} for s in subjects]}")

    if request.method == 'POST':
        if exam:
            form = ExamForm(request.POST, instance=exam)
        else:
            form = ExamForm(request.POST)
        
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.is_published = True
            exam.is_active = True
            exam.save()  # First save to get a primary key
            
            # Delete existing questions if editing
            if exam_id:
                exam.questions.all().delete()
            
            # Process questions if they exist in the request
            questions_data = request.POST.get('questions')
            if questions_data:
                try:
                    questions_data = json.loads(questions_data)
                    for q_data in questions_data:
                        question = Question.objects.create(
                            exam=exam,
                            question_type=q_data['type'],
                            content=q_data['text'],
                            points=q_data.get('points', 1),
                            order=q_data.get('order', 0)
                        )
                        
                        if q_data['type'] == 'multiple_choice':
                            for c_data in q_data['choices']:
                                Choice.objects.create(
                                    question=question,
                                    text=c_data['text'],
                                    is_correct=c_data['is_correct']
                                )
                        elif q_data['type'] == 'short_answer':
                            # For short answer questions, create a choice with the correct answer
                            Choice.objects.create(
                                question=question,
                                text=q_data.get('correct_answer', ''),
                                is_correct=True
                            )
                except json.JSONDecodeError as e:
                    messages.error(request, f'Error processing questions: {str(e)}')
                    return redirect('admin_exam')
            
            # Update total questions count and points
            exam.total_questions = exam.questions.count()
            exam.total_points = sum(question.points for question in exam.questions.all())
            exam.save()
            
            messages.success(request, 'Exam saved and published successfully!')
            return redirect('admin_exam')
        else:
            messages.error(request, 'Please correct the errors below.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        if exam:
            form = ExamForm(instance=exam)
        else:
            form = ExamForm(initial={
                'is_published': True,
                'is_active': True,
                'time_limit': 30
            })
    
    context = {
        'form': form,
        'subjects': subjects,
        'exam': exam
    }
    print(f"Context subjects: {[{'id': s.id, 'name': s.name} for s in context['subjects']]}")
    return render(request, 'panel/exam-question-bank.html', context)

@login_required
def student_quiz_list(request):
    # Get all active and published quizzes
    student = get_object_or_404(StudentProfile, user=request.user)
    quizzes = Quiz.objects.filter(is_active=True, is_published=True)
    
    # Get quizzes that the student has already completed
    completed_quizzes = Quiz.objects.filter(
        quizresult__student=student,
        quizresult__is_completed=True
    ).distinct()
    
    # Get pending quizzes (not completed)
    pending_quizzes = quizzes.exclude(
        quizresult__student=student,
        quizresult__is_completed=True
    )
    
    context = {
        'student': student,
        'quizzes': quizzes,
        'completed_quizzes': completed_quizzes,
        'pending_quizzes': pending_quizzes
    }
    return render(request, 'student/quiz.html', context)

@login_required
def quiz_take(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True, is_published=True)
    
    # Check if student has already taken this quiz
    if QuizResult.objects.filter(quiz=quiz, student=request.user.studentprofile, is_completed=True).exists():
        messages.error(request, 'You have already taken this quiz.')
        return redirect('student_quiz')
    
    # Get all questions for this quiz
    questions = Question.objects.filter(quiz=quiz).order_by('order')
    
    return render(request, 'student/quiz-take.html', {
        'quiz': quiz,
        'questions': questions
    })

@login_required
def submit_quiz(request, quiz_id):
    if request.method == 'POST':
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        student = get_object_or_404(StudentProfile, user=request.user)
        
        # Check if student has already taken this quiz
        if QuizResult.objects.filter(quiz=quiz, student=student, is_completed=True).exists():
            messages.error(request, 'You have already taken this quiz.')
            return redirect('student_quiz')
        
        # Create a new quiz result
        quiz_result = QuizResult.objects.create(
            quiz=quiz,
            student=student,
            is_completed=True,
            date_submitted=timezone.now(),
            total_points=quiz.total_points
        )
        
        # Process each question's answer
        total_score = 0
        for question in Question.objects.filter(quiz=quiz):
            if question.question_type == 'multiple_choice':
                choice_id = request.POST.get(f'question_{question.id}')
                if choice_id:
                    choice = get_object_or_404(Choice, pk=choice_id)
                    StudentAnswer.objects.create(
                        quiz_result=quiz_result,
                        question=question,
                        selected_choice=choice,
                        is_correct=choice.is_correct
                    )
                    if choice.is_correct:
                        total_score += question.points
            else:  # short_answer
                answer_text = request.POST.get(f'question_{question.id}')
                if answer_text:
                    StudentAnswer.objects.create(
                        quiz_result=quiz_result,
                        question=question,
                        answer_text=answer_text
                    )
        
        # Update the quiz result with the total score
        quiz_result.score = total_score
        quiz_result.save()
        
        messages.success(request, 'Quiz submitted successfully!')
        return redirect('student_quiz')
    
    return redirect('student_quiz')

@login_required
def quiz_result(request, quiz_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    try:
        quiz_result = QuizResult.objects.get(quiz_id=quiz_id, student=student)
        answers = StudentAnswer.objects.filter(quiz_result=quiz_result)
    except QuizResult.DoesNotExist:
        messages.error(request, "Quiz result not found or you haven't taken this quiz yet.")
        return redirect('student_quiz')
    
    return render(request, 'student/quiz-result.html', {
        'quiz_result': quiz_result,
        'answers': answers
    })

@login_required
def add_student(request):
    if request.method == 'POST':
        try:
            # Create user account
            user = CustomUser.objects.create_user(
                username=request.POST['student_number'],
                email=request.POST['email'],
                password=request.POST['password'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name']
            )
            
            # Create student profile
            student = StudentProfile.objects.create(
                user=user,
                student_number=request.POST['student_number'],
                section=request.POST['section']
            )
            
            messages.success(request, 'Student added successfully!')
            return redirect('admin_students')
        except Exception as e:
            messages.error(request, f'Error adding student: {str(e)}')
            return redirect('admin_students')
    return redirect('admin_students')

@login_required
def delete_student(request):
    if request.method == 'POST':
        try:
            student_number = request.POST['student_number']
            student = StudentProfile.objects.get(student_number=student_number)
            user = student.user
            
            # Delete student profile first
            student.delete()
            # Then delete user account
            user.delete()
            
            messages.success(request, 'Student deleted successfully!')
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Student not found!')
        except Exception as e:
            messages.error(request, f'Error deleting student: {str(e)}')
    return redirect('admin_students')

# Add new view for handling student approval
@login_required
@user_passes_test(is_admin)
def approve_student(request, student_id):
    if request.method == 'POST':
        try:
            student = get_object_or_404(StudentProfile, id=student_id)
            action = request.POST.get('action')
            
            if not action:
                messages.error(request, 'No action specified.')
                return redirect('admin_dashboard')
            
            if action == 'approve':
                # Set is_approved on StudentProfile
                student.is_approved = True
                student.save()
                
                # Ensure is_student is set on CustomUser
                user = student.user
                user.is_student = True
                user.save()
                
                messages.success(request, 'Student approved successfully.')
                return redirect('admin_dashboard')
                
            elif action == 'decline':
                # Delete the student profile and associated user
                user = student.user
                student.delete()
                user.delete()
                messages.success(request, 'Student registration has been declined and removed from the system.')
            else:
                messages.error(request, 'Invalid action specified.')
                return redirect('admin_dashboard')
                
            return redirect('admin_dashboard')
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Student not found.')
            return redirect('admin_dashboard')
        except Exception as e:
            print(f"Error in approve_student: {str(e)}")  # Add logging
            messages.error(request, 'An error occurred while processing the request.')
            return redirect('admin_dashboard')
    
    messages.error(request, 'Invalid request method.')
    return redirect('admin_dashboard')