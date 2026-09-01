from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify

from quiz_types.models import TypeQuiz


class Quiz(models.Model):
    type_quiz = models.ForeignKey(
        TypeQuiz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quizzes',
        verbose_name='quiz type',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='quiz title',
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='quiz description',
    )
    # Polymorphic link: a quiz can belong to either a Module or a Course.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='content type',
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='object id',
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name='slug',
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='Active',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'quiz'
        verbose_name_plural = 'quizzes'
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
