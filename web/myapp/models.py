from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

# Custom user model to handle role (admin, student)


class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)  # Make username optional

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Username not required for createsuperuser
    
    objects = CustomUserManager()  # Use the custom manager

# Student profile fields
class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=100, blank=True)
    student_number = models.CharField(max_length=20, unique=True)
    section = models.CharField(max_length=50)
    course = models.CharField(max_length=100, blank=True)
    birthday = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # New field for approval status
    date_registered = models.DateTimeField(default=timezone.now)  # Changed to use default instead of auto_now_add

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_number})"


# Subjects that students attend
class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Attendance model
class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date} - {self.status}"

# Assessment (Quiz or Exam)
class Assessment(models.Model):
    TYPE_CHOICES = (
        ('Quiz', 'Quiz'),
        ('Exam', 'Exam'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date = models.DateField()
    score = models.FloatField()
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} - {self.student} - {self.score}"

class Quiz(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    due_date = models.DateTimeField(null=True, blank=True)
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes")
    total_questions = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Exam(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    due_date = models.DateTimeField(null=True, blank=True)
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes")
    total_questions = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('short_answer', 'Short Answer'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    content = models.TextField()
    points = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.quiz:
            return f"Question {self.order} - {self.quiz.title}"
        elif self.exam:
            return f"Question {self.order} - {self.exam.title}"
        return f"Question {self.order}"

    class Meta:
        ordering = ['order']

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255, default='')
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['id']

class QuizResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    date_taken = models.DateTimeField(auto_now_add=True)
    date_submitted = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0)
    total_points = models.FloatField(null=True, blank=True)
    time_taken = models.IntegerField(help_text="Time taken in seconds", default=0)
    is_completed = models.BooleanField(default=False)
    is_graded = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.quiz.title} - {self.score}/{self.total_points}"

    def save(self, *args, **kwargs):
        if not self.total_points:
            self.total_points = self.quiz.total_points
        super().save(*args, **kwargs)

class ExamResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    date_taken = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)
    total_points = models.FloatField(null=True, blank=True)
    time_taken = models.IntegerField(help_text="Time taken in seconds", default=0)
    is_completed = models.BooleanField(default=False)
    is_graded = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.exam.title} - {self.score}/{self.total_points}"

    def save(self, *args, **kwargs):
        if not self.total_points:
            self.total_points = self.exam.total_points
        super().save(*args, **kwargs)

class StudentAnswer(models.Model):
    quiz_result = models.ForeignKey(QuizResult, on_delete=models.CASCADE, related_name='answers', null=True, blank=True)
    exam_result = models.ForeignKey(ExamResult, on_delete=models.CASCADE, related_name='answers', null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.FloatField(default=0)
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Answer for {self.question.content[:50]}..."

    def save(self, *args, **kwargs):
        if self.question.question_type == 'multiple_choice':
            self.is_correct = self.selected_choice.is_correct if self.selected_choice else False
            self.points_earned = self.question.points if self.is_correct else 0
        super().save(*args, **kwargs)
        # Update result score
        if self.quiz_result:
            self.quiz_result.score = sum(answer.points_earned for answer in self.quiz_result.answers.all())
            self.quiz_result.save()
        elif self.exam_result:
            self.exam_result.score = sum(answer.points_earned for answer in self.exam_result.answers.all())
            self.exam_result.save()