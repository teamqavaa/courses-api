# app/resources/serializers.py
from rest_framework import serializers
from resources.models import Resource


class ResourceDetailSerializer(serializers.ModelSerializer):
    """Serializer pour la LECTURE (GET)."""
    file_size_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            'id',
            'course',
            'module',
            'lesson',
            'title',
            'description',
            'resource_type',
            'file',
            'external_url',
            'file_size_bytes',
            'file_size_formatted',
            'is_preview_allowed',
            'is_published',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_file_size_formatted(self, obj) -> str:
        """Retourne la taille en Mo ou Ko."""
        bytes_count = obj.file_size_bytes
        if not bytes_count:
            return "0 KB"
        if bytes_count >= 1024 * 1024:
            return f"{round(bytes_count / (1024 * 1024), 2)} MB"
        return f"{round(bytes_count / 1024, 2)} KB"


class ResourceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la CRÉATION / MODIFICATION (POST, PUT, PATCH)."""
    class Meta:
        model = Resource
        fields = [
            'id',
            'course',
            'module',
            'lesson',
            'title',
            'description',
            'resource_type',
            'file',
            'external_url',
            'is_preview_allowed',
            'is_published',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        course = attrs.get('course') or getattr(self.instance, 'course', None)
        module = attrs.get('module') or getattr(self.instance, 'module', None)
        lesson = attrs.get('lesson') or getattr(self.instance, 'lesson', None)
        file = attrs.get('file') or getattr(self.instance, 'file', None)
        external_url = attrs.get('external_url') or getattr(self.instance, 'external_url', None)

        if not any([course, module, lesson]):
            raise serializers.ValidationError("Rattachez la ressource à un cours, un module ou une leçon.")

        if not file and not external_url:
            raise serializers.ValidationError("Fournissez un fichier ou un lien externe.")

        return attrs
