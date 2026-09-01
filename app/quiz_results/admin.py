from django.contrib import admin

from quiz_results.models import Result


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'answer', 'is_correct', 'score', 'created_at']
    readonly_fields = ['id', 'created_at']
    list_filter = ['is_correct']
