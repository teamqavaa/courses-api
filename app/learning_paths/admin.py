from django.contrib import admin

from learning_paths.models import LearningPath, PathOutcome, PathPrerequisite


class PathOutcomeInline(admin.TabularInline):
    model = PathOutcome
    extra = 1
    readonly_fields = ['id', 'created_at']


class PathPrerequisiteInline(admin.TabularInline):
    model = PathPrerequisite
    extra = 1
    readonly_fields = ['id', 'created_at']


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'kind', 'icon', 'duration_weeks', 'pace', 'order', 'is_active', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ['kind', 'is_active']
    search_fields = ['title', 'description']
    filter_horizontal = ['courses']
    inlines = [
        PathOutcomeInline,
        PathPrerequisiteInline,
    ]
