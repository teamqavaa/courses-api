from django.core.management.base import BaseCommand
from courses_type.models import TypeCourse  # ⚠️ Remplacez par le nom réel de votre app


class Command(BaseCommand):
    help = "Seeds the database with default course types directly."

    def handle(self, *args, **options):
        # Données de seed directes
        course_types_to_seed = [
            {
                "name": "E-learning",
                "description": "Online courses with pre-recorded videos and quizzes.",
                "is_virtual": True
            },
            {
                "name": "Live Classroom",
                "description": "Interactive online courses via live video streaming.",
                "is_virtual": True
            },
            {
                "name": "In-Person Workshop",
                "description": "Face-to-face practical courses in a physical classroom.",
                "is_virtual": False
            }
        ]

        self.stdout.write(self.style.WARNING("Starting database seeding..."))

        for data in course_types_to_seed:
            # get_or_create évite de dupliquer les types de cours si la commande est lancée plusieurs fois
            obj, created = TypeCourse.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "is_virtual": data["is_virtual"],
                    "is_active": True
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f" -> Created: '{obj.name}'")
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(f" -> Already exists: '{obj.name}'")
                )

        self.stdout.write(self.style.SUCCESS("Database seeding completed!"))

