# app/payments/services.py
import logging
from django.db import transaction
from django.core.exceptions import ValidationError

from orders.models import Order
from payments.models import Payment, PaymentProvider
from enrollments.models import Enrollment  # Ajustez l'import selon le nom de votre modèle d'inscription

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
        Inicie une tentative de paiement auprès du prestataire choisi.
        """
        try:
            order = Order.objects.select_related('user').get(id=order_id)
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
        # (Pattern Strategy)
        payment_data = cls._dispatch_initiate_to_provider(provider_code, order, payment)

        # 3. Mettre à jour le paiement avec les identifiants renvoyés par la passerelle
        payment.transaction_reference = payment_data.get('transaction_reference')
        payment.client_secret = payment_data.get('client_secret')  # URL de redirection ou Token Client
        payment.save(update_fields=['transaction_reference', 'client_secret'])

        return payment

    @classmethod
    def process_webhook(cls, provider_code: str, request) -> bool:
        """
        Traite la notification asynchrone (Webhook) envoyée par le prestataire distant.
        """
        try:
            # 1. Extraire et vérifier la signature du Webhook
            payload, is_valid = cls._verify_and_parse_webhook(provider_code, request)
            if not is_valid:
                logger.warning(f"Signature Webhook invalide pour le prestataire {provider_code}")
                return False

            # 2. Extraire la référence de transaction et le statut du paiement depuis le payload
            tx_ref = payload.get('transaction_reference')
            is_successful = payload.get('is_successful', False)
            raw_response = payload.get('raw_data', {})

            if not tx_ref:
                logger.error(f"Référence de transaction manquante dans le Webhook {provider_code}")
                return False

            # 3. Exécuter la confirmation du paiement en base de données
            if is_successful:
                cls.fulfill_payment_success(tx_ref, raw_response)
            else:
                cls.fulfill_payment_failure(tx_ref, raw_response)

            return True

        except Exception as e:
            logger.exception(f"Erreur lors du traitement du Webhook {provider_code}: {str(e)}")
            return False

    @classmethod
    @transaction.atomic
    def fulfill_payment_success(cls, transaction_reference: str, raw_response: dict):
        """
        Règlement réussi :
        1. Marque le Payment comme SUCCESSFUL.
        2. Marque l'Order comme PAID.
        3. Crée les accès aux cours (Enrollment) pour l'étudiant.
        """
        try:
            payment = Payment.objects.select_related('order', 'order__user').get(
                transaction_reference=transaction_reference
            )
        except Payment.DoesNotExist:
            logger.error(f"Paiement introuvable pour la référence : {transaction_reference}")
            return

        # Éviter d'exécuter à nouveau si le Webhook est envoyé plusieurs fois (Idempotence)
        if payment.status == Payment.PaymentStatus.SUCCESSFUL:
            logger.info(f"Paiement #{payment.id} déjà validé précédemment.")
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
        user = order.user
        order_items = order.items.select_related('course').all()

        enrollments_to_create = []
        for item in order_items:
            # Vérifier que l'étudiant n'est pas déjà inscrit
            if not Enrollment.objects.filter(user=user, course=item.course).exists():
                enrollments_to_create.append(
                    Enrollment(
                        user=user,
                        course=item.course,
                        order=order
                    )
                )

        if enrollments_to_create:
            Enrollment.objects.bulk_create(enrollments_to_create)
            logger.info(f"{len(enrollments_to_create)} inscriptions créées pour l'utilisateur {user.email}")

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

    # ------------------------------------------------------------------
    # Méthodes privées d'adaptation aux prestataires (Pattern Strategy)
    # ------------------------------------------------------------------

    @classmethod
    def _dispatch_initiate_to_provider(cls, provider_code: str, order: Order, payment: Payment) -> dict:
        """
        Achemine la requête d'initialisation vers l'API du prestataire concerné (Stripe, Wave, OM, etc.).
        """
        if provider_code == PaymentProvider.ProviderCode.STRIPE:
            # Exemple de retour factice pour Stripe Checkout Session
            return {
                'transaction_reference': f"pi_stripe_{payment.id.hex[:12]}",
                'client_secret': f"https://checkout.stripe.com/pay/{payment.id}"
            }
        elif provider_code == PaymentProvider.ProviderCode.WAVE:
            # Exemple de retour factice pour Wave Launch URL
            return {
                'transaction_reference': f"wave_tx_{payment.id.hex[:12]}",
                'client_secret': f"https://wave.com/pay/checkout_{payment.id}"
            }
        else:
            raise NotImplementedError(f"Le prestataire {provider_code} n'est pas encore implémenté.")

    @classmethod
    def _verify_and_parse_webhook(cls, provider_code: str, request) -> tuple[dict, bool]:
        """
        Valide la signature cryptographique du Webhook et extrait un format unifié.
        """
        # Dans un environnement de production, vous vérifierez les entêtes HTTP
        # (ex: Stripe-Signature ou Wave-Signature) avec la clé secrète du prestataire.
        data = request.data if hasattr(request, 'data') else {}

        parsed_payload = {
            'transaction_reference': data.get('transaction_reference') or data.get('id'),
            'is_successful': data.get('status') in ['succeeded', 'successful', 'COMPLETED', 'SUCCESS'],
            'raw_data': data
        }
        return parsed_payload, True
