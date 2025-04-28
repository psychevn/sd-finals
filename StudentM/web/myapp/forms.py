from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import inlineformset_factory
from .models import (
    CustomUser, StudentProfile, Subject, AttendanceRecord, 
    Assessment, Quiz, Exam, Question, Choice, QuizResult, ExamResult
)

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_admin')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_admin')

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['middle_name', 'student_number', 'section', 'phone', 'birthday']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']

class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'subject', 'date', 'status', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

class BulkAttendanceForm(forms.Form):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    status = forms.ChoiceField(choices=AttendanceRecord.STATUS_CHOICES)
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'subject', 'due_date', 'time_limit', 'total_points']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['content', 'question_type']

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']

# Create formsets for handling multiple choices per question
ChoiceFormSet = inlineformset_factory(
    Question, 
    Choice, 
    form=ChoiceForm, 
    extra=4, 
    can_delete=True
)

class QuizResultForm(forms.ModelForm):
    class Meta:
        model = QuizResult
        fields = ['student', 'quiz', 'score', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ['student', 'exam', 'score', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
