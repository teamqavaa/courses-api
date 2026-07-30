import uuid
from django.db import models
from django.conf import settings


class Cart(models.Model):
    """
    Modèle représentant le panier global d'un utilisateur.
    Identifié par un UUID v4.
    Chaque utilisateur connecté possède un seul panier actif (OneToOneField).
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name="user"
    )
    # Lien vers le code promo / coupon actif dans le panier
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
        return f"Panier de {self.user.email}"

    @property
    def items_count(self) -> int:
        """Renvoie le nombre total de cours actuellement dans le panier."""
        return self.items.count()

    @property
    def subtotal_price(self):
        """
        Prix total brut du panier SANS l'effet du coupon du panier
        (prend en compte les promotions de base du cours).
        """
        return sum(item.price for item in self.items.all())

    @property
    def total_price(self):
        """
        Calcule le prix total NET du panier avec application du coupon :
        - Si coupon ciblé sur un cours : réduction uniquement sur ce cours.
        - Si coupon global : réduction sur l'ensemble du panier.
        """
        if not self.discount or not self.discount.is_valid:
            return self.subtotal_price

        # --- CAS 1 : COUPON CIBLÉ SUR UN COURS SPÉCIFIQUE ---
        if self.discount.course:
            total = 0
            for item in self.items.all():
                if item.course_id == self.discount.course_id:
                    discount_val = (item.price * self.discount.discount_percentage) / 100
                    total += (item.price - discount_val)
                else:
                    total += item.price
            return max(total, 0)

        # --- CAS 2 : COUPON GLOBAL SUR TOUT LE PANIER ---
        discount_val = (self.subtotal_price * self.discount.discount_percentage) / 100
        return max(self.subtotal_price - discount_val, 0)

    @property
    def discount_amount(self):
        """Montant total économisé grâce au code promo."""
        return self.subtotal_price - self.total_price

    def clear(self):
        """
        Vide l'ensemble des cours du panier et retire le coupon.
        Utile après la création de la commande (Checkout).
        """
        self.items.all().delete()
        self.discount = None
        self.save()
