from django.contrib import admin

from quiz_answers.models import QuizAnswer


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'attempt', 'question', 'option', 'created_at']
    readonly_fields = ['id', 'created_at']
    list_filter = ['attempt', 'question']
