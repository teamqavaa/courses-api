from django.db import models
from django.utils.text import slugify


class TypeQuestion(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="question type name"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True
    )
    description = models.CharField(
        blank=True,
        verbose_name="question type description"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "question type"
        verbose_name_plural = "question types"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
