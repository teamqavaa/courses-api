import uuid
from django.db import models
from django.core.exceptions import ValidationError
from carts.models import Cart
from courses.models import Course


class CartItem(models.Model):
    """
    Modèle représentant une ligne individuelle dans le panier.
    Identifié par un UUID v4.
    Fait le pont entre un panier (Cart) et un cours (Course).
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Panier"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name="Cours"
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ajouté le"
    )

    class Meta:
        ordering = ['-added_at']
        verbose_name = "Élément du panier"
        verbose_name_plural = "Éléments du panier"
        # Empêche d'ajouter deux fois le même cours dans le même panier au niveau SQL
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'course'],
                name='unique_course_per_cart'
            )
        ]

    def __str__(self):
        return f"{self.course.title} (Panier: {self.cart.user_id})"

    @property
    def price(self):
        """
        Retourne le prix effectif du cours (base/promo du cours).
        Si un prix promotionnel (discount_price) existe sur le cours et est valide, il est prioritaire.
        """
        if getattr(self.course, 'discount_price', None) and self.course.discount_price > 0:
            return self.course.discount_price
        return self.course.price

    def clean(self):
        """
        Validations métier avant enregistrement en base de données :
        1. Ne pas ajouter un cours déjà acheté / inscrit (Enrollment actif).
        2. Ne pas ajouter un cours non publié ou archivé.
        """
        from enrollments.models import Enrollment

        # Validation 1 : Vérifier si l'utilisateur a déjà un accès actif au cours
        if Enrollment.objects.filter(user_id=self.cart.user_id, course=self.course, status='active').exists():
            raise ValidationError("Vous êtes déjà inscrit à ce cours.")

        # Validation 2 : Vérifier si le cours est accessible/publié
        if hasattr(self.course, 'status') and self.course.status != 'published':
            raise ValidationError("Ce cours n'est pas disponible à l'achat.")

    def save(self, *args, **kwargs):
        # Exécute la méthode clean() automatiquement à la sauvegarde
        self.full_clean()
        super().save(*args, **kwargs)
