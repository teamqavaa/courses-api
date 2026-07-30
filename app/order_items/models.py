import uuid
from django.db import models
from django.conf import settings
from courses.models import Course
from  orders.models import Order



class OrderItem(models.Model):
    """Ligne de commande individuelle (prix fige par cours)."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Commande"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name="Cours"
    )
    price_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix payé (figé)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )

    class Meta:
        verbose_name = "Élément de commande"
        verbose_name_plural = "Éléments de commande"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=['order', 'course'],
                name='unique_course_per_order'
            )
        ]

    def __str__(self):
        return f"{self.course.title} - {self.price_paid}"

