from rest_framework import serializers
from .models import TypeCourse

class TypeCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeCourse
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'is_virtual',
            'is_active',
            'created_at',
            'updated_at'
        ]
        # These fields are managed by Django/PostgreSQL, so we make them read-only
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
