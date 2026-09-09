# app/payments/services.py
import logging
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from orders.models import Order
from payments.models import Payment, PaymentProvider
from enrollments.models import Enrollment
from carts.models import Cart

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service central gérant l'orchestration des paiements, la validation des webhooks
    et la livraison des accès aux cours (Enrollment).
    """

    @classmethod
    @transaction.atomic
    def initiate_payment(cls, order_id: str, provider_code: str) -> Payment:
        """
        Initie une tentative de paiement auprès du prestataire choisi.
        Si le prestataire est un mode automatique/test (comme QAVAA), valide instantanément le paiement.
        """
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise ValidationError("La commande spécifiée est introuvable.")

        try:
            provider = PaymentProvider.objects.get(code=provider_code, is_active=True)
        except PaymentProvider.DoesNotExist:
            raise ValidationError(f"Le prestataire de paiement '{provider_code}' est indisponible.")

        # 1. Créer la tentative de paiement en base de données (Statut PENDING)
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            amount=order.total_amount,
            status=Payment.PaymentStatus.PENDING
        )

        # 2. Appel au sous-service/adapter spécifique du prestataire pour générer l'URL ou la session
        payment_data = cls._dispatch_initiate_to_provider(provider_code, order, payment)

        # 3. Mettre à jour le paiement avec les identifiants renvoyés par la passerelle
        payment.transaction_reference = payment_data.get('transaction_reference')
        payment.client_secret = payment_data.get('client_secret')
        payment.save(update_fields=['transaction_reference', 'client_secret'])

        # 🟢 4. VALIDATION INSTANTANÉE POUR QAVAA (ET AUTRES PROVIDERS DE TEST)
        if provider_code in ["QAVAA", "MOCK", "TEST"]:
            logger.info(f"Prestataire automatique '{provider_code}' détecté : Validation instantanée du paiement #{payment.id}")

            fake_raw_response = {
                "status": "SUCCESS",
                "transaction_reference": payment.transaction_reference,
                "amount": str(payment.amount),
                "message": "Auto-validated by custom provider"
            }

            cls.fulfill_payment_success(
                transaction_reference=payment.transaction_reference,
                raw_response=fake_raw_response,
                amount_paid=payment.amount
            )

        return payment

    @classmethod
    def process_webhook(cls, provider_code: str, request) -> bool:
        """
        Traite la notification asynchrone (Webhook) envoyée par le prestataire distant.
        """
        try:
            payload, is_valid = cls._verify_and_parse_webhook(provider_code, request)
            if not is_valid:
                logger.warning(f"Signature ou structure Webhook invalide pour le prestataire {provider_code}")
                return False

            tx_ref = payload.get('transaction_reference')
            is_successful = payload.get('is_successful', False)
            amount_paid = payload.get('amount_paid')
            raw_response = payload.get('raw_data', {})

            if not tx_ref:
                logger.error(f"Référence de transaction manquante dans le Webhook {provider_code}")
                return False

            if is_successful:
                cls.fulfill_payment_success(tx_ref, raw_response, amount_paid)
            else:
                cls.fulfill_payment_failure(tx_ref, raw_response)

            return True

        except Exception as e:
            logger.exception(f"Erreur lors du traitement du Webhook {provider_code}: {str(e)}")
            return False

    @classmethod
    @transaction.atomic
    def fulfill_payment_success(cls, transaction_reference: str, raw_response: dict, amount_paid=None):
        """
        Règlement réussi :
        1. Vérifie l'existence et le montant du paiement.
        2. Marque le Payment comme SUCCESSFUL.
        3. Marque l'Order comme PAID.
        4. Crée les accès aux cours (Enrollment) pour l'étudiant.
        5. Vide le panier de l'utilisateur.
        """
        try:
            payment = Payment.objects.select_related('order').get(
                transaction_reference=transaction_reference
            )
        except Payment.DoesNotExist:
            logger.error(f"Paiement introuvable pour la référence : {transaction_reference}")
            return

        if payment.status == Payment.PaymentStatus.SUCCESSFUL:
            logger.info(f"Paiement #{payment.id} déjà validé précédemment.")
            return

        # VÉRIFICATION DE SÉCURITÉ : Contrôle du montant payé si fourni
        if amount_paid is not None:
            if Decimal(str(amount_paid)) < Decimal(str(payment.amount)):
                logger.error(f"Fraude potentielle : Montant payé ({amount_paid}) inférieur au montant de la commande ({payment.amount}) pour la référence {transaction_reference}")
                cls.fulfill_payment_failure(transaction_reference, raw_response)
                return

        # 1. Mise à jour du paiement
        payment.status = Payment.PaymentStatus.SUCCESSFUL
        payment.raw_response = raw_response
        payment.save(update_fields=['status', 'raw_response', 'updated_at'])

        # 2. Mise à jour de la commande
        order = payment.order
        order.status = Order.OrderStatus.PAID
        order.save(update_fields=['status', 'updated_at'])

        # 3. Inscription de l'étudiant à tous les cours de la commande (Enrollment)
        user_id = order.user_id
        order_items = order.items.select_related('course').all()

        enrollments_to_create = []
        for item in order_items:
            if not Enrollment.objects.filter(user_id=user_id, course=item.course).exists():
                enrollments_to_create.append(
                    Enrollment(
                        user_id=user_id,
                        course=item.course,
                        order=order
                    )
                )

        if enrollments_to_create:
            Enrollment.objects.bulk_create(enrollments_to_create)
            logger.info(f"{len(enrollments_to_create)} inscriptions créées pour l'utilisateur ID {user_id}")

        # 4. Vider le panier de l'utilisateur suite au paiement validé
        try:
            cart = Cart.objects.filter(user_id=user_id).first()
            if cart:
                cart.items.all().delete()
                cart.discount = None
                cart.save(update_fields=['discount'])
                logger.info(f"Panier vidé avec succès pour l'utilisateur ID {user_id} suite au paiement réussi.")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du panier pour l'utilisateur {user_id}: {str(e)}")

    @classmethod
    @transaction.atomic
    def fulfill_payment_failure(cls, transaction_reference: str, raw_response: dict):
        """
        Règlement échoué : marque le Payment et l'Order en FAILED.
        """
        try:
            payment = Payment.objects.select_related('order').get(
                transaction_reference=transaction_reference
            )
        except Payment.DoesNotExist:
            return

        if payment.status != Payment.PaymentStatus.PENDING:
            return

        payment.status = Payment.PaymentStatus.FAILED
        payment.raw_response = raw_response
        payment.save(update_fields=['status', 'raw_response', 'updated_at'])

        order = payment.order
        order.status = Order.OrderStatus.FAILED
        order.save(update_fields=['status', 'updated_at'])

    @classmethod
    def _dispatch_initiate_to_provider(cls, provider_code: str, order: Order, payment: Payment) -> dict:
        """
        Achemine la requête d'initialisation vers l'API du prestataire dynamique (QAVAA, IGNITE, etc.).
        """
        if provider_code == "QAVAA":
            return {
                'transaction_reference': f"qavaa_tx_{payment.id.hex[:12]}",
                'client_secret': f"http://localhost:3001/qavaa?order_id={order.id}"
            }
        elif provider_code == "IGNITE":
            return {
                'transaction_reference': f"ignite_tx_{payment.id.hex[:12]}",
                'client_secret': f"https://api.ignite.com/pay/checkout_{payment.id}"
            }
        else:
            raise NotImplementedError(f"Le prestataire {provider_code} n'est pas encore implémenté.")

    @classmethod
    def _verify_and_parse_webhook(cls, provider_code: str, request) -> tuple[dict, bool]:
        """
        Valide la structure et les informations clés du Webhook.
        """
        data = request.data if hasattr(request, 'data') else {}

        parsed_payload = {
            'transaction_reference': data.get('transaction_reference') or data.get('id') or data.get('reference'),
            'is_successful': data.get('status') in ['succeeded', 'successful', 'COMPLETED', 'SUCCESS', 'paid'],
            'amount_paid': data.get('amount') or data.get('total_amount') or data.get('value'),
            'raw_data': data
        }

        is_valid = bool(parsed_payload['transaction_reference'])

        return parsed_payload, is_valid
