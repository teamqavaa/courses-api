from rest_framework import serializers
from lessons.models import Lesson
from videos.serializers import VideoReadPublicSerializer
from lab.models import Lab


class LessonLabSerializer(serializers.ModelSerializer):
    """Résumé du lab d'une leçon LAB (lien vers /labs/<slug> côté front)."""

    class Meta:
        model = Lab
        fields = ['id', 'slug', 'title', 'language']
        read_only_fields = fields


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour la LECTURE (GET).
    Renvoie les métadonnées de la leçon ainsi que l'objet vidéo rattaché.
    """
    video = VideoReadPublicSerializer(read_only=True)
    lab_details = LessonLabSerializer(source='lab', read_only=True, allow_null=True)

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
            'content',
            'lab',
            'lab_details',
            'quiz',
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
            'content',
            'lab',
            'quiz',
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

        # Leçon LAB : lab obligatoire et publié (sinon 404 pour les apprenants) ; autre type : lab retiré
        lesson_type = attrs.get('lesson_type', getattr(self.instance, 'lesson_type', Lesson.LessonType.VIDEO))
        lab = attrs['lab'] if 'lab' in attrs else getattr(self.instance, 'lab', None)
        if lesson_type == Lesson.LessonType.LAB:
            if lab is None:
                raise serializers.ValidationError({"lab": "Une leçon de type LAB doit être rattachée à un lab."})
            if 'lab' in attrs and lab.status != Lab.Status.PUBLISHED:
                raise serializers.ValidationError({"lab": "Seul un lab publié peut être rattaché à une leçon."})
        elif lab is not None:
            attrs['lab'] = None

        # Leçon QUIZ : quiz facultatif (les leçons QUIZ existantes n'en ont pas), à soi, et libre ;
        # autre type : quiz retiré
        quiz = attrs['quiz'] if 'quiz' in attrs else getattr(self.instance, 'quiz', None)
        if lesson_type != Lesson.LessonType.QUIZ:
            if quiz is not None:
                attrs['quiz'] = None
        elif 'quiz' in attrs and quiz is not None:
            from quizzes.permissions import can_edit_quiz
            request = self.context.get('request')
            if request is not None and not can_edit_quiz(request.user, quiz):
                raise serializers.ValidationError({"quiz": "Vous ne pouvez rattacher que vos propres quiz."})
            used = Lesson.objects.filter(quiz=quiz).exclude(pk=getattr(self.instance, 'pk', None))
            if used.exists():
                raise serializers.ValidationError({"quiz": "Ce quiz est déjà rattaché à une autre leçon."})

        return attrs
