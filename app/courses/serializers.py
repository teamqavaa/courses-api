import re
from decimal import Decimal
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import serializers

from courses.models import Course
from categories.models import Category
from categories.serializers import CategorySerializer
from tags.models import Tag
from tags.serializers import TagSerializer

# Imports des sérialiseurs des relations associées
from highlights.serializers import CourseHighlightDetailSerializer
from learning_points.serializers import CourseLearningPointDetailSerializer
from modules.serializers import ModuleDetailSerializer
from resources.serializers import ResourceDetailSerializer
from enrollments.models import Enrollment


class HybridFileField(serializers.FileField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            return data
        return super().to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None
        return str(value)


class CourseSerializer(serializers.ModelSerializer):
    # --- Relations en Lecture (GET) ---
    category_details = CategorySerializer(source='category', read_only=True)
    tags_details = TagSerializer(source='tags', many=True, read_only=True)

    # Relations imbriquées liées au cours (via related_name sur les modèles enfants)
    highlights = CourseHighlightDetailSerializer(source='course_highlights', many=True, read_only=True)
    learning_points = CourseLearningPointDetailSerializer(source='course_learning_points', many=True, read_only=True)
    modules = ModuleDetailSerializer(many=True, read_only=True)
    resources = ResourceDetailSerializer(many=True, read_only=True)

    # Statut d'inscription dynamique pour l'utilisateur connecté
    is_enrolled = serializers.SerializerMethodField()

    # --- Relations en Écriture (POST/PUT/PATCH) ---
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
        write_only=True
    )

    thumbnail = HybridFileField(required=False, allow_null=True)
    promo_video_url = HybridFileField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'category',
            'category_details',
            'tags',
            'tags_details',
            'highlights',
            'learning_points',
            'modules',
            'resources',
            'user_id',
            'user_email',
            'user_roles',
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
            'is_enrolled',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'slug',
            'user_id',
            'user_email',
            'user_roles',
            'average_rating',
            'total_students',
            'total_reviews',
            'is_enrolled',
            'created_at',
            'updated_at'
        ]

    def get_is_enrolled(self, obj) -> bool:
        request = self.context.get('request')
        if not request:
            return False

        current_user_id = getattr(request, 'user_id', None)
        if not current_user_id and hasattr(request, 'user') and request.user.is_authenticated:
            current_user_id = getattr(request.user, 'sub', None) or str(request.user.id)

        if not current_user_id:
            return False

        return Enrollment.objects.filter(user_id=current_user_id, course=obj).exists()

    def validate(self, data):
        price = data.get('price')
        discount_price = data.get('discount_price', Decimal("0.00"))

        if price is not None and discount_price > price:
            raise serializers.ValidationError({
                "discount_price": "The discount price cannot be greater than the original price."
            })
        return data

    def _is_valid_url_or_path(self, value):
        if not value:
            return True
        url_pattern = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(value) or value.startswith('/'))

    def validate_thumbnail(self, value):
        if not isinstance(value, str):
            return value
        if value and not self._is_valid_url_or_path(value):
            raise serializers.ValidationError("The thumbnail must be a valid file upload, URL, or local path.")
        return value

    def validate_promo_video_url(self, value):
        if not isinstance(value, str):
            return value
        if value and not self._is_valid_url_or_path(value):
            raise serializers.ValidationError("The promo video URL must be a valid file upload, URL, or local path.")
        return value

    def _handle_file_upload(self, validated_data, field_name, subfolder):
        file_obj = validated_data.get(field_name)
        if file_obj and not isinstance(file_obj, str):
            file_path = f"courses/{subfolder}/{file_obj.name}"
            saved_path = default_storage.save(file_path, ContentFile(file_obj.read()))
            validated_data[field_name] = default_storage.url(saved_path)

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['user_id'] = getattr(request.user, 'sub', None) or str(request.user.id)
            validated_data['user_email'] = getattr(request.user, 'email', '')
            validated_data['user_roles'] = getattr(request.user, 'roles', [])
        else:
            raise serializers.ValidationError({
                "detail": "An authenticated user is required to create a course."
            })

        self._handle_file_upload(validated_data, 'thumbnail', 'thumbnails')
        self._handle_file_upload(validated_data, 'promo_video_url', 'videos')

        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._handle_file_upload(validated_data, 'thumbnail', 'thumbnails')
        self._handle_file_upload(validated_data, 'promo_video_url', 'videos')

        return super().update(instance, validated_data)
