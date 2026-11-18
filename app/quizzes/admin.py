from django.contrib import admin

from .models import Choice, Question, Quiz, QuizAttempt


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'pass_score', 'max_attempts', 'time_limit_min', 'created_by', 'created_at')
    search_fields = ('title', 'created_by')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('statement', 'quiz', 'type', 'points', 'order')
    list_filter = ('type',)
    search_fields = ('statement', 'quiz__title')
    inlines = [ChoiceInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'user_id', 'started_at', 'submitted_at', 'score', 'passed')
    list_filter = ('passed',)
    search_fields = ('user_id', 'quiz__title')
    readonly_fields = ('started_at',)
