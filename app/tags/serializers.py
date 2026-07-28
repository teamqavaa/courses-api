# app/courses/serializers.py
from rest_framework import serializers
from .models import Tag

class TagSerializer(serializers.ModelSerializer):
    """
    Sérialiseur isolé pour gérer la création, la lecture et la mise à jour des Tags.
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        # Le slug est généré automatiquement par la méthode save() du modèle,
        # on le protège donc en lecture seule pour l'API.
        read_only_fields = ['slug']
