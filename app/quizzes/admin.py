from django.contrib import admin

from quizzes.models import Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type_quiz', 'content_type', 'object_id', 'is_active', 'created_at', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ['is_active', 'type_quiz']
    search_fields = ['title']
