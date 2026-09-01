from django.contrib import admin

from requirements.models import CourseRequirement


@admin.register(CourseRequirement)
class CourseRequirementAdmin(admin.ModelAdmin):
    list_display = ['id', 'course', 'order', 'content', 'created_at']
    readonly_fields = ['id', 'created_at']
    list_filter = ['course']
