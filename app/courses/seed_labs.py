"""
Labs pratiques des cours de démonstration (commande seed_courses).

Chaque lab est rattaché à un cours par une leçon LAB (`course_title`, `module_order`, `lesson`) et
contient des étapes ordonnées (LabObjective) : consigne, indice et code de départ exécutable avec
Piston (Python 3.12, TypeScript 5.0). La commande tourne à chaque déploiement : `ensure_seed_lab`
ne crée un lab et ses étapes que s'ils n'existent pas, pour ne jamais écraser une modification
faite depuis l'administration ou « Manage labs ».
"""
from lab.models import Lab, LabObjective

SEED_AUTHOR_NAME = 'Qavaa Ignite Experts'

COURSE_LABS = [
    {
        'course_title': 'Become a Full-Stack Developer with React & Django',
        'module_order': 2,
        'lesson': {'title': 'Lab: Validate API payloads', 'duration_in_minutes': 30, 'order': 3},
        'lab': {
            'slug': 'validate-api-payloads-in-python',
            'title': 'Validate API payloads in Python',
            'description': (
                'Write the validation logic a DRF serializer runs before saving data: '
                'required fields, types and error messages returned to the client.'
            ),
            'language': Lab.Language.PYTHON,
            'difficulty': Lab.Difficulty.GUIDED,
        },
        'steps': [
            {
                'title': 'Check required fields',
                'content': (
                    'An API receives a JSON payload as a Python dict. Complete missing_fields() so it '
                    'returns the required fields that are absent or empty, in the order of REQUIRED.\n\n'
                    'Expected output:\n[\'email\']\n[]'
                ),
                'hint': 'Loop over REQUIRED and keep a field when payload.get(field) is falsy.',
                'starter_code': (
                    'REQUIRED = ["title", "email", "price"]\n\n\n'
                    'def missing_fields(payload):\n'
                    '    # TODO: return the required fields that are missing or empty\n'
                    '    return []\n\n\n'
                    'print(missing_fields({"title": "React", "email": "", "price": 10}))\n'
                    'print(missing_fields({"title": "React", "email": "a@b.co", "price": 10}))\n'
                ),
            },
            {
                'title': 'Validate field types',
                'content': (
                    'A price must be a positive number and an email must contain "@". Complete '
                    'validate() so it returns a dict {field: message} with one message per invalid field.\n\n'
                    'Expected output:\n{\'price\': \'Must be a positive number.\', '
                    '\'email\': \'Enter a valid email address.\'}\n{}'
                ),
                'hint': 'Use isinstance(value, (int, float)) and value > 0 for the price, "@" in value for the email.',
                'starter_code': (
                    'def validate(payload):\n'
                    '    errors = {}\n'
                    '    # TODO: check "price" then "email"\n'
                    '    return errors\n\n\n'
                    'print(validate({"title": "React", "email": "nope", "price": -5}))\n'
                    'print(validate({"title": "React", "email": "a@b.co", "price": 49.9}))\n'
                ),
            },
            {
                'title': 'Return an API response',
                'content': (
                    'Combine both checks like serializer.is_valid(): return (400, errors) when something '
                    'is wrong, (201, cleaned_payload) otherwise. The cleaned payload trims the title.\n\n'
                    'Expected output:\n(400, {\'email\': \'This field is required.\'})\n'
                    '(201, {\'title\': \'React\', \'email\': \'a@b.co\', \'price\': 10})'
                ),
                'hint': 'Start with the missing fields ("This field is required."), then merge the type errors.',
                'starter_code': (
                    'REQUIRED = ["title", "email", "price"]\n\n\n'
                    'def create_course(payload):\n'
                    '    errors = {}\n'
                    '    # TODO: required fields, then types, then the cleaned payload\n'
                    '    return 201, payload\n\n\n'
                    'print(create_course({"title": "React", "price": 10}))\n'
                    'print(create_course({"title": "  React ", "email": "a@b.co", "price": 10}))\n'
                ),
            },
        ],
    },
    {
        'course_title': 'Advanced DevOps & Docker Pipeline Mastery',
        'module_order': 1,
        'lesson': {'title': 'Lab: Lint a Dockerfile', 'duration_in_minutes': 30, 'order': 3},
        'lab': {
            'slug': 'lint-a-dockerfile-in-python',
            'title': 'Lint a Dockerfile in Python',
            'description': (
                'Build a small Dockerfile linter that applies the best practices from the course: '
                'pinned base images, no root user and a clean multi-stage build.'
            ),
            'language': Lab.Language.PYTHON,
            'difficulty': Lab.Difficulty.INTERMEDIATE,
        },
        'steps': [
            {
                'title': 'Parse the instructions',
                'content': (
                    'Turn a Dockerfile into a list of (INSTRUCTION, arguments) tuples. Skip empty lines '
                    'and comments, and upper-case the instruction.\n\n'
                    'Expected output:\n[(\'FROM\', \'python:latest\'), (\'COPY\', \'. /app\'), '
                    '(\'RUN\', \'pip install -r requirements.txt\')]'
                ),
                'hint': 'line.strip(), skip lines starting with "#", then line.split(maxsplit=1).',
                'starter_code': (
                    'DOCKERFILE = """\n'
                    '# Build image\n'
                    'FROM python:latest\n\n'
                    'copy . /app\n'
                    'RUN pip install -r requirements.txt\n'
                    '"""\n\n\n'
                    'def parse(text):\n'
                    '    # TODO: return [(instruction, arguments), ...]\n'
                    '    return []\n\n\n'
                    'print(parse(DOCKERFILE))\n'
                ),
            },
            {
                'title': 'Flag unpinned base images',
                'content': (
                    'A FROM without a tag, or with the "latest" tag, makes builds non reproducible. '
                    'Complete unpinned_images() so it returns every such image.\n\n'
                    'Expected output:\n[\'python:latest\', \'nginx\']'
                ),
                'hint': 'An image is pinned when it contains ":" and the part after the last ":" is not "latest".',
                'starter_code': (
                    'INSTRUCTIONS = [\n'
                    '    ("FROM", "python:latest"),\n'
                    '    ("FROM", "node:20-alpine"),\n'
                    '    ("FROM", "nginx"),\n'
                    ']\n\n\n'
                    'def unpinned_images(instructions):\n'
                    '    # TODO: return the FROM images without a fixed tag\n'
                    '    return []\n\n\n'
                    'print(unpinned_images(INSTRUCTIONS))\n'
                ),
            },
            {
                'title': 'Report every issue',
                'content': (
                    'Write lint() returning a sorted list of messages: "Pin the base image <image>" for '
                    'each unpinned image, and "Add a non-root USER" when no USER instruction exists.\n\n'
                    'Expected output:\n[\'Add a non-root USER\', \'Pin the base image python:latest\']'
                ),
                'hint': 'Reuse the logic of step 2 and check any(name == "USER" for name, _ in instructions).',
                'starter_code': (
                    'INSTRUCTIONS = [\n'
                    '    ("FROM", "python:latest"),\n'
                    '    ("COPY", ". /app"),\n'
                    '    ("CMD", "python app.py"),\n'
                    ']\n\n\n'
                    'def lint(instructions):\n'
                    '    issues = []\n'
                    '    # TODO: unpinned images, then the USER instruction\n'
                    '    return sorted(issues)\n\n\n'
                    'print(lint(INSTRUCTIONS))\n'
                ),
            },
        ],
    },
    {
        'course_title': 'UI/UX Design Masterclass with Figma',
        'module_order': 1,
        'lesson': {'title': 'Lab: Build an auto layout spacing scale', 'duration_in_minutes': 25, 'order': 3},
        'lab': {
            'slug': 'auto-layout-spacing-scale-in-typescript',
            'title': 'Auto layout spacing scale in TypeScript',
            'description': (
                'Recreate the maths behind Figma auto layout: a consistent spacing scale, the size of '
                'a frame that hugs its content, and design tokens ready for developers.'
            ),
            'language': Lab.Language.TYPESCRIPT,
            'difficulty': Lab.Difficulty.GUIDED,
        },
        'steps': [
            {
                'title': 'Generate a spacing scale',
                'content': (
                    'Design systems use spacing values that are multiples of a base unit. Complete '
                    'spacingScale() so it returns the first `steps` multiples of `base`.\n\n'
                    'Expected output:\n[ 4, 8, 12, 16, 20, 24 ]'
                ),
                'hint': 'Array.from({ length: steps }, (_, i) => base * (i + 1)).',
                'starter_code': (
                    'function spacingScale(base: number, steps: number): number[] {\n'
                    '  // TODO: return [base, base * 2, ...]\n'
                    '  return [];\n'
                    '}\n\n'
                    'console.log(spacingScale(4, 6));\n'
                ),
            },
            {
                'title': 'Compute a hug-contents frame',
                'content': (
                    'A horizontal auto layout frame set to "hug contents" is as wide as its children, '
                    'plus the gaps between them, plus the left and right padding. Complete hugWidth().\n\n'
                    'Expected output:\n184'
                ),
                'hint': 'Sum of widths + gap * (children - 1) + padding * 2.',
                'starter_code': (
                    'function hugWidth(childWidths: number[], gap: number, padding: number): number {\n'
                    '  // TODO: children + gaps + padding on both sides\n'
                    '  return 0;\n'
                    '}\n\n'
                    'console.log(hugWidth([40, 64, 40], 8, 12));\n'
                ),
            },
            {
                'title': 'Export design tokens',
                'content': (
                    'Developers consume spacing as named tokens. Complete toTokens() so it maps each '
                    'value of the scale to "space-<index>" (starting at 1) with a px value.\n\n'
                    'Expected output:\n{ \'space-1\': \'4px\', \'space-2\': \'8px\', \'space-3\': \'12px\' }'
                ),
                'hint': 'Build an object with scale.forEach((value, i) => tokens[`space-${i + 1}`] = `${value}px`).',
                'starter_code': (
                    'function toTokens(scale: number[]): Record<string, string> {\n'
                    '  const tokens: Record<string, string> = {};\n'
                    '  // TODO: fill the tokens\n'
                    '  return tokens;\n'
                    '}\n\n'
                    'console.log(toTokens([4, 8, 12]));\n'
                ),
            },
        ],
    },
    {
        'course_title': 'Growth Hacking & SaaS Marketing Blueprint',
        'module_order': 1,
        'lesson': {'title': 'Lab: Compute CAC, LTV and payback', 'duration_in_minutes': 25, 'order': 3},
        'lab': {
            'slug': 'saas-unit-economics-in-python',
            'title': 'SaaS unit economics in Python',
            'description': (
                'Compute the growth metrics from the course with real numbers: customer acquisition '
                'cost, lifetime value and the LTV/CAC ratio that tells whether a channel is worth it.'
            ),
            'language': Lab.Language.PYTHON,
            'difficulty': Lab.Difficulty.GUIDED,
        },
        'steps': [
            {
                'title': 'Calculate the CAC',
                'content': (
                    'The customer acquisition cost is the marketing spend divided by the number of new '
                    'customers. Complete cac() and round the result to 2 decimals.\n\n'
                    'Expected output:\n125.0'
                ),
                'hint': 'round(spend / new_customers, 2).',
                'starter_code': (
                    'def cac(spend, new_customers):\n'
                    '    # TODO: cost to acquire one customer\n'
                    '    return 0\n\n\n'
                    'print(cac(5000, 40))\n'
                ),
            },
            {
                'title': 'Calculate the LTV',
                'content': (
                    'Lifetime value = monthly revenue per customer × gross margin / monthly churn rate. '
                    'Complete ltv() and round to 2 decimals.\n\n'
                    'Expected output:\n1600.0'
                ),
                'hint': 'With arpu=40, margin=0.8 and churn=0.02: 40 * 0.8 / 0.02.',
                'starter_code': (
                    'def ltv(arpu, gross_margin, monthly_churn):\n'
                    '    # TODO: lifetime value of one customer\n'
                    '    return 0\n\n\n'
                    'print(ltv(40, 0.8, 0.02))\n'
                ),
            },
            {
                'title': 'Rank the acquisition channels',
                'content': (
                    'A channel is healthy when LTV / CAC is at least 3. Print each channel with its ratio '
                    '(1 decimal) and "keep" or "cut", best ratio first.\n\n'
                    'Expected output:\nSEO 12.8 keep\nAds 3.2 keep\nEvents 1.1 cut'
                ),
                'hint': 'Compute the ratios in a list of tuples, sort with key=lambda row: row[1], reverse=True.',
                'starter_code': (
                    'LTV = 1600\n'
                    'CHANNELS = {"Ads": (25000, 50), "SEO": (5000, 40), "Events": (30000, 20)}\n\n'
                    '# TODO: for each channel (spend, customers) compute CAC, then LTV / CAC\n'
                    'for name, (spend, customers) in CHANNELS.items():\n'
                    '    print(name)\n'
                ),
            },
        ],
    },
]


def ensure_seed_lab(lab_data, steps):
    """Crée le lab publié et ses étapes s'ils n'existent pas ; un lab existant est renvoyé tel quel."""
    lab, created = Lab.objects.get_or_create(
        slug=lab_data['slug'],
        defaults={
            'title': lab_data['title'],
            'description': lab_data['description'],
            'language': lab_data['language'],
            'difficulty': lab_data['difficulty'],
            'status': Lab.Status.PUBLISHED,
            'starter_code': steps[0]['starter_code'],
            'author_name': SEED_AUTHOR_NAME,
        },
    )
    if created:
        LabObjective.objects.bulk_create(
            LabObjective(lab=lab, order=order, **step) for order, step in enumerate(steps, start=1)
        )
    return lab


def lab_lessons_by_module(course_title):
    """{module_order: [(données de leçon, lab)]} des leçons LAB d'un cours de démonstration."""
    lessons = {}
    for item in COURSE_LABS:
        if item['course_title'] == course_title:
            lab = ensure_seed_lab(item['lab'], item['steps'])
            lessons.setdefault(item['module_order'], []).append((item['lesson'], lab))
    return lessons
