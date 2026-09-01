from rest_framework import serializers
from .models import TypeQuestion


class TypeQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeQuestion
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
