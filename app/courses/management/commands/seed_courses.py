# app/courses/management/commands/seed_courses.py
import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from courses.models import Course
from categories.models import Category
from tags.models import Tag


class Command(BaseCommand):
    help = "Peuple la base de données avec des catégories, des tags et des cours de test."

    def handle(self, *args, **options):
        self.stdout.write("Début du peuplement de la base de données...")

        # 1. Nettoyage complet des anciennes données
        self.stdout.write("Nettoyage de la base de données existante...")
        Course.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()

        # 2. Création des tags de test
        self.stdout.write("Création des tags...")
        tags_list = [
            "Python", "Django", "React", "Frontend", "Backend",
            "Docker", "DevOps", "Kubernetes", "Figma", "UI/UX",
            "Design", "SEO", "Marketing", "SaaS"
        ]

        tags_dict = {}
        for tag_name in tags_list:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={"slug": slugify(tag_name)}
            )
            tags_dict[tag_name] = tag

        # 3. Création des catégories de test
        categories_data = [
            {"name": "Développement Web", "description": "Apprenez à coder des sites et applications modernes."},
            {"name": "Design & UI/UX", "description": "Maîtrisez les outils de design et l'expérience utilisateur."},
            {"name": "Business & Marketing", "description": "Lancez votre activité et trouvez vos premiers clients."},
        ]

        categories_dict = {}
        for cat in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat["name"],
                defaults={
                    "slug": slugify(cat["name"]),
                    "description": cat["description"]
                }
            )
            categories_dict[cat["name"]] = category
            if created:
                self.stdout.write(f"Catégorie créée : '{category.name}'")

        # ID instructeur simulé
        instructor_id = str(uuid.uuid4())

        # 4. Liste de cours réalistes à insérer (avec la correction "french" en minuscules)
        courses_data = [
            {
                "category": categories_dict["Développement Web"],
                "title": "Devenir Développeur Full-Stack avec React & Django",
                "subtitle": "La formation ultime pour maîtriser le frontend et le backend de A à Z.",
                "description": "Dans ce cours complet, vous allez apprendre à concevoir une API robuste avec Django REST Framework et à l'interfacer avec une interface dynamique en React. Idéal pour les profils juniors.",
                "language": "french",  # <--- CORRIGÉ : "French" -> "french"
                "level": "intermediate",
                "status": "published",
                "price": Decimal("199.99"),
                "discount_price": Decimal("99.99"),
                "thumbnail": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97",
                "promo_video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
                "average_rating": Decimal("4.8"),
                "total_students": 1420,
                "total_reviews": 312,
                "tags_to_add": ["Python", "Django", "React", "Frontend", "Backend"]
            },
            {
                "category": categories_dict["Développement Web"],
                "title": "Introduction à Docker et Kubernetes pour le DevOps",
                "subtitle": "Conteneurisez vos applications et orchestrez vos déploiements.",
                "description": "Découvrez les bases de Docker, comment écrire un Dockerfile optimisé et comment déployer vos applications multi-conteneurs en production avec Docker Compose et Kubernetes.",
                "language": "french",  # <--- CORRIGÉ : "French" -> "french"
                "level": "beginner",
                "status": "published",
                "price": Decimal("49.99"),
                "discount_price": Decimal("29.99"),
                "thumbnail": "https://images.unsplash.com/photo-1607799279861-4dd421887fb3",
                "promo_video_url": "https://www.w3schools.com/html/movie.mp4",
                "average_rating": Decimal("4.6"),
                "total_students": 840,
                "total_reviews": 110,
                "tags_to_add": ["Docker", "DevOps", "Kubernetes"]
            },
            {
                "category": categories_dict["Design & UI/UX"],
                "title": "Maîtriser Figma de débutant à pro",
                "subtitle": "Concevez de superbes interfaces web et mobiles modernes.",
                "description": "Figma est l'outil indispensable du designer d'interface. Apprenez le responsive design, le prototypage interactif, les systèmes de composants et le travail collaboratif.",
                "language": "french",  # <--- CORRIGÉ : "French" -> "french"
                "level": "beginner",
                "status": "published",
                "price": Decimal("89.99"),
                "discount_price": Decimal("0.00"),
                "thumbnail": "https://images.unsplash.com/photo-1611532736597-de2d4265fba3",
                "promo_video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
                "average_rating": Decimal("4.9"),
                "total_students": 2500,
                "total_reviews": 680,
                "tags_to_add": ["Figma", "UI/UX", "Design"]
            },
            {
                "category": categories_dict["Business & Marketing"],
                "title": "Stratégie Marketing Digital & SEO",
                "subtitle": "Dominez les résultats Google et convertissez vos visiteurs.",
                "description": "Une approche pratique du référencement naturel (SEO), de la rédaction web, du copywriting et de l'acquisition de trafic via les réseaux sociaux.",
                "language": "french",  # <--- CORRIGÉ : "French" -> "french"
                "level": "advanced",
                "status": "draft",
                "price": Decimal("149.99"),
                "discount_price": Decimal("119.99"),
                "thumbnail": "https://images.unsplash.com/photo-1460925895917-afdab827c52f",
                "promo_video_url": "https://www.w3schools.com/html/movie.mp4",
                "average_rating": Decimal("0.0"),
                "total_students": 0,
                "total_reviews": 0,
                "tags_to_add": ["SEO", "Marketing"]
            }
        ]

        # 5. Insertion des cours et association des tags
        for course_item in courses_data:
            course = Course.objects.create(
                category=course_item["category"],
                instructor_id=instructor_id,
                title=course_item["title"],
                slug=slugify(course_item["title"]),
                subtitle=course_item["subtitle"],
                description=course_item["description"],
                language=course_item["language"],
                level=course_item["level"],
                status=course_item["status"],
                price=course_item["price"],
                discount_price=course_item["discount_price"],
                thumbnail=course_item["thumbnail"],
                promo_video_url=course_item["promo_video_url"],
                average_rating=course_item["average_rating"],
                total_students=course_item["total_students"],
                total_reviews=course_item["total_reviews"]
            )

            tags_to_add = [tags_dict[name] for name in course_item["tags_to_add"] if name in tags_dict]
            course.tags.add(*tags_to_add)

            self.stdout.write(f"Cours créé : '{course.title}' avec {len(tags_to_add)} tags (Instructor: {instructor_id})")

        self.stdout.write(self.style.SUCCESS("Peuplement terminé avec succès !"))
