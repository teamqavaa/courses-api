from django.db import transaction
from django.core.exceptions import ValidationError
from orders.models import Order
from order_items.models import OrderItem
from carts.models import Cart


class CheckoutService:
    """
    Service gérant la conversion d'un panier (Cart) en commande (Order).
    """

    @classmethod
    @transaction.atomic
    def create_order_from_cart(cls, cart: Cart) -> Order:
        """
        Transforme un Panier en Commande :
        1. Vérifie la validité du panier.
        2. Calcule les prix nets par cours (avec gestion des réductions).
        3. Crée l'Order en statut PENDING.
        4. Crée les OrderItem en figant les prix payés (Snapshot).
        5. Incrémente l'utilisation du coupon si présent.
        6. Vide le panier (supprime les CartItem).
        """
        cart_items = list(cart.items.select_related('course').all())

        if not cart_items:
            raise ValidationError("Impossible de créer une commande à partir d'un panier vide.")

        user_id = cart.user_id
        discount = cart.discount

        valid_discount = discount if (discount and getattr(discount, 'is_valid', False)) else None

        items_to_create = []
        total_amount = 0

        for item in cart_items:
            course = item.course

            base_price = (
                course.discount_price
                if (hasattr(course, 'discount_price') and course.discount_price)
                else course.price
            )
            price_paid = base_price

            if valid_discount:
                if valid_discount.course_id is None or valid_discount.course_id == course.id:
                    reduction = (base_price * valid_discount.discount_percentage) / 100
                    price_paid = max(base_price - reduction, 0)

            total_amount += price_paid
            items_to_create.append({
                'course': course,
                'price_paid': price_paid
            })

        subtotal = sum(
            (c.course.discount_price if hasattr(c.course, 'discount_price') and c.course.discount_price else c.course.price)
            for c in cart_items
        )
        discount_amount = max(subtotal - total_amount, 0)

        order = Order.objects.create(
            user_id=user_id,
            total_amount=total_amount,
            discount=valid_discount,
            discount_amount=discount_amount,
            status=Order.OrderStatus.PENDING
        )

        order_items = [
            OrderItem(
                order=order,
                course=data['course'],
                price_paid=data['price_paid']
            )
            for data in items_to_create
        ]
        OrderItem.objects.bulk_create(order_items)

        if valid_discount:
            valid_discount.used_count += 1
            valid_discount.save(update_fields=['used_count'])

        cart.items.all().delete()
        cart.discount = None
        cart.save(update_fields=['discount'])

        return order
