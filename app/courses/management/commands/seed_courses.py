import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from courses.models import Course
from categories.models import Category
from tags.models import Tag
from highlights.models import CourseHighlight
from learning_points.models import CourseLearningPoint
from modules.models import Module
from lessons.models import Lesson
from resources.models import Resource
from videos.models import Video


class Command(BaseCommand):
    help = "Populates the database with categories, tags, 4 English courses, and YouTube video links."

    def handle(self, *args, **options):
        self.stdout.write("Starting complete database seeding...")

        # 1. Complete cleanup in reverse order of dependencies
        self.stdout.write("Cleaning up existing database...")
        Video.objects.all().delete()
        Resource.objects.all().delete()
        Lesson.objects.all().delete()
        Module.objects.all().delete()
        CourseLearningPoint.objects.all().delete()
        CourseHighlight.objects.all().delete()
        Course.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()

        # 2. Creation of tags
        self.stdout.write("Creating tags...")
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

        # 3. Creation of categories
        categories_data = [
            {"name": "Web Development", "description": "Learn to code modern websites and applications."},
            {"name": "Design & UI/UX", "description": "Master design tools and user experience principles."},
            {"name": "Business & Marketing", "description": "Launch your business and acquire your first customers."},
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

        instructor_id = str(uuid.uuid4())
        instructor_email = "expert.instructor@example.com"
        instructor_roles = ["instructor", "admin"]

        # Vos liens YouTube à distribuer sur les leçons
        youtube_links = [
            "https://www.youtube.com/watch?v=D1B_BkGHbqs",
            "https://www.youtube.com/watch?v=zu_lcO7Yueo",
            "https://www.youtube.com/watch?v=2TlIg3VokY8",
        ]
        video_counter = 0

        # 4. List of 4 rich courses to insert
        courses_data = [
            {
                "category": categories_dict["Web Development"],
                "title": "Become a Full-Stack Developer with React & Django",
                "subtitle": "The ultimate masterclass to conquer frontend and backend development from scratch.",
                "description": "In this comprehensive course, you will learn how to design a robust API using Django REST Framework and interface it with a dynamic React interface.",
                "language": "english",
                "level": "intermediate",
                "status": "published",
                "price": Decimal("199.99"),
                "discount_price": Decimal("99.99"),
                "thumbnail": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97",
                "promo_video_url": "https://www.youtube.com/watch?v=D1B_BkGHbqs",
                "average_rating": Decimal("4.8"),
                "total_students": 1420,
                "total_reviews": 312,
                "tags_to_add": ["Python", "Django", "React", "Frontend", "Backend"],
                "highlights": [
                    "Over 40 hours of hands-on video tutorials",
                    "Production-ready real-world projects",
                    "Direct support from the instructor"
                ],
                "learning_points": [
                    "Master Django REST Framework from zero",
                    "Build reactive interfaces using React and Vite",
                    "Configure secure JWT authentication"
                ],
                "modules": [
                    {
                        "title": "Module 1: Introduction and Setup",
                        "description": "Setting up the complete development environment.",
                        "order": 1,
                        "lessons": [
                            {"title": "Installing development tools", "duration_in_minutes": 15, "order": 1},
                            {"title": "Django project structure", "duration_in_minutes": 25, "order": 2}
                        ]
                    },
                    {
                        "title": "Module 2: Building the Backend API",
                        "description": "Developing models and secure endpoints.",
                        "order": 2,
                        "lessons": [
                            {"title": "Configuring DRF", "duration_in_minutes": 30, "order": 1},
                            {"title": "Serializers and Views", "duration_in_minutes": 45, "order": 2}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Complete Course Syllabus (PDF)", "file_url": "https://example.com/resources/complete-course.pdf", "type": Resource.ResourceTypeChoices.DOCUMENT},
                    {"title": "GitHub Repository Source Code", "file_url": "https://github.com/example/fullstack-repo", "type": Resource.ResourceTypeChoices.EXTERNAL_LINK}
                ]
            },
            {
                "category": categories_dict["Web Development"],
                "title": "Advanced DevOps & Docker Pipeline Mastery",
                "subtitle": "Automate deployment and scale your applications effortlessly.",
                "description": "Learn containerization, CI/CD pipelines, and orchestration with Docker and Kubernetes to ensure smooth enterprise-grade deployments.",
                "language": "english",
                "level": "advanced",
                "status": "published",
                "price": Decimal("249.99"),
                "discount_price": Decimal("129.99"),
                "thumbnail": "https://images.unsplash.com/photo-1618401471353-b98aedd04e11",
                "promo_video_url": "https://www.youtube.com/watch?v=zu_lcO7Yueo",
                "average_rating": Decimal("4.9"),
                "total_students": 850,
                "total_reviews": 145,
                "tags_to_add": ["Docker", "DevOps", "Kubernetes", "Backend"],
                "highlights": [
                    "Advanced Kubernetes cluster architectures",
                    "Continuous Integration workflows with GitHub Actions",
                    "Best practices for container security"
                ],
                "learning_points": [
                    "Containerize any legacy or modern application",
                    "Deploy scalable clusters on the cloud",
                    "Monitor infrastructure health efficiently"
                ],
                "modules": [
                    {
                        "title": "Module 1: Docker Essentials",
                        "description": "Understanding containers, images, and multi-stage builds.",
                        "order": 1,
                        "lessons": [
                            {"title": "Dockerfiles best practices", "duration_in_minutes": 20, "order": 1},
                            {"title": "Docker Compose orchestration", "duration_in_minutes": 35, "order": 2}
                        ]
                    }
                ],
                "resources": [
                    {"title": "DevOps Cheat Sheet", "file_url": "https://example.com/resources/devops-cheatsheet.pdf", "type": Resource.ResourceTypeChoices.DOCUMENT}
                ]
            },
            {
                "category": categories_dict["Design & UI/UX"],
                "title": "UI/UX Design Masterclass with Figma",
                "subtitle": "Design stunning, user-centric mobile and web interfaces.",
                "description": "Dive deep into user experience research, wireframing, interactive prototyping, and modern design systems using Figma.",
                "language": "english",
                "level": "beginner",
                "status": "published",
                "price": Decimal("149.99"),
                "discount_price": Decimal("79.99"),
                "thumbnail": "https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e",
                "promo_video_url": "https://www.youtube.com/watch?v=2TlIg3VokY8",
                "average_rating": Decimal("4.7"),
                "total_students": 2300,
                "total_reviews": 410,
                "tags_to_add": ["Figma", "UI/UX", "Design"],
                "highlights": [
                    "Design systems creation from scratch",
                    "Advanced Figma components and auto-layout",
                    "Real user testing strategies"
                ],
                "learning_points": [
                    "Build clickable interactive prototypes",
                    "Conduct effective user research interviews",
                    "Export assets for developers seamlessly"
                ],
                "modules": [
                    {
                        "title": "Module 1: Figma Fundamentals",
                        "description": "Getting comfortable with interface layout and frames.",
                        "order": 1,
                        "lessons": [
                            {"title": "Navigating Figma Workspace", "duration_in_minutes": 10, "order": 1},
                            {"title": "Auto Layout mastery", "duration_in_minutes": 30, "order": 2}
                        ]
                    }
                ],
                "resources": [
                    {"title": "UI Kit Figma Template", "file_url": "https://figma.com/@example/uikit-template", "type": Resource.ResourceTypeChoices.EXTERNAL_LINK}
                ]
            },
            {
                "category": categories_dict["Business & Marketing"],
                "title": "Growth Hacking & SaaS Marketing Blueprint",
                "subtitle": "Acquire thousands of users without spending a fortune on ads.",
                "description": "Discover proven growth loops, viral marketing tactics, SEO strategies, and conversion rate optimization (CRO) tailored for SaaS products.",
                "language": "english",
                "level": "intermediate",
                "status": "published",
                "price": Decimal("179.99"),
                "discount_price": Decimal("89.99"),
                "thumbnail": "https://images.unsplash.com/photo-1432888498266-38ffec3eaf0a",
                "promo_video_url": "https://www.youtube.com/watch?v=D1B_BkGHbqs",
                "average_rating": Decimal("4.6"),
                "total_students": 920,
                "total_reviews": 180,
                "tags_to_add": ["SEO", "Marketing", "SaaS"],
                "highlights": [
                    "Data-driven customer acquisition frameworks",
                    "High-converting landing page frameworks",
                    "Email automation sequences that convert"
                ],
                "learning_points": [
                    "Identify your product-market fit metrics",
                    "Rank higher on search engines organically",
                    "Optimize onboarding funnels for retention"
                ],
                "modules": [
                    {
                        "title": "Module 1: Foundations of Growth",
                        "description": "Core concepts of product-led growth and metrics tracking.",
                        "order": 1,
                        "lessons": [
                            {"title": "Calculating CAC and LTV", "duration_in_minutes": 25, "order": 1},
                            {"title": "Setting up analytics tools", "duration_in_minutes": 20, "order": 2}
                        ]
                    }
                ],
                "resources": [
                    {"title": "SaaS Growth Framework Template", "file_url": "https://example.com/resources/growth-framework.xlsx", "type": Resource.ResourceTypeChoices.DOCUMENT}
                ]
            }
        ]

        # 5. Insertion of courses and relations
        for course_item in courses_data:
            course = Course.objects.create(
                category=course_item["category"],
                user_id=instructor_id,
                user_email=instructor_email,
                user_roles=instructor_roles,
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

            # Tags
            tags_to_add = [tags_dict[name] for name in course_item["tags_to_add"] if name in tags_dict]
            course.tags.add(*tags_to_add)

            # Highlights
            for idx, item_text in enumerate(course_item.get("highlights", []), start=1):
                CourseHighlight.objects.create(course=course, title=item_text, order=idx)

            # Learning Points
            for idx, item_text in enumerate(course_item.get("learning_points", []), start=1):
                CourseLearningPoint.objects.create(course=course, title=item_text, order=idx)

            # Modules and Lessons
            for mod_data in course_item.get("modules", []):
                module = Module.objects.create(
                    course=course,
                    title=mod_data["title"],
                    description=mod_data["description"],
                    order=mod_data["order"]
                )

                for les_data in mod_data.get("lessons", []):
                    duration_min = les_data["duration_in_minutes"]
                    lesson = Lesson.objects.create(
                        module=module,
                        title=les_data["title"],
                        duration_in_minutes=duration_min,
                        order=les_data["order"]
                    )

                    # Assigner l'un de vos liens YouTube en boucle
                    current_youtube_url = youtube_links[video_counter % len(youtube_links)]
                    video_counter += 1

                    # Video (Sans duration_in_seconds)
                    Video.objects.create(
                        lesson=lesson,
                        title=f"Video: {les_data['title']}",
                        video_url=current_youtube_url
                    )

            # Resources
            for res_data in course_item.get("resources", []):
                resource = Resource(
                    course=course,
                    title=res_data["title"],
                    external_url=res_data["file_url"],
                    resource_type=res_data.get("type", Resource.ResourceTypeChoices.EXTERNAL_LINK)
                )
                resource.full_clean()
                resource.save()

            self.stdout.write(f"Course successfully created: '{course.title}'")

        self.stdout.write(self.style.SUCCESS("Complete database seeding with YouTube links finished successfully!"))
