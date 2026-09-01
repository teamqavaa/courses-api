from django.contrib import admin

from quiz_attempts.models import QuizAttempt


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'quiz', 'is_completed', 'started_at', 'completed_at']
    readonly_fields = ['id', 'started_at']
    list_filter = ['is_completed', 'quiz']
