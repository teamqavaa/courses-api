from rest_framework import serializers
from modules.models import Module
from lessons.serializers import LessonDetailSerializer  # 🔑 Importez le serializer des leçons


class ModuleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer léger retournant les métadonnées et la liste des leçons associées.
    Utilisé pour la LECTURE (GET).
    """
    lessons_count = serializers.IntegerField(
        source='lessons.count',
        read_only=True,
        help_text="Nombre total de leçons dans ce module"
    )

    # 🔑 Ajout de la relation inverse pour imbriquer les leçons du module
    lessons = LessonDetailSerializer(many=True, read_only=True)

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
            'lessons',  # 🔑 Inclure le champ ici
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
            'resources',
            'title',
            'slug',
            'description',
            'order',
            'is_published',
            'is_free',
        ]
        read_only_fields = ['id']  # noqa: RUF012

