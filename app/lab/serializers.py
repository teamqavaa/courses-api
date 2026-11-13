from rest_framework import serializers

from .models import (
    Lab,
    LabObjective,
    Skill,
    SkillOutcome,
    SkillPrerequisite,
    UserProgress,
)


class SkillOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillOutcome
        fields = ['id', 'order', 'content']


class SkillPrerequisiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillPrerequisite
        fields = ['id', 'order', 'content']


class SkillSerializer(serializers.ModelSerializer):
    lab_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Skill
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'icon',
            'order',
            'is_active',
            'duration_weeks',
            'pace',
            'includes_certificate',
            'lab_count',
        ]


class SkillDetailSerializer(SkillSerializer):
    outcomes = SkillOutcomeSerializer(many=True, read_only=True)
    prerequisites = SkillPrerequisiteSerializer(many=True, read_only=True)
    labs = serializers.SerializerMethodField()

    class Meta(SkillSerializer.Meta):
        fields = SkillSerializer.Meta.fields + [
            'outcomes',
            'prerequisites',
            'labs',
        ]

    def get_labs(self, obj):
        return LabSerializer(
            obj.labs.filter(status=Lab.Status.PUBLISHED),
            many=True,
        ).data


class LabObjectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabObjective
        fields = [
            'id',
            'order',
            'title',
            'content',
            'hint',
            'starter_code',
        ]


class LabSerializer(serializers.ModelSerializer):
    objectives = LabObjectiveSerializer(many=True, read_only=True)
    skill_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Lab
        fields = [
            'id',
            'slug',
            'title',
            'description',
            'language',
            'status',
            'difficulty',
            'skills',
            'skill_slugs',
            'user_id',
            'author_name',
            'created_at',
            'updated_at',
            'starter_code',
            'objectives',
        ]

    def get_skill_slugs(self, obj):
        return [skill.slug for skill in obj.skills.all()]


class LabManageSerializer(LabSerializer):
    """Lab vu par son auteur ou un admin : ajoute l'email de l'auteur et le nombre d'étapes."""
    objectives_count = serializers.SerializerMethodField()

    class Meta(LabSerializer.Meta):
        fields = LabSerializer.Meta.fields + ['user_email', 'objectives_count']

    def get_objectives_count(self, obj):
        return len(obj.objectives.all())


class LabObjectiveWriteSerializer(serializers.Serializer):
    """Étape envoyée avec le lab : `id` présent = mise à jour, absent = création."""
    id = serializers.UUIDField(required=False)
    order = serializers.IntegerField(required=False, min_value=1)
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    hint = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    starter_code = serializers.CharField(required=False, allow_blank=True, default='')


class LabWriteSerializer(serializers.ModelSerializer):
    """
    Création / modification d'un lab. `objectives` (facultatif) remplace la liste des étapes :
    les étapes absentes sont supprimées, celles avec un `id` connu mises à jour, les autres créées.
    """
    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        required=False,
    )
    objectives = LabObjectiveWriteSerializer(many=True, required=False)

    class Meta:
        model = Lab
        fields = [
            'title',
            'description',
            'language',
            'status',
            'difficulty',
            'starter_code',
            'skills',
            'objectives',
        ]

    def create(self, validated_data):
        objectives = validated_data.pop('objectives', None)
        skills = validated_data.pop('skills', None)
        lab = Lab.objects.create(**validated_data)
        if skills is not None:
            lab.skills.set(skills)
        if objectives is not None:
            self._sync_objectives(lab, objectives)
        return lab

    def update(self, instance, validated_data):
        objectives = validated_data.pop('objectives', None)
        skills = validated_data.pop('skills', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if skills is not None:
            instance.skills.set(skills)
        if objectives is not None:
            self._sync_objectives(instance, objectives)
        return instance

    def _sync_objectives(self, lab, objectives):
        existing = {objective.id: objective for objective in lab.objectives.all()}
        kept = set()
        for position, data in enumerate(objectives, start=1):
            values = {
                'order': data.get('order') or position,
                'title': data['title'],
                'content': data['content'],
                'hint': data.get('hint') or None,
                'starter_code': data.get('starter_code') or '',
            }
            objective = existing.get(data.get('id'))
            if objective is None:
                objective = LabObjective.objects.create(lab=lab, **values)
            else:
                for field, value in values.items():
                    setattr(objective, field, value)
                objective.save()
            kept.add(objective.id)
        lab.objectives.exclude(id__in=kept).delete()


class LabStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Lab.Status.choices)


class SessionSaveRequestSerializer(serializers.Serializer):
    current_code = serializers.CharField(required=False, allow_blank=True)
    completed_steps = serializers.IntegerField(required=False, min_value=0)


class SessionGetResponseSerializer(serializers.Serializer):
    current_code = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField()
    last_active_at = serializers.DateTimeField(required=False, allow_null=True)


class SessionSaveResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    last_active_at = serializers.DateTimeField()


class OkSerializer(serializers.Serializer):
    ok = serializers.BooleanField()


class WeekDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    practiced = serializers.BooleanField()
    is_today = serializers.BooleanField()


class StatsSerializer(serializers.Serializer):
    labs_completed = serializers.IntegerField()
    hours_practiced = serializers.FloatField()
    current_streak = serializers.IntegerField()
    week = WeekDaySerializer(many=True)


class ProgressSerializer(serializers.Serializer):
    lab_id = serializers.UUIDField(required=False)
    status = serializers.CharField()
    attempts = serializers.IntegerField()
    completed_at = serializers.DateTimeField(required=False, allow_null=True)
    completed_steps = serializers.IntegerField()
    total_steps = serializers.IntegerField()
    progress_percent = serializers.IntegerField()


class ExecuteRequestSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=Lab.Language.choices)
    version = serializers.CharField(max_length=50)
    filename = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=100000)


class ExecuteResponseSerializer(serializers.Serializer):
    language = serializers.CharField(required=False)
    version = serializers.CharField(required=False)
    run = serializers.DictField(required=False)


class ExecuteErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class UserProgressSerializer(serializers.ModelSerializer):
    lab_id = serializers.UUIDField(source='lab.id', read_only=True)

    class Meta:
        model = UserProgress
        fields = [
            'lab_id',
            'status',
            'attempts',
            'completed_at',
            'seconds_practiced',
            'completed_steps',
            'started_at',
            'updated_at',
        ]


__all__ = [
    'ExecuteErrorSerializer',
    'ExecuteRequestSerializer',
    'ExecuteResponseSerializer',
    'LabManageSerializer',
    'LabObjectiveSerializer',
    'LabObjectiveWriteSerializer',
    'LabSerializer',
    'LabStatusSerializer',
    'LabWriteSerializer',
    'MessageSerializer',
    'OkSerializer',
    'ProgressSerializer',
    'SessionGetResponseSerializer',
    'SessionSaveRequestSerializer',
    'SessionSaveResponseSerializer',
    'SkillDetailSerializer',
    'SkillOutcomeSerializer',
    'SkillPrerequisiteSerializer',
    'SkillSerializer',
    'StatsSerializer',
    'UserProgressSerializer',
    'WeekDaySerializer',
]
