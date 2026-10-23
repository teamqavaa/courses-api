import uuid

from django.db import models

from .slugs import make_unique_slug


class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, default='')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    duration_weeks = models.PositiveIntegerField(default=0)
    pace = models.CharField(max_length=50, blank=True, default='self-paced')
    includes_certificate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class SkillOutcome(models.Model):
    skill = models.ForeignKey(
        Skill,
        related_name='outcomes',
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=1)
    content = models.TextField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.content[:80]


class SkillPrerequisite(models.Model):
    skill = models.ForeignKey(
        Skill,
        related_name='prerequisites',
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=1)
    content = models.TextField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.content[:80]


class Lab(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    class Difficulty(models.TextChoices):
        GUIDED = 'guided', 'Guided'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    class Language(models.TextChoices):
        PYTHON = 'python', 'Python'
        PHP = 'php', 'PHP'
        TYPESCRIPT = 'typescript', 'TypeScript'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=False)
    description = models.TextField(null=True, blank=True)
    language = models.CharField(
        max_length=20,
        choices=Language.choices,
        default=Language.PYTHON,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.GUIDED,
    )
    starter_code = models.TextField(blank=True, default='')
    skills = models.ManyToManyField(Skill, blank=True, related_name='labs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            used_slugs = set(
                type(self).objects.values_list('slug', flat=True)
            )
            self.slug = make_unique_slug(self.title, used_slugs)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class LabObjective(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab = models.ForeignKey(
        Lab,
        related_name='objectives',
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    content = models.TextField()
    hint = models.TextField(blank=True, null=True)
    starter_code = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.lab.title} - {self.order}. {self.title}'


class LabSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        EXPIRED = 'expired', 'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    lab = models.ForeignKey(
        Lab,
        related_name='sessions',
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    current_code = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-last_active_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'lab'],
                name='lab_session_unique_user_lab',
            ),
        ]
        indexes = [
            models.Index(fields=['user_id', 'last_active_at']),
            models.Index(fields=['lab', 'status']),
        ]

    def __str__(self):
        return f'{self.user_id} - {self.lab.title}'


class UserProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    lab = models.ForeignKey(
        Lab,
        related_name='progress_records',
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    attempts = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(blank=True, null=True)
    seconds_practiced = models.PositiveIntegerField(default=0)
    completed_steps = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'lab'],
                name='lab_progress_unique_user_lab',
            ),
        ]
        indexes = [
            models.Index(fields=['user_id', 'updated_at']),
        ]

    def __str__(self):
        return f'{self.user_id} - {self.lab.title}'


class RateLimit(models.Model):
    user_id = models.CharField(max_length=255, primary_key=True)
    request_count = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-window_start']

    def __str__(self):
        return f'{self.user_id} ({self.request_count})'
