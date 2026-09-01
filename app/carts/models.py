import uuid
from django.db import models


class Cart(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    # Stocke le 'sub' extrait de l'access_token
    user_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="ID Utilisateur (sub)"
    )
    discount = models.ForeignKey(
        'discounts.Discount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts',
        verbose_name="Code promo appliqué"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )

    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
        ordering = ['-created_at']

    def __str__(self):
        return f"Panier de l'utilisateur {self.user_id}"

    @property
    def items_count(self) -> int:
        return self.items.count()

    @property
    def subtotal_price(self):
        return sum(item.price for item in self.items.all())

    @property
    def total_price(self):
        if not self.discount or not self.discount.is_valid:
            return self.subtotal_price
        if self.discount.course:
            total = 0
            for item in self.items.all():
                if item.course_id == self.discount.course_id:
                    discount_val = (item.price * self.discount.discount_percentage) / 100
                    total += (item.price - discount_val)
                else:
                    total += item.price
            return max(total, 0)
        discount_val = (self.subtotal_price * self.discount.discount_percentage) / 100
        return max(self.subtotal_price - discount_val, 0)

    @property
    def discount_amount(self):
        return self.subtotal_price - self.total_price

    def clear(self):
        self.items.all().delete()
        self.discount = None
        self.save()
