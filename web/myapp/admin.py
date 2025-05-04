from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, StudentProfile, Subject, AttendanceRecord, 
    Assessment, Quiz, Exam, Question, Choice, QuizResult, ExamResult
)
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_student', 'is_admin']
    list_filter = ['is_student', 'is_admin']
    fieldsets = UserAdmin.fieldsets + (
        ('Roles', {'fields': ('is_student', 'is_admin')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Roles', {'fields': ('is_student', 'is_admin')}),
    )

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_number', 'section', 'birthday']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'student_number']
    list_filter = ['section']

class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'date', 'status']
    list_filter = ['status', 'date', 'subject']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_number']
    date_hierarchy = 'date'

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['content', 'question_type']
    list_filter = ['question_type']
    inlines = [ChoiceInline]

class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at']
    search_fields = ['title']

class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at']
    search_fields = ['title']

class QuizResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'date_taken', 'score']
    list_filter = ['date_taken', 'quiz']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_number']

class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'date_taken', 'score']
    list_filter = ['date_taken', 'exam']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_number']

class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(AttendanceRecord, AttendanceRecordAdmin)
admin.site.register(Assessment)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizResult, QuizResultAdmin)
admin.site.register(ExamResult, ExamResultAdmin)