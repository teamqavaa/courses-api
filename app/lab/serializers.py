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
            'created_at',
            'starter_code',
            'objectives',
        ]

    def get_skill_slugs(self, obj):
        return [skill.slug for skill in obj.skills.all()]


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
    'LabObjectiveSerializer',
    'LabSerializer',
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
