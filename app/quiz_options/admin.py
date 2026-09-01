from django.contrib import admin

from quiz_options.models import QuizOption


@admin.register(QuizOption)
class QuizOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'text', 'is_correct', 'order', 'created_at']
    readonly_fields = ['id', 'created_at']
    list_filter = ['is_correct', 'question']
    search_fields = ['text']
