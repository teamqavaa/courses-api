# app/enrollments/serializers.py
from rest_framework import serializers
from .models import Enrollment
from courses.serializers import CourseSerializer

class EnrollmentSerializer(serializers.ModelSerializer):
    # Permet d'intégrer tous les détails du cours dans l'inscription (GET)
    course_details = CourseSerializer(source='course', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'course',          # Utilisé pour spécifier le cours à l'écriture (si besoin)
            'course_details',   # Utilisé pour afficher les détails du cours en lecture
            'enrolled_at',
            'last_accessed_at',
            'progress_percentage',
            'status'
        ]
        read_only_fields = [
            'id',
            'enrolled_at',
            'last_accessed_at',
            'progress_percentage',
            'status'
        ]
