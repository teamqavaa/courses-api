from django.contrib import admin

from .models import (
    Lab,
    LabObjective,
    LabSession,
    RateLimit,
    Skill,
    SkillOutcome,
    SkillPrerequisite,
    UserProgress,
)


class SkillOutcomeInline(admin.TabularInline):
    model = SkillOutcome
    extra = 0


class SkillPrerequisiteInline(admin.TabularInline):
    model = SkillPrerequisite
    extra = 0


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SkillOutcomeInline, SkillPrerequisiteInline]


class LabObjectiveInline(admin.TabularInline):
    model = LabObjective
    extra = 0
    fields = ['order', 'title', 'content', 'hint', 'starter_code']


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'language', 'difficulty', 'status']
    list_filter = ['status', 'language', 'difficulty']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['skills']
    inlines = [LabObjectiveInline]


@admin.register(LabSession)
class LabSessionAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'lab', 'status', 'last_active_at']
    list_filter = ['status']
    search_fields = ['user_id', 'lab__title']
    readonly_fields = [
        'user_id',
        'lab',
        'status',
        'current_code',
        'started_at',
        'last_active_at',
        'completed_at',
    ]


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = [
        'user_id',
        'lab',
        'status',
        'completed_steps',
        'seconds_practiced',
        'updated_at',
    ]
    list_filter = ['status']
    search_fields = ['user_id', 'lab__title']


@admin.register(RateLimit)
class RateLimitAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'request_count', 'window_start', 'updated_at']
    search_fields = ['user_id']
