from django.db import models
from django.utils.text import slugify


class TypeQuiz(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="quiz type name"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True
    )
    description = models.CharField(
        blank=True,
        verbose_name="quiz type description"
    )
    allowed_question_types = models.ManyToManyField(
        'question_types.TypeQuestion',
        blank=True,
        related_name='quiz_types',
        verbose_name='allowed question types',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "quiz type"
        verbose_name_plural = "quiz types"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
