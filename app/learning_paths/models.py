from django.db import models
from django.utils.text import slugify

from courses.models import Course


KIND_CHOICES = [
    ('skill', 'Skill Path'),
    ('career', 'Career Path'),
]

# Values must match the icon-name maps in the frontend dashboard.
ICON_CHOICES = [
    ('git', 'Git'),
    ('api', 'API'),
    ('sql', 'SQL'),
    ('cli', 'Command line'),
    ('docker', 'Docker'),
    ('data-viz', 'Data visualization'),
    ('testing', 'Testing'),
    ('security', 'Security'),
    ('backend', 'Backend'),
    ('frontend', 'Frontend'),
    ('data', 'Data'),
    ('cloud', 'Cloud'),
    ('mobile', 'Mobile'),
]


class LearningPath(models.Model):
    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        verbose_name='path kind',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='path title',
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name='slug',
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='path description',
    )
    icon = models.CharField(
        max_length=20,
        choices=ICON_CHOICES,
        blank=True,
        default='',
        verbose_name='icon',
    )
    duration_weeks = models.PositiveIntegerField(
        default=0,
        verbose_name='duration in weeks',
    )
    pace = models.CharField(
        max_length=50,
        blank=True,
        default='self-paced',
        verbose_name='pace',
    )
    includes_certificate = models.BooleanField(
        default=False,
        verbose_name='Includes certificate',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='display order',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
    )
    courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name='learning_paths',
        verbose_name='courses',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'learning path'
        verbose_name_plural = 'learning paths'
        ordering = ['order', 'title']

    # Auto-generate slug from title on first save so callers never need to provide one.
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_kind_display()}: {self.title}"


class PathBullet(models.Model):
    """Ordered text bullet attached to a learning path (outcomes, prerequisites)."""

    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='learning path',
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name='display order',
    )
    content = models.TextField(verbose_name='content')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['order', 'id']

    def __str__(self):
        return self.content[:50]


class PathOutcome(PathBullet):
    # Explicit related_name: the abstract '%(class)ss' would yield 'pathoutcomes',
    # while seed + serializer contract on 'outcomes'.
    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='outcomes',
        verbose_name='learning path',
    )

    class Meta(PathBullet.Meta):
        verbose_name = 'path outcome'
        verbose_name_plural = 'path outcomes'


class PathPrerequisite(PathBullet):
    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='prerequisites',
        verbose_name='learning path',
    )

    class Meta(PathBullet.Meta):
        verbose_name = 'path prerequisite'
        verbose_name_plural = 'path prerequisites'
