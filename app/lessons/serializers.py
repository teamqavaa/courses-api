from rest_framework import serializers
from lessons.models import Lesson
from videos.serializers import VideoReadPublicSerializer


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour la LECTURE (GET).
    Renvoie les métadonnées de la leçon ainsi que l'objet vidéo rattaché.
    """
    video = VideoReadPublicSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = [
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
        fields = [
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
        read_only_fields = ['id']

    def validate(self, attrs):
        """
        Empêche les conflits d'ordre au sein d'un même module.
        """
        module = attrs.get('module')
        order = attrs.get('order')

        # Lors de la création (pas d'instance) ou si l'ordre change en modification
        if module and order:
            queryset = Lesson.objects.filter(module=module, order=order)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError({
                    "order": f"Une leçon avec l'ordre {order} existe déjà dans ce module."
                })

        return attrs
