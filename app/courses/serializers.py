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

    # --- Dashboard shape (api_tables parity) ---
    # These read-only extras mirror the names the frontend dashboard expects
    # (see qi-sso-front/types/course.ts) without changing the existing API.
    is_active = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    instructor = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    original_price = serializers.SerializerMethodField()
    audience = serializers.SerializerMethodField()
    cohort_label = serializers.SerializerMethodField()
    downloadable_files_count = serializers.SerializerMethodField()
    highlights = serializers.SerializerMethodField()
    outcomes = serializers.SerializerMethodField()
    learning_points = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()

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
            # Dashboard shape extras
            'is_active',
            'type',
            'instructor',
            'duration_minutes',
            'rating',
            'review_count',
            'original_price',
            'audience',
            'cohort_label',
            'downloadable_files_count',
            'highlights',
            'outcomes',
            'learning_points',
            'requirements',
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

    def get_is_active(self, obj):
        return obj.status == 'published'

    def get_type(self, obj):
        return obj.category.slug if obj.category_id else None

    def get_instructor(self, obj):
        return ''

    def get_duration_minutes(self, obj):
        total = 0
        for module in obj.modules.all():
            if not module.is_published:
                continue
            for lesson in module.lessons.all():
                if lesson.is_published:
                    total += lesson.duration_in_minutes
        return total

    def get_rating(self, obj):
        return obj.average_rating if obj.average_rating > 0 else None

    def get_review_count(self, obj):
        return obj.total_reviews

    def get_original_price(self, obj):
        # A strike-through price only makes sense when a discount is applied.
        if obj.discount_price and obj.discount_price > 0 and obj.discount_price < obj.price:
            return f"{obj.price:.2f}"
        return None

    def get_audience(self, obj):
        return ''

    def get_cohort_label(self, obj):
        return ''

    def get_downloadable_files_count(self, obj):
        return sum(1 for r in obj.resources.all() if r.is_published)

    def get_highlights(self, obj):
        return [
            {'id': str(h.pk), 'course': str(obj.pk), 'order': h.order, 'content': h.title}
            for h in obj.highlights.all() if h.is_published
        ]

    def get_outcomes(self, obj):
        return [
            {'id': str(o.pk), 'course': str(obj.pk), 'order': o.order, 'content': o.description}
            for o in obj.outcomes.all() if o.is_published
        ]

    def get_learning_points(self, obj):
        return [
            {'id': str(lp.pk), 'course': str(obj.pk), 'order': lp.order, 'content': lp.title}
            for lp in obj.learning_points.all() if lp.is_published
        ]

    def get_requirements(self, obj):
        return [
            {'id': str(r.pk), 'course': str(obj.pk), 'order': r.order, 'content': r.content}
            for r in obj.requirements.all()
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


class CourseListItemSerializer(CourseSerializer):
    """
    Slim, dashboard-shaped course payload used by the catalog + learning path
    endpoints. `id` is the course *slug*: every dashboard URL (detail,
    curriculum, path-context, progress) is keyed on the slug, so the frontend's
    `summary.id` join with progress rows works regardless of the real PK type.
    """

    id = serializers.CharField(source='slug', read_only=True)

    class Meta(CourseSerializer.Meta):
        fields = [
            'id',
            'type',
            'title',
            'subtitle',
            'description',
            'language',
            'level',
            'slug',
            'is_active',
            'thumbnail',
            'instructor',
            'duration_minutes',
            'rating',
            'review_count',
            'price',
            'original_price',
            'cohort_label',
            'audience',
            'downloadable_files_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
