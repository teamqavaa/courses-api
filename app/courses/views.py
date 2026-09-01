# app/courses/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from decimal import Decimal

# Imports de vos modules d'authentification et de permissions locaux
from courses_type.authentication import LocalJWTAuthentication
from core.authentication import CustomJWTAuthentication
from core.permissions import IsInstructorOrAdmin
from courses.models import Course
from lessons.models import Lesson
from modules.models import Module
from categories.models import Category
from .serializers import CourseListItemSerializer, CourseSerializer


PUBLISHED = 'published'
DRAFT = 'draft'


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    # Utilise le champ 'slug' au lieu de la clé primaire (id/pk) pour les URLs de détail
    lookup_field = 'slug'

    # Vérifie les tokens RS256 émis par le SSO (certificat public) OU accepte
    # l'authentification simulée par en-têtes HTTP pour le développement local.
    authentication_classes = [CustomJWTAuthentication, LocalJWTAuthentication]

    # Intégration de la permission adaptée à votre SimulatedUser
    permission_classes = [IsInstructorOrAdmin]

    # Support des fichiers (upload) et du JSON classique
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        Optimisation de la requête (Eager Loading) :
        - select_related('category') pour la relation One-to-Many (clé étrangère simple)
        - prefetch_related pour les relations utilisées par les sérialiseurs
          (tags, modules/leçons, bullets et ressources).
        """
        return Course.objects.all().select_related('category').prefetch_related(
            'tags',
            'modules',
            'modules__lessons',
            'resources',
            'highlights',
            'outcomes',
            'learning_points',
            'requirements',
        )

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """GET /api/courses/active/ - the published catalog for the dashboard."""
        courses = self.get_queryset().filter(status=PUBLISHED)
        serializer = CourseListItemSerializer(courses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='curriculum')
    def curriculum(self, request, *args, **kwargs):
        """GET /api/courses/{slug}/curriculum/ - published modules + lessons."""
        course = self.get_object()
        modules = (
            Module.objects.filter(course=course, is_published=True)
            .order_by('order')
            .prefetch_related('lessons')
        )

        module_data = []
        total_lessons = 0
        total_duration = 0
        for module in modules:
            lessons = sorted(
                [lesson for lesson in module.lessons.all() if lesson.is_published],
                key=lambda lesson: lesson.order,
            )
            total_lessons += len(lessons)
            total_duration += sum(lesson.duration_in_minutes for lesson in lessons)

            if not lessons:
                continue

            module_data.append({
                'id': str(module.pk),
                'title': module.title,
                'order': module.order,
                'lessons': [
                    {
                        'id': str(lesson.pk),
                        'title': lesson.title,
                        'order': lesson.order,
                        'lesson_type': lesson.lesson_type.lower(),
                        'duration_minutes': lesson.duration_in_minutes,
                    }
                    for lesson in lessons
                ],
            })

        return Response({
            'course_id': course.slug,
            'total_lessons': total_lessons,
            'total_duration_minutes': total_duration,
            'modules': module_data,
        })

    @action(detail=True, methods=['get'], url_path='path-context')
    def path_context(self, request, *args, **kwargs):
        """GET /api/courses/{slug}/path-context/ - the learning paths a course belongs to."""
        from learning_paths.models import LearningPath

        course = self.get_object()
        paths = LearningPath.objects.filter(courses=course, is_active=True).order_by('order', 'title')

        result = []
        for path in paths:
            active_courses = sorted(
                [item for item in path.courses.all() if item.status == PUBLISHED],
                key=lambda item: item.id,
            )
            try:
                position = next(
                    i for i, item in enumerate(active_courses, start=1)
                    if str(item.id) == str(course.id)
                )
            except StopIteration:
                position = None

            result.append({
                'id': path.slug,
                'title': path.title,
                'slug': path.slug,
                'kind': path.kind,
                'position': position,
                'total_courses': len(active_courses),
            })

        return Response({'paths': result})

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk(self, request):
        """
        POST /api/courses/bulk/ - import courses from the admin console.

        Body: {"mode": "create"|"upsert", "rows": [{"title": ..., "type": "..."}]}
        `type` is matched against Category name/slug; 'is_active' maps to
        status; legacy display fields (duration_minutes, rating, ...) are
        translated where the model stores them.
        Responds with {"created", "updated", "errors": [{row, field, message}]}.
        """
        language_map = {
            'en': 'english',
            'fr': 'french',
            'english': 'english',
            'french': 'french',
        }
        level_choices = {'beginner', 'intermediate', 'advanced'}
        payload = request.data or {}
        mode = payload.get('mode', 'create')
        rows = payload.get('rows') or []

        if mode not in {'create', 'upsert'}:
            return Response({'detail': 'mode must be "create" or "upsert"'}, status=400)

        created = 0
        updated = 0
        errors = []

        for index, raw in enumerate(rows, start=1):
            if not isinstance(raw, dict):
                errors.append({'row': index, 'field': 'row', 'message': 'Row must be an object.'})
                continue

            try:
                title = str(raw.get('title') or '').strip()
                if not title:
                    raise ValueError('title is required.')

                description = str(raw.get('description') or '').strip()
                if not description:
                    raise ValueError('description is required.')

                raw_type = str(raw.get('type') or '').strip() or str(raw.get('category') or '').strip()
                category = None
                if raw_type:
                    category = (
                        Category.objects.filter(name__iexact=raw_type).first()
                        or Category.objects.filter(slug=raw_type).first()
                    )
                if category is None:
                    raise ValueError(f'Unknown course type/category "{raw_type}".')

                language = language_map.get(str(raw.get('language') or '').strip().lower(), 'english')
                level = str(raw.get('level') or '').strip().lower()
                if level not in level_choices:
                    level = 'all'

                is_active = bool(raw.get('is_active', False))
                status_value = PUBLISHED if is_active else DRAFT

                discount = raw.get('original_price')
                # Legacy CSV "original_price" is the strikethrough (higher)
                # price. The model's discount_price must not exceed price, so
                # only keep it when it is genuinely below the selling price.
                try:
                    price_value = Decimal(str(raw.get('price', 0)))
                    discount_value = Decimal(str(discount or 0))
                    if discount_value <= 0 or discount_value >= price_value:
                        discount_value = Decimal('0.00')
                except Exception:  # noqa: BLE001 - malformed prices fall back to no discount
                    discount_value = Decimal('0.00')
                data = {
                    'category': str(category.pk),
                    'title': title,
                    'subtitle': str(raw.get('subtitle') or ''),
                    'description': description,
                    'language': language,
                    'level': level,
                    'status': status_value,
                    'price': str(raw.get('price', 0)),
                    'discount_price': str(discount_value),
                    'thumbnail': raw.get('thumbnail') or None,
                    'promo_video_url': raw.get('promo_video_url') or None,
                }
                if 'rating' in raw and raw.get('rating') not in (None, ''):
                    data['average_rating'] = float(raw['rating'])
                if 'review_count' in raw and raw.get('review_count') not in (None, ''):
                    data['total_reviews'] = int(raw['review_count'])

                slug = str(raw.get('slug') or '').strip()
                lookup_slug = slug or Course.objects.filter(title=title).values_list('slug', flat=True).first()

                if mode == 'upsert' and lookup_slug:
                    instance = Course.objects.filter(slug=lookup_slug).first()
                    if instance:
                        serializer = CourseSerializer(
                            instance, data=data, partial=True, context={'request': request}
                        )
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        updated += 1
                        continue

                serializer = CourseSerializer(data=data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.save()
                created += 1
            except Exception as exc:  # noqa: BLE001 - per-row errors must not abort the import
                field = getattr(exc, 'field', None) or 'data'
                message = str(exc.detail[0]) if getattr(exc, 'detail', None) and isinstance(exc.detail, list) else str(exc)
                errors.append({'row': index, 'field': field, 'message': message})

        return Response({'created': created, 'updated': updated, 'errors': errors})