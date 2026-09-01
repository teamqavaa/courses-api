from django.contrib import admin

from quiz_questions.models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'quiz', 'type_question', 'text', 'order', 'is_active', 'created_at', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_filter = ['is_active', 'quiz', 'type_question']
    search_fields = ['text']
