# app/categories/management/commands/seed_categories.py
from django.core.management.base import BaseCommand
from categories.models import Category
from courses.models import Course  # <--- AJOUTÉ : Pour supprimer les clés étrangères référencées


class Command(BaseCommand):
    help = "Seeds the database with 10 main categories and at least 5 subcategories each for a modern LMS (in English)."

    def handle(self, *args, **options):
        self.stdout.write("Purging existing courses...")
        # 1. On supprime d'abord les cours qui référencent (PROTECT) les catégories
        Course.objects.all().delete()

        self.stdout.write("Purging existing categories...")
        # 2. On peut maintenant supprimer les catégories en toute sécurité
        Category.objects.all().delete()

        # Structure des données des catégories
        categories_data = [
            # 1. Software Development
            {
                "name": "Software Development",
                "description": "Learn to code, build modern web/mobile applications, and design complex software architectures.",
                "subcategories": [
                    {"name": "Web Development", "description": "Frontend, backend, and full-stack web technologies."},
                    {"name": "Mobile Development", "description": "Native and cross-platform mobile apps for iOS and Android."},
                    {"name": "Programming Languages", "description": "Master languages like Python, JavaScript, Rust, and Go."},
                    {"name": "Game Development", "description": "Game design and development using Unity, Unreal Engine, and C#."},
                    {"name": "Software Architecture", "description": "Design patterns, microservices, and system architecture principles."}
                ]
            },
            # 2. Data Science & Artificial Intelligence
            {
                "name": "Data Science & AI",
                "description": "Unlock data-driven insights and harness the power of neural networks, machine learning, and AI models.",
                "subcategories": [
                    {"name": "Machine Learning", "description": "Supervised, unsupervised learning, and predictive modeling."},
                    {"name": "Deep Learning", "description": "Neural networks, computer vision, and natural language processing."},
                    {"name": "Data Analytics", "description": "Data exploration, business intelligence, and visualization tools."},
                    {"name": "Generative AI", "description": "Prompt engineering, LLM integration, and fine-tuning."},
                    {"name": "Data Engineering", "description": "ETL pipelines, big data storage, and database management."}
                ]
            },
            # 3. IT Infrastructure & Cybersecurity
            {
                "name": "IT Infrastructure & Security",
                "description": "Manage modern cloud environments, automate infrastructure, and defend against cyber threats.",
                "subcategories": [
                    {"name": "Cloud Computing", "description": "AWS, Microsoft Azure, and Google Cloud Platform services."},
                    {"name": "DevOps & SRE", "description": "CI/CD pipelines, infrastructure as code, and site reliability."},
                    {"name": "Cybersecurity", "description": "Ethical hacking, network security, and threat intelligence."},
                    {"name": "Network Engineering", "description": "Routing, switching, and enterprise network design."},
                    {"name": "Linux & SysAdmin", "description": "Unix/Linux system administration and shell scripting."}
                ]
            },
            # 4. Design & Creative Arts
            {
                "name": "Design & Creative Arts",
                "description": "Discover visual design, create stellar user interfaces, and build engaging multimedia content.",
                "subcategories": [
                    {"name": "UI/UX Design", "description": "User research, wireframing, prototyping, and UI design."},
                    {"name": "Graphic Design", "description": "Layout, typography, branding, and vector illustration."},
                    {"name": "3D & Animation", "description": "3D modeling, rendering, and motion graphic design."},
                    {"name": "Video Editing", "description": "Video production, post-processing, and visual effects."},
                    {"name": "Photography & Imaging", "description": "Digital photography, lighting techniques, and photo editing."}
                ]
            },
            # 5. Business & Entrepreneurship
            {
                "name": "Business & Entrepreneurship",
                "description": "Learn how to build a startup, optimize business models, and manage complex operations.",
                "subcategories": [
                    {"name": "Entrepreneurship & Startups", "description": "Venture capital, lean startup methodology, and business plans."},
                    {"name": "Product Management", "description": "Product lifecycle, agile frameworks, and user-story mapping."},
                    {"name": "Project Management", "description": "Scrum, Kanban, PMP methodologies, and project delivery."},
                    {"name": "Business Strategy", "description": "Competitive analysis, market entry, and growth strategies."},
                    {"name": "Sales & Business Development", "description": "B2B sales, negotiation techniques, and pipeline management."}
                ]
            },
            # 6. Marketing & Growth
            {
                "name": "Marketing & Growth",
                "description": "Master digital channels, grow audience bases, and convert leads into loyal customers.",
                "subcategories": [
                    {"name": "Digital Marketing", "description": "Social media marketing, content marketing, and email campaigns."},
                    {"name": "Search Engine Optimization", "description": "On-page, off-page, and technical SEO strategies."},
                    {"name": "Paid Advertising", "description": "Google Ads, Meta Ads, and PPC campaign optimization."},
                    {"name": "Growth Hacking", "description": "Data-driven marketing, A/B testing, and viral loops."},
                    {"name": "Brand Strategy", "description": "Brand positioning, copywriting, and storytelling."}
                ]
            },
            # 7. Finance & Fintech
            {
                "name": "Finance & Fintech",
                "description": "Navigate financial markets, manage corporate portfolios, and leverage blockchain tech.",
                "subcategories": [
                    {"name": "Investment & Trading", "description": "Stock market, technical analysis, and portfolio management."},
                    {"name": "Corporate Finance", "description": "Financial modeling, accounting, and capital budgeting."},
                    {"name": "Blockchain & Cryptocurrencies", "description": "DeFi, smart contracts, and Web3 technologies."},
                    {"name": "Personal Finance", "description": "Budgeting, tax planning, and wealth accumulation."},
                    {"name": "Financial Risk Management", "description": "Credit, market, and operational risk assessment."}
                ]
            },
            # 8. No-Code & Automation
            {
                "name": "No-Code & Automation",
                "description": "Build tools, databases, and automated workflows without writing traditional code.",
                "subcategories": [
                    {"name": "No-Code Web App Builders", "description": "Building powerful web apps with Bubble, Webflow, or Softr."},
                    {"name": "Workflow Automation", "description": "Connecting tools and automating tasks with Make and Zapier."},
                    {"name": "No-Code Mobile App Builders", "description": "Creating native mobile apps with FlutterFlow, Glide, or Adalo."},
                    {"name": "Database & Productivity", "description": "Relational data structuring using Airtable and Notion."},
                    {"name": "AI Automation Agency (AAA)", "description": "Building and selling AI agents and automation setups for businesses."}
                ]
            },
            # 9. Personal Development & Leadership
            {
                "name": "Personal Development",
                "description": "Maximize personal productivity, master communication, and build emotional intelligence.",
                "subcategories": [
                    {"name": "Leadership & Management", "description": "Team building, delegation, and strategic leadership."},
                    {"name": "Productivity & Time Management", "description": "Goal setting, focus optimization, and work-life balance."},
                    {"name": "Public Speaking", "description": "Presentation skills, vocal training, and stage presence."},
                    {"name": "Emotional Intelligence", "description": "Self-awareness, empathy, and relationship management."},
                    {"name": "Career Development", "description": "Resume writing, interview prep, and salary negotiation."}
                ]
            },
            # 10. Language & Communication
            {
                "name": "Language & Communication",
                "description": "Learn new languages and master professional communication in global environments.",
                "subcategories": [
                    {"name": "Business English", "description": "Professional emails, corporate presentations, and meeting vocabulary."},
                    {"name": "Spanish", "description": "From beginner conversational Spanish to advanced business fluency."},
                    {"name": "French", "description": "Mastering the language of French culture, travel, and business."},
                    {"name": "Mandarin Chinese", "description": "Introduction to characters, tones, and professional Chinese conversation."},
                    {"name": "Technical Writing", "description": "Writing clean documentation, APIs guides, and whitepapers."}
                ]
            }
        ]

        def create_categories_recursive(data_list, parent=None):
            count = 0
            for item in data_list:
                category = Category.objects.create(
                    name=item["name"],
                    description=item["description"],
                    parent=parent,
                    is_active=True
                )
                count += 1
                self.stdout.write(f"Created: {category}")

                if "subcategories" in item and item["subcategories"]:
                    count += create_categories_recursive(item["subcategories"], parent=category)

            return count

        total_created = create_categories_recursive(categories_data)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {total_created} categories and subcategories!")
        )
