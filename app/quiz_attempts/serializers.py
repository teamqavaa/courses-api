from rest_framework import serializers

from quiz_answers.serializers import QuizAnswerSerializer

from .models import QuizAttempt


class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            'id',
            'quiz',
            'started_at',
            'completed_at',
            'is_completed',
            'answers',
        ]
        read_only_fields = ['started_at']
