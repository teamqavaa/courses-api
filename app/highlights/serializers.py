from rest_framework import serializers
from highlights.models import CourseHighlight


class CourseHighlightDetailSerializer(serializers.ModelSerializer):
    """Serializer pour la LECTURE (GET)."""
    class Meta:
        model = CourseHighlight
        fields = [  # noqa: RUF012
            'id',
            'course',
            'title',
            'description',
            'icon',
            'order',
            'is_published',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class CourseHighlightCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la CRÉATION / MODIFICATION (POST, PUT, PATCH)."""
    class Meta:
        model = CourseHighlight
        fields = [  # noqa: RUF012
            'id',
            'course',
            'title',
            'description',
            'icon',
            'order',
            'is_published',
        ]
        read_only_fields = ['id']  # noqa: RUF012

    def validate(self, attrs):
        course = attrs.get('course')
        order = attrs.get('order')

        if not self.instance and course and order:
            if CourseHighlight.objects.filter(course=course, order=order).exists():
                raise serializers.ValidationError({
                    "order": f"Un point fort avec l'ordre {order} existe déjà pour ce cours."
                })

        return attrs
