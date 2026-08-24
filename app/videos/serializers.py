from rest_framework import serializers
from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour la gestion CRUD des vidéos (Instructeur / Admin).
    """
    duration_in_minutes = serializers.SerializerMethodField(
        read_only=True,
        help_text="Durée calculée en minutes"
    )

    class Meta:
        model = Video
        fields = [  # noqa: RUF012
            'id',
            'lesson',
            'title',
            'provider',
            'video_url',
            'external_id',
            'thumbnail_url',
            'duration_in_seconds',
            'duration_in_minutes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_in_minutes']  # noqa: RUF012

    def get_duration_in_minutes(self, obj) -> int:
        return round(obj.duration_in_seconds / 60) if obj.duration_in_seconds else 0


class VideoReadPublicSerializer(serializers.ModelSerializer):
    """
    Serializer restreint pour la consultation par l'élève (GET).
    """
    class Meta:
        model = Video
        fields = [  # noqa: RUF012
            'id',
            'lesson',
            'title',
            'provider',
            'video_url',
            'thumbnail_url',
            'duration_in_seconds',
        ]
        read_only_fields = fields
