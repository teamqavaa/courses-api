from rest_framework import serializers

from .models import CourseProgress


class CourseProgressSerializer(serializers.ModelSerializer):
    # The dashboard joins progress rows against the course list by `course_id`,
    # and courses are keyed on their slug everywhere (CourseListItemSerializer).
    course_id = serializers.SlugRelatedField(
        slug_field='slug',
        read_only=True,
        source='course',
    )

    class Meta:
        model = CourseProgress
        fields = ['course_id', 'status', 'progress_percent', 'completed_at']
        read_only_fields = fields