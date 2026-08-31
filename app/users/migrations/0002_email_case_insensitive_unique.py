from django.db import migrations, models
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Lower


def backfill_lowercase_emails(apps, schema_editor):
    """Lowercase stored emails, keeping the oldest row on case-variant pairs."""
    User = apps.get_model("users", "User")

    keep_pk = (
        User.objects.filter(email__iexact=OuterRef("email"))
        .order_by("date_joined", "pk")
        .values("pk")[:1]
    )
    User.objects.filter(email__isnull=False).exclude(pk__in=Subquery(keep_pk)).update(
        email=None
    )

    User.objects.filter(email__isnull=False).update(email=Lower("email"))


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_lowercase_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower("email"),
                name="users_user_email_unique_ci",
                condition=models.Q(email__isnull=False),
            ),
        ),
    ]
