from rest_framework import serializers
from .models import TypeQuiz


class TypeQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeQuiz
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'allowed_question_types',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
