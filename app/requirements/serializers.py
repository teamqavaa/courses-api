from rest_framework import serializers

from .models import CourseRequirement


class CourseRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRequirement
        fields = ['id', 'course', 'order', 'content']
