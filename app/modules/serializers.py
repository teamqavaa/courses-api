from rest_framework import serializers
from .models import Module


class ModuleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer léger retournant uniquement les métadonnées propres au Module.
    Utilisé pour la LECTURE (GET).
    """
    lessons_count = serializers.IntegerField(
        source='lessons.count',
        read_only=True,
        help_text="Nombre total de leçons dans ce module"
    )

    class Meta:
        model = Module
        fields = [  # noqa: RUF012
            'id',
            'course',
            'title',
            'slug',
            'description',
            'order',
            'is_published',
            'is_free',
            'lessons_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer utilisé pour la CRÉATION (POST) et la MODIFICATION (PUT/PATCH)
    par les utilisateurs ayant le rôle instructor ou admin.
    """
    class Meta:
        model = Module
        fields = [  # noqa: RUF012
            'id',
            'course',
            'title',
            'slug',
            'description',
            'order',
            'is_published',
            'is_free',
        ]
        read_only_fields = ['id']  # noqa: RUF012
