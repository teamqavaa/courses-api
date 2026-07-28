import re
from decimal import Decimal
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import serializers

from courses.models import Course
from categories.models import Category
# Importation du modèle et du sérialiseur depuis l'application 'tags'
from tags.models import Tag
from tags.serializers import TagSerializer


class CategorySimpleSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour afficher les détails essentiels de la catégorie
    lors de la récupération d'un cours (GET).
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class HybridFileField(serializers.FileField):
    """
    Champ personnalisé capable d'accepter soit un fichier téléversé (upload)
    soit une URL/chemin sous forme de texte brut.
    """
    def to_internal_value(self, data):
        # Si c'est une chaîne de caractères (URL ou chemin existant)
        if isinstance(data, str):
            return data
        # Si c'est un fichier brut, on laisse le comportement par défaut de validation de fichier de DRF
        return super().to_internal_value(data)

    def to_representation(self, value):
        # S'assure de renvoyer une chaîne de caractères propre (URL) dans le JSON de réponse
        if not value:
            return None
        return str(value)


class CourseSerializer(serializers.ModelSerializer):
    # Permet de lire les détails de la catégorie (ex: GET /api/courses/)
    category_details = CategorySimpleSerializer(source='category', read_only=True)

    # Utilisé uniquement pour l'écriture lors de la création ou mise à jour (POST/PUT/PATCH)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True
    )

    # --- LIEN AVEC L'APPLICATION TAGS ---
    # Pour afficher les objets Tags complets lors d'un GET
    tags_details = TagSerializer(source='tags', many=True, read_only=True)

    # Pour associer les tags via leurs IDs à l'écriture (POST/PUT/PATCH)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    # -------------------------------------

    # Utilisation du champ hybride personnalisé pour accepter l'upload ou le texte brut
    thumbnail = HybridFileField(required=False, allow_null=True)
    promo_video_url = HybridFileField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'category',
            'category_details',
            'tags',              # <-- AJOUTÉ : liste d'IDs pour l'écriture
            'tags_details',      # <-- AJOUTÉ : liste d'objets complets pour la lecture
            'instructor_id',
            'title',
            'slug',
            'subtitle',
            'description',
            'language',
            'level',
            'status',
            'price',
            'discount_price',
            'thumbnail',
            'promo_video_url',
            'average_rating',
            'total_students',
            'total_reviews',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'slug',
            'instructor_id',
            'average_rating',
            'total_students',
            'total_reviews',
            'created_at',
            'updated_at'
        ]

    def validate(self, data):
        """
        Validation globale : s'assure de la cohérence des tarifs.
        """
        # On utilise .get() avec des valeurs par défaut pour éviter des erreurs KeyErrors si les champs ne sont pas fournis (PATCH)
        price = data.get('price')
        discount_price = data.get('discount_price', Decimal("0.00"))

        if price is not None and discount_price > price:
            raise serializers.ValidationError({
                "discount_price": "The discount price cannot be greater than the original price."
            })

        return data

    def _is_valid_url_or_path(self, value):
        """
        Vérifie si la chaîne est une URL valide (HTTP/HTTPS) ou un chemin local.
        """
        if not value:
            return True

        url_pattern = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if url_pattern.match(value) or value.startswith('/'):
            return True

        return False

    def validate_thumbnail(self, value):
        # Si c'est un fichier téléversé réel, on ignore la validation de chaîne de caractères
        if not isinstance(value, str):
            return value

        if value and not self._is_valid_url_or_path(value):
            raise serializers.ValidationError(
                "The thumbnail must be a valid file upload, an absolute URL (http/https), or a valid local path."
            )
        return value

    def validate_promo_video_url(self, value):
        # Si c'est un fichier téléversé réel, on ignore la validation de chaîne de caractères
        if not isinstance(value, str):
            return value

        if value and not self._is_valid_url_or_path(value):
            raise serializers.ValidationError(
                "The promo video URL must be a valid file upload, an absolute URL (http/https), or a valid local path."
            )
        return value

    def _handle_file_upload(self, validated_data, field_name, subfolder):
        """
        Enregistre physiquement le fichier sur le serveur de stockage configuré par Django,
        puis remplace l'objet fichier binaire par l'URL d'accès sous forme de texte.
        """
        file_obj = validated_data.get(field_name)
        # Si c'est un fichier importé (et non une chaîne de caractères déjà en base)
        if file_obj and not isinstance(file_obj, str):
            # Construction d'un dossier structuré (ex: media/courses/thumbnails/mon_image.png)
            file_path = f"courses/{subfolder}/{file_obj.name}"
            # Sauvegarde physique via Django Storage API
            saved_path = default_storage.save(file_path, ContentFile(file_obj.read()))
            # Transformation en URL exploitable pour l'enregistrement du CharField
            validated_data[field_name] = default_storage.url(saved_path)

    def create(self, validated_data):
        # Récupération de l'ID instructeur via la session/request
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['instructor_id'] = request.user.id
        else:
            raise serializers.ValidationError({
                "detail": "An authenticated instructor is required to create a course."
            })

        # Processus de sauvegarde des fichiers physiques
        self._handle_file_upload(validated_data, 'thumbnail', 'thumbnails')
        self._handle_file_upload(validated_data, 'promo_video_url', 'videos')

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Processus de sauvegarde des fichiers physiques lors d'une modification (PUT/PATCH)
        self._handle_file_upload(validated_data, 'thumbnail', 'thumbnails')
        self._handle_file_upload(validated_data, 'promo_video_url', 'videos')

        return super().update(instance, validated_data)
