from django.contrib import admin

# Register your models here.
from .models import Enrollment, LessonProgress


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'course', 'progress_percentage', 'status', 'last_accessed_at')
    list_filter = ('status',)
    search_fields = ('user_id', 'course__title')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'position_seconds', 'is_completed', 'updated_at')
    list_filter = ('is_completed',)
