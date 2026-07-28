import uuid
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Category name"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True
    )
    description = models.TextField(
        blank=True,
        verbose_name="Category description"
    )
    # Relation récursive : pointe vers 'self'.
    # related_name="subcategories" permet de récupérer facilement les sous-catégories d'un parent.
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Parent Category"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        # Affiche le chemin complet (ex: "Développement > Python" au lieu de juste "Python")
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name
