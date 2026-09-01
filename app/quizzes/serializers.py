from rest_framework import serializers

from quiz_questions.serializers import QuestionSerializer

from .models import Quiz


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id',
            'type_quiz',
            'title',
            'description',
            'content_type',
            'object_id',
            'slug',
            'is_active',
            'created_at',
            'updated_at',
            'questions',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
