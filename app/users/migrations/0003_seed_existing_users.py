"""Seed users carried over from the former Digital-Readiness-Lab identity DB.

The users below are the canonical accounts migrated from the live DRL database
during the platform merger. Each insert is idempotent: a row whose email (or
phone) already exists is skipped, so re-running `migrate` on a populated DB is
harmless. The password hashes carry over so existing accounts keep working.

The original live accounts were replaced here with anonymized placeholders.
Real user names, email addresses, phone numbers, and password hashes are not
committed to source control.
"""

import uuid

from django.db import migrations

USERS = [
    {
        "id": "9d2fcad3-0f3d-4ff1-9195-61ecef7effba",
        "full_name": "Test User",
        "display_name": "Tester",
        "bio": "Hello",
        "email": "test@example.com",
        "phone": None,
        "role": "student",
        "is_staff": False,
        "is_active": False,
        "is_superuser": False,
        "date_joined": "2026-07-07 07:14:14.161272+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "33d8d5a1-fb8b-4287-a9ee-7cb5f2ff825a",
        "full_name": "Phone User",
        "display_name": None,
        "bio": None,
        "email": None,
        "phone": "+15550111111",
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-07-07 07:15:36.180193+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "f63d4e0f-0b2c-4f04-8865-0667cf3f0702",
        "full_name": "Test Student",
        "display_name": None,
        "bio": None,
        "email": "student1@example.com",
        "phone": None,
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-07-07 07:49:55.465727+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "9cfd2c4d-6e99-456d-819d-79669e573ff0",
        "full_name": "Test User",
        "display_name": None,
        "bio": None,
        "email": None,
        "phone": "+15550122222",
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-07-07 07:52:45.937126+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "bc573f21-ce05-44b3-9f8c-581efdf181a1",
        "full_name": "Test Name",
        "display_name": None,
        "bio": None,
        "email": "name1@example.org",
        "phone": "+15550133333",
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-07-07 14:09:52.200464+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "3968e9d3-32ef-405e-a398-ff3d812b2420",
        "full_name": "Admin User",
        "display_name": "Admin",
        "bio": "Cool Kid",
        "email": "root@example.com",
        "phone": None,
        "role": "admin",
        "is_staff": True,
        "is_active": True,
        "is_superuser": True,
        "last_login": "2026-08-25 21:43:57.788886+00:00",
        "date_joined": "2026-07-09 14:31:23.35066+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "2e9f7f57-d7ee-40ad-b80e-96b32e000424",
        "full_name": "Test User",
        "display_name": None,
        "bio": None,
        "email": None,
        "phone": "+15550144444",
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-07-11 15:43:35.65493+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "65e8ac6a-8738-4593-a97b-afee9d27bbd6",
        "full_name": "Test User",
        "display_name": None,
        "bio": None,
        "email": "user8@example.com",
        "phone": None,
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-07-18 15:12:29.016537+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "6b1886d0-bf28-4bba-94b8-02dfc51fc6e7",
        "full_name": "Test User",
        "display_name": "Test",
        "bio": None,
        "email": "User8@example.com",
        "phone": "+15550155555",
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-08-26 11:59:45.889081+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "614a87d4-cf73-441c-a128-f816c8b62864",
        "full_name": "Test User",
        "display_name": None,
        "bio": None,
        "email": "user10@example.com",
        "phone": None,
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-08-28 13:47:38.605016+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
    {
        "id": "b7839849-5e6b-4b24-8a1c-7ee7e078911f",
        "full_name": "Test User",
        "display_name": "Test",
        "bio": None,
        "email": "user11@example.com",
        "phone": None,
        "role": "student",
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "date_joined": "2026-08-29 12:35:45.812346+00:00",
        "language": "en",
        "password": "pbkdf2_sha256$1200000$IjegWQA3aU13QIuwhREleg==$AuZZnbQSNzfNIkfvNWnbbfMvpD04KU2lNf12JkmS3r8=",
    },
]


def seed_users(apps, schema_editor):
    User = apps.get_model("users", "User")
    for spec in USERS:
        email = (spec.get("email") or "").strip().lower() or None
        phone = spec.get("phone")
        if email and User.objects.filter(email__iexact=email).exists():
            continue
        if phone and User.objects.filter(phone=phone).exists():
            continue
        User.objects.create(
            id=uuid.UUID(spec["id"]),
            password=spec["password"],
            last_login=spec.get("last_login"),
            is_superuser=spec.get("is_superuser", False),
            full_name=spec.get("full_name"),
            display_name=spec.get("display_name"),
            bio=spec.get("bio"),
            email=email,
            phone=phone,
            language=spec.get("language", "en"),
            role=spec.get("role", "student"),
            is_active=spec.get("is_active", True),
            is_staff=spec.get("is_staff", False),
            date_joined=spec["date_joined"],
        )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_email_case_insensitive_unique"),
    ]

    operations = [
        migrations.RunPython(seed_users, migrations.RunPython.noop),
    ]
