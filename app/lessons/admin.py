from django.contrib import admin
from .models import Lesson, LabActivity


class LabActivityInline(admin.TabularInline):
    model = LabActivity
    extra = 0
    fields = ['lab_id', 'title', 'order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'lesson_type', 'order', 'is_published']
    list_filter = ['lesson_type', 'is_published']
    search_fields = ['title']
    inlines = [LabActivityInline]


@admin.register(LabActivity)
class LabActivityAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'lab_id', 'title', 'order']
    list_filter = ['lesson']
