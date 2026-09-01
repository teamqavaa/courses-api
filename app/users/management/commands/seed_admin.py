"""Seed a staff admin account so the admin UI can log in via the portal.

The migrated ``test@example.com`` rows are deliberately inactive, so nothing
useful logs in after a fresh migrate. This command creates (or updates) one
active staff/admin account.

Defaults are for local development only; override with the ADMIN_EMAIL and
ADMIN_PASSWORD environment variables in real environments.
"""

import os

from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):
    help = "Create or update a staff admin account for the admin UI."

    def handle(self, *args, **options):
        email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()
        password = os.getenv("ADMIN_PASSWORD", "admin12345")

        user = User.objects.filter(email=email).first()
        created = user is None

        if created:
            user = User.objects.create_user(
                email=email,
                password=password,
                role=User.Role.ADMIN,
                is_staff=True,
                is_active=True,
                display_name="Admin",
            )
        else:
            changed = not user.is_staff or not user.check_password(password)
            if changed:
                user.role = User.Role.ADMIN
                user.is_staff = True
                user.is_active = True
                user.set_password(password)
                user.save()

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin account {action}: {email} (is_staff={user.is_staff}, "
                f"role={user.role})"
            )
        )