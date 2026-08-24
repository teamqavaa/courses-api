# app/courses/serializers.py
from rest_framework import serializers
from outcomes.models import CourseOutcome


class CourseOutcomeDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour la LECTURE (GET).
    Utilisé pour afficher la liste des acquis et objectifs pédagogiques d'un cours.
    """
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True,
        help_text="Libellé lisible de la catégorie"
    )

    class Meta:
        model = CourseOutcome
        fields = [  # noqa: RUF012
            'id',
            'course',
            'description',
            'category',
            'category_display',
            'icon',
            'order',
            'is_highlighted',
            'is_published',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class CourseOutcomeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la CRÉATION (POST) et la MODIFICATION (PUT/PATCH).
    Réservé aux utilisateurs autorisés (Instructor / Admin).
    """
    class Meta:
        model = CourseOutcome
        fields = [  # noqa: RUF012
            'id',
            'course',
            'description',
            'category',
            'icon',
            'order',
            'is_highlighted',
            'is_published',
        ]
        read_only_fields = ['id']  # noqa: RUF012

    def validate(self, attrs):
        """
        Vérifie qu'il n'y a pas de conflit d'ordre pour un même cours lors de la création.
        """
        course = attrs.get('course')
        order = attrs.get('order')

        # Lors d'une création
        if not self.instance and course and order:
            if CourseOutcome.objects.filter(course=course, order=order).exists():
                raise serializers.ValidationError({
                    "order": f"Un objectif avec l'ordre {order} existe déjà pour ce cours."
                })

        return attrs
