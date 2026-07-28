import uuid
from django.db import models
from django.utils.text import slugify


class TypeCourse(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="course type name"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True
    )
    description = models.CharField(
        blank=True,
        verbose_name="course type description"
    )
    is_virtual = models.BooleanField(
        default=True,
        verbose_name="Course is online?"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "course type"
        verbose_name_plural = "courses types"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        # Generate slug automatically
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
