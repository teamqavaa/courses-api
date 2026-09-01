from rest_framework import serializers
from .models import QuizOption


class QuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = [
            'id',
            'question',
            'text',
            'is_correct',
            'order',
            'created_at',
        ]
        read_only_fields = ['created_at']
