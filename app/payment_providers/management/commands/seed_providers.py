from django.core.management.base import BaseCommand
from payment_providers.models import PaymentProvider


class Command(BaseCommand):
    help = "Populate the database with Qavaa and Ignite payment providers."

    def handle(self, *args, **options):
        providers = [
            {
                "name": "Qavaa",
                "code": "QAVAA",
                "is_active": True,
                "config": {"env": "production", "merchant_id": "qavaa_default_merchant"},
            },
            {
                "name": "Ignite",
                "code": "IGNITE",
                "is_active": False,
                "config": {"env": "sandbox", "client_key": "ignite_test_key"},
            },
        ]

        for provider_data in providers:
            provider, created = PaymentProvider.objects.get_or_create(
                code=provider_data["code"],
                defaults={
                    "name": provider_data["name"],
                    "is_active": provider_data["is_active"],
                    "config": provider_data["config"],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f" -> Created: '{provider.name}' ({provider.code})"))
            else:
                self.stdout.write(f" -> Already exists: '{provider.name}' ({provider.code})")

        self.stdout.write(self.style.SUCCESS("Qavaa and Ignite providers seeding completed!"))
