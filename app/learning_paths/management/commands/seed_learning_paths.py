import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand

from categories.models import Category
from courses.models import Course
from learning_paths.models import LearningPath, PathOutcome, PathPrerequisite
from lessons.models import Lesson
from modules.models import Module


# Demo curriculum for the "Backend Developer" career path.
BACKEND_DEVELOPER_COURSES = [
    {
        "slug": "foundations-of-server-side-programming",
        "title": "Foundations of Server-Side Programming",
        "subtitle": "How servers, requests and responses really work",
        "description": "Build the mental model behind every backend: processes, sockets, HTTP semantics and clean server-side architecture.",
        "level": "beginner",
        "instructor": "Reza Ahmadi",
        "duration_minutes": 380,
        "rating": 4.8,
        "review_count": 1204,
        "price": "39.00",
        "original_price": "65.00",
        "cohort_label": "Limited cohort",
        "audience": "Developers who have shipped small scripts or frontend apps and want a solid mental model of how servers handle requests before touching a framework.",
        "downloadable_files_count": 12,
    },
    {
        "slug": "designing-restful-apis",
        "title": "Designing RESTful APIs",
        "subtitle": "Resources, verbs and versioning done right",
        "description": "Design predictable, well-versioned REST APIs that clients enjoy consuming.",
        "level": "intermediate",
        "instructor": "Nadia Kovacs",
        "duration_minutes": 585,
        "rating": 4.9,
        "review_count": 987,
        "price": "48.00",
        "original_price": "76.00",
        "cohort_label": "Limited cohort",
        "audience": "Backend developers who can build endpoints but want their APIs to stay predictable as teams, clients and traffic grow.",
        "downloadable_files_count": 18,
    },
    {
        "slug": "relational-databases-sql-mastery",
        "title": "Relational Databases & SQL Mastery",
        "subtitle": "Schema design, joins, indexes and query plans",
        "description": "Model relational schemas and write optimized SQL for real application workloads.",
        "level": "intermediate",
        "instructor": "Takashi Mori",
        "duration_minutes": 670,
        "rating": 4.7,
        "review_count": 762,
        "price": "52.00",
        "original_price": "84.00",
        "cohort_label": "Limited cohort",
        "audience": "Application developers who write SQL by hand but cannot yet read a query plan or defend a schema under review.",
        "downloadable_files_count": 15,
    },
    {
        "slug": "authentication-security-middleware",
        "title": "Authentication, Security & Middleware",
        "subtitle": "JWT, OAuth 2.0 and hardened request pipelines",
        "description": "Implement secure authentication flows and middleware pipelines for real traffic.",
        "level": "intermediate",
        "instructor": "Amara Diallo",
        "duration_minutes": 510,
        "rating": 4.8,
        "review_count": 541,
        "price": "45.00",
        "original_price": "72.00",
        "cohort_label": "Limited cohort",
        "audience": "Developers building multi-user products who must move from 'it logs in' to tokens, scopes and request pipelines that survive an audit.",
        "downloadable_files_count": 10,
    },
    {
        "slug": "deployment-production-operations",
        "title": "Deployment & Production Operations",
        "subtitle": "Docker, CI/CD, monitoring and safe releases",
        "description": "Ship services to production with Docker and CI/CD, then keep them observable.",
        "level": "advanced",
        "instructor": "Lena Hoffmann",
        "duration_minutes": 735,
        "rating": 4.9,
        "review_count": 389,
        "price": "56.00",
        "original_price": "89.00",
        "cohort_label": "Limited cohort",
        "audience": "Engineers whose code now runs somewhere real and who need containers, pipelines, alerts and rollback plans instead of Friday deploys.",
        "downloadable_files_count": 18,
    },
]

BACKEND_DEVELOPER_OUTCOMES = [
    "Design and build production-ready REST APIs",
    "Model relational schemas and write optimized SQL",
    "Implement secure authentication flows (JWT, OAuth 2.0)",
    "Deploy backend services using Docker and CI/CD",
    "Monitor, log, and debug live production systems",
    "Manage environment config and secrets safely",
]

BACKEND_DEVELOPER_PREREQUISITES = [
    "Comfort with any programming language",
    "Basic understanding of the web (HTTP, browsers)",
]

# Lesson-level outline for "Designing RESTful APIs".
# (module_slug, module_title, [(lesson_title, lesson_type, duration_minutes), ...])
REST_API_CURRICULUM = [
    (
        "resource-modeling",
        "Resource Modeling",
        [
            ("What makes an API RESTful", "video", 12),
            ("Resources, URIs and naming conventions", "video", 18),
            ("HTTP verbs beyond GET and POST", "video", 21),
            ("Resource modeling check", "quiz", 6),
        ],
    ),
    (
        "status-codes-and-errors",
        "Status Codes & Errors",
        [
            ("Status codes that mean something", "video", 16),
            ("Error responses clients can act on", "video", 19),
            ("Idempotency and safe retries", "video", 14),
            ("Contracts check", "quiz", 8),
        ],
    ),
    (
        "versioning-and-evolution",
        "Versioning & Evolution",
        [
            ("Why APIs break and how to avoid it", "video", 17),
            ("URL versioning vs header versioning", "video", 22),
            ("Deprecation without drama", "video", 15),
            ("Versioning check", "quiz", 7),
        ],
    ),
    (
        "documentation-and-consistency",
        "Documentation & Consistency",
        [
            ("OpenAPI as a design tool", "video", 20),
            ("Pagination, filtering and sorting conventions", "video", 24),
            ("Auditing a real API design", "video", 27),
            ("Final assessment", "quiz", 15),
        ],
    ),
]


class Command(BaseCommand):
    help = "Seeds the database with the default skill and career learning paths."

    def handle(self, *args, **options):
        paths_to_seed = [
            # Skill paths
            {
                "kind": "skill",
                "slug": "git-version-control",
                "title": "Git & Version Control",
                "description": "Master branching, merging, and collaborative workflows",
                "icon": "git",
                "duration_weeks": 3,
            },
            {
                "kind": "skill",
                "slug": "api-design-basics",
                "title": "API Design Basics",
                "description": "Design clean, consistent REST endpoints",
                "icon": "api",
                "duration_weeks": 4,
            },
            {
                "kind": "skill",
                "slug": "sql-fundamentals",
                "title": "SQL Fundamentals",
                "description": "Query, join, and shape relational data confidently",
                "icon": "sql",
                "duration_weeks": 5,
            },
            {
                "kind": "skill",
                "slug": "command-line-essentials",
                "title": "Command Line Essentials",
                "description": "Navigate and automate from the terminal",
                "icon": "cli",
                "duration_weeks": 2,
            },
            {
                "kind": "skill",
                "slug": "docker-basics",
                "title": "Docker Basics",
                "description": "Containerize and ship applications reliably",
                "icon": "docker",
                "duration_weeks": 4,
            },
            {
                "kind": "skill",
                "slug": "data-visualization",
                "title": "Data Visualization",
                "description": "Turn numbers into charts people actually read",
                "icon": "data-viz",
                "duration_weeks": 3,
            },
            {
                "kind": "skill",
                "slug": "testing-fundamentals",
                "title": "Testing Fundamentals",
                "description": "Write tests that catch real bugs",
                "icon": "testing",
                "duration_weeks": 4,
            },
            {
                "kind": "skill",
                "slug": "authentication-security-basics",
                "title": "Authentication & Security Basics",
                "description": "Implement login flows and protect user data",
                "icon": "security",
                "duration_weeks": 3,
            },
            # Career paths
            {
                "kind": "career",
                "slug": "backend-developer",
                "title": "Backend Developer",
                "description": "Build and deploy production-ready APIs and services",
                "icon": "backend",
                "duration_weeks": 12,
            },
            {
                "kind": "career",
                "slug": "frontend-developer",
                "title": "Frontend Developer",
                "description": "Ship accessible, responsive interfaces users trust",
                "icon": "frontend",
                "duration_weeks": 14,
            },
            {
                "kind": "career",
                "slug": "data-analyst",
                "title": "Data Analyst",
                "description": "Turn raw data into decisions leaders act on",
                "icon": "data",
                "duration_weeks": 10,
            },
            {
                "kind": "career",
                "slug": "cloud-engineer",
                "title": "Cloud Engineer",
                "description": "Automate infrastructure that scales without drama",
                "icon": "cloud",
                "duration_weeks": 16,
            },
            {
                "kind": "career",
                "slug": "cybersecurity-analyst",
                "title": "Cybersecurity Analyst",
                "description": "Detect, investigate and contain real-world threats",
                "icon": "security",
                "duration_weeks": 13,
            },
            {
                "kind": "career",
                "slug": "mobile-developer",
                "title": "Mobile Developer",
                "description": "Publish cross-platform apps to both app stores",
                "icon": "mobile",
                "duration_weeks": 9,
            },
        ]

        self.stdout.write(self.style.WARNING("Starting database seeding..."))

        for index, data in enumerate(paths_to_seed, start=1):
            # get_or_create keeps the command idempotent; order follows the seed list.
            obj, created = LearningPath.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "kind": data["kind"],
                    "title": data["title"],
                    "description": data["description"],
                    "icon": data["icon"],
                    "duration_weeks": data["duration_weeks"],
                    "order": index,
                    "is_active": True,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f" -> Created: '{obj.title}' ({obj.kind})")
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(f" -> Already exists: '{obj.title}' ({obj.kind})")
                )

        self.stdout.write(self.style.SUCCESS("Database seeding completed!"))
        self.seed_backend_developer_courses()

    def seed_backend_developer_courses(self):
        """Attach the demo curriculum to the Backend Developer career path."""
        path = LearningPath.objects.filter(slug="backend-developer").first()
        if path is None:
            self.stdout.write(
                self.style.NOTICE(" -> Skipping courses: 'backend-developer' path missing")
            )
            return

        category, _ = Category.objects.get_or_create(
            name="Backend Development",
            defaults={
                "slug": "backend-development",
                "description": "Server-side engineering: APIs, databases, security and operations.",
            },
        )
        instructor_id = uuid.uuid4()

        course_ids = []
        for data in BACKEND_DEVELOPER_COURSES:
            course, created = Course.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "category": category,
                    "instructor_id": instructor_id,
                    "title": data["title"],
                    "subtitle": data["subtitle"],
                    "description": data["description"],
                    "language": "english",
                    "level": data["level"],
                    "status": "published",
                    "price": Decimal(data["price"]),
                    "discount_price": Decimal("0.00"),
                    "thumbnail": "",
                    "promo_video_url": "",
                    "average_rating": data["rating"],
                    "total_reviews": data["review_count"],
                },
            )
            course_ids.append(course.id)
            state = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(f" -> {state} course: '{course.title}'")
            )

        path.courses.set(course_ids)

        if not path.outcomes.exists():
            for order, content in enumerate(BACKEND_DEVELOPER_OUTCOMES, start=1):
                PathOutcome.objects.create(path=path, order=order, content=content)
            self.stdout.write(self.style.SUCCESS(" -> Created 6 path outcomes"))
        if not path.prerequisites.exists():
            for order, content in enumerate(BACKEND_DEVELOPER_PREREQUISITES, start=1):
                PathPrerequisite.objects.create(path=path, order=order, content=content)
            self.stdout.write(self.style.SUCCESS(" -> Created 2 prerequisites"))

        self.seed_rest_api_curriculum()

    def seed_rest_api_curriculum(self):
        """Attach modules and lessons to the Designing RESTful APIs course."""
        course = Course.objects.filter(slug="designing-restful-apis").first()
        if course is None:
            self.stdout.write(
                self.style.NOTICE(" -> Skipping curriculum: 'designing-restful-apis' missing")
            )
            return

        lesson_count = 0
        for module_order, (module_slug, module_title, lessons) in enumerate(
            REST_API_CURRICULUM, start=1
        ):
            # Module slugs are globally unique; prefix keeps them collision-free.
            module, _ = Module.objects.get_or_create(
                slug=f"rest-api-{module_slug}",
                defaults={
                    "course": course,
                    "title": module_title,
                    "order": module_order,
                    "is_published": True,
                },
            )
            for lesson_order, (lesson_title, lesson_type, minutes) in enumerate(
                lessons, start=1
            ):
                Lesson.objects.update_or_create(
                    slug=f"rest-api-{module_slug}-{lesson_order:02d}",
                    defaults={
                        "module": module,
                        "title": lesson_title,
                        "description": "",
                        "lesson_type": (
                            Lesson.LessonType.VIDEO
                            if lesson_type == "video"
                            else Lesson.LessonType.QUIZ
                        ),
                        "duration_in_minutes": minutes,
                        "order": lesson_order,
                        "is_preview": lessons[0][0] == lesson_title and module_order == 1,
                        "is_published": True,
                    },
                )
                lesson_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f" -> Seeded {len(REST_API_CURRICULUM)} modules / {lesson_count} lessons"
                " for 'Designing RESTful APIs'"
            )
        )
