from django.apps import AppConfig


class EnrollmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enrollments'

    def ready(self):
        # Branche les receivers des signaux d'activité (core/signals.py)
        from . import receivers  # noqa: F401
