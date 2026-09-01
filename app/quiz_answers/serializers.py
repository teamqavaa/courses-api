from rest_framework import serializers

from quiz_results.serializers import ResultSerializer

from .models import QuizAnswer


class QuizAnswerSerializer(serializers.ModelSerializer):
    result = ResultSerializer(read_only=True)

    class Meta:
        model = QuizAnswer
        fields = [
            'id',
            'attempt',
            'question',
            'option',
            'created_at',
            'result',
        ]
        read_only_fields = ['created_at']
