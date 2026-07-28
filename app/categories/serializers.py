from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    # Ce champ appelle récursivement le même serializer pour lister les enfants
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'parent',  # ID du parent lors de la création
            'subcategories',  # Arbre descendant
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_subcategories(self, obj):
        # On récupère les sous-catégories actives de l'objet courant
        active_subs = obj.subcategories.filter(is_active=True)
        # On les sérialise avec ce même serializer (récursion)
        serializer = CategorySerializer(active_subs, many=True, context=self.context)
        return serializer.data
