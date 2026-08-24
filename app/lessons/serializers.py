# app/lessons/serializers.py
from rest_framework import serializers
from .models import Lesson


class LessonVideoSummarySerializer(serializers.Serializer):
    """
    Serializer léger en lecture seule pour exposer les données clés
    de la vidéo rattachée à la leçon.
    """
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    video_url = serializers.URLField(read_only=True)
    duration = serializers.IntegerField(read_only=True)
    provider = serializers.CharField(read_only=True)


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour la LECTURE (GET).
    Renvoie les métadonnées de la leçon ainsi que la vidéo rattachée.
    """
    video = LessonVideoSummarySerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = [  # noqa: RUF012
            'id',
            'module',
            'title',
            'slug',
            'description',
            'lesson_type',
            'duration_in_minutes',
            'order',
            'is_preview',
            'is_published',
            'video',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la CRÉATION (POST) et la MODIFICATION (PUT/PATCH).
    Dédié aux rôles instructor / admin.
    """
    class Meta:
        model = Lesson
        fields = [  # noqa: RUF012
            'id',
            'module',
            'title',
            'slug',
            'description',
            'lesson_type',
            'duration_in_minutes',
            'order',
            'is_preview',
            'is_published',
        ]
        read_only_fields = ['id']  # noqa: RUF012

    def validate(self, attrs):
        """
        Empêche les conflits d'ordre au sein d'un même module.
        """
        module = attrs.get('module')
        order = attrs.get('order')

        if not self.instance and module and order:
            if Lesson.objects.filter(module=module, order=order).exists():
                raise serializers.ValidationError({
                    "order": f"Une leçon avec l'ordre {order} existe déjà dans ce module."
                })

        return attrs
