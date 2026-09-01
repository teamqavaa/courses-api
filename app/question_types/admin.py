from django.contrib import admin

from question_types.models import TypeQuestion


@admin.register(TypeQuestion)
class TypeQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'is_active', 'created_at', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
