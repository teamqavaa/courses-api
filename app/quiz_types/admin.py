from django.contrib import admin

from quiz_types.models import TypeQuiz


@admin.register(TypeQuiz)
class TypeQuizAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'is_active', 'created_at', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
