from rest_framework import serializers

from quiz_options.serializers import QuizOptionSerializer

from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    options = QuizOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'quiz',
            'type_question',
            'text',
            'order',
            'slug',
            'is_active',
            'created_at',
            'updated_at',
            'options',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
