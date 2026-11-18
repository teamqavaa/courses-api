"""
QCM des cours de démonstration (commande seed_courses), distincts des labs : questions à choix unique,
choix multiples et vrai / faux, corrigées côté serveur (quizzes/services.py). Pas de question de code :
la pratique du code se fait dans les labs (courses/seed_labs.py).

Chaque quiz est rattaché à son cours par une leçon QUIZ placée après la leçon LAB du même module.
La commande tourne à chaque déploiement et recrée les leçons : le quiz, lui, est créé **une seule fois**
(retrouvé par `created_by = "seed:<clé>"`), ce qui conserve ses tentatives et toute modification faite
dans l'éditeur de quiz.
"""
from quizzes.models import Choice, Question, Quiz

SINGLE = Question.Type.SINGLE
MULTIPLE = Question.Type.MULTIPLE
TRUE_FALSE = Question.Type.TRUE_FALSE

# Question : (type, énoncé, explication, [(choix, correct), ...]) ; vrai / faux : [(True|False)] suffit.
COURSE_QUIZZES = [
    {
        'key': 'react-django-apis',
        'course_title': 'Become a Full-Stack Developer with React & Django',
        'module_order': 2,
        'lesson': {'title': 'Quiz: React & Django APIs', 'duration_in_minutes': 10, 'order': 4},
        'title': 'React & Django APIs',
        'description': 'Check what you learned about Django REST Framework and how a React app consumes it.',
        'questions': [
            (SINGLE, 'Which DRF component turns a model instance into JSON and validates incoming data?',
             'A serializer converts model instances to native types and validates input before saving.',
             [('A serializer', True), ('A router', False), ('A middleware', False), ('A migration', False)]),
            (SINGLE, 'Which HTTP status code should an API return after successfully creating a resource?',
             '201 Created tells the client a new resource exists; 200 is for a successful read or update.',
             [('200', False), ('201', True), ('204', False), ('302', False)]),
            (MULTIPLE, 'Which of these are valid ways to protect a DRF endpoint? (select all that apply)',
             'permission_classes and authentication_classes both secure a view; CORS only controls browsers.',
             [('permission_classes = [IsAuthenticated]', True),
              ('A token authentication class', True),
              ('Adding the domain to CORS_ALLOWED_ORIGINS', False)]),
            (TRUE_FALSE, 'In React, calling fetch() directly in the component body on every render is good practice.',
             'Side effects such as fetch belong in useEffect (or a data library), otherwise they run on each render.',
             [False]),
            (SINGLE, 'Where should a JWT access token be stored to keep it away from JavaScript?',
             'An httpOnly cookie cannot be read by scripts, which limits the impact of an XSS attack.',
             [('localStorage', False), ('An httpOnly cookie', True), ('A global variable', False)]),
        ],
    },
    {
        'key': 'docker-essentials',
        'course_title': 'Advanced DevOps & Docker Pipeline Mastery',
        'module_order': 1,
        'lesson': {'title': 'Quiz: Docker essentials', 'duration_in_minutes': 10, 'order': 4},
        'title': 'Docker essentials',
        'description': 'Images, layers, multi-stage builds and Docker Compose.',
        'questions': [
            (SINGLE, 'What is the main benefit of a multi-stage Docker build?',
             'Build tools stay in the first stage; only the artifacts are copied into a small final image.',
             [('A smaller final image', True), ('Faster network access', False),
              ('Running several containers at once', False)]),
            (SINGLE, 'Which instruction should come first to make the best use of the layer cache?',
             'Copy the dependency file and install dependencies before copying the source code, which changes often.',
             [('COPY . .', False), ('COPY requirements.txt . then RUN pip install', True), ('CMD', False)]),
            (MULTIPLE, 'Which practices make an image more secure? (select all that apply)',
             'A pinned base image and a non-root user reduce risk; secrets must never be baked into an image.',
             [('Pin the base image version', True), ('Run as a non-root USER', True),
              ('Copy the .env file into the image', False)]),
            (TRUE_FALSE, 'In Docker Compose, services on the same network can reach each other by service name.',
             'Compose creates a network where each service name resolves to its container (e.g. db:5432).',
             [True]),
            (SINGLE, 'Which command starts every service defined in docker-compose.yml in the background?',
             'docker compose up -d starts the services detached; build only builds the images.',
             [('docker compose up -d', True), ('docker compose build', False), ('docker run compose', False)]),
        ],
    },
    {
        'key': 'figma-fundamentals',
        'course_title': 'UI/UX Design Masterclass with Figma',
        'module_order': 1,
        'lesson': {'title': 'Quiz: Figma fundamentals', 'duration_in_minutes': 10, 'order': 4},
        'title': 'Figma fundamentals',
        'description': 'Frames, auto layout, components and developer handoff.',
        'questions': [
            (SINGLE, 'What does "Hug contents" do on an auto layout frame?',
             'Hug contents sizes the frame to its children plus padding and gaps.',
             [('The frame grows with its children', True), ('The frame fills its parent', False),
              ('The frame keeps a fixed size', False)]),
            (SINGLE, 'Why use a spacing scale based on a 4 or 8 px unit?',
             'A shared unit keeps spacing consistent and maps directly to developer tokens.',
             [('It keeps spacing consistent across screens', True), ('It makes files lighter', False),
              ('Figma requires it', False)]),
            (MULTIPLE, 'Which elements belong in a design system? (select all that apply)',
             'Components and tokens (colors, spacing, typography) are shared; one-off screens are not.',
             [('Reusable components', True), ('Color and spacing tokens', True),
              ('A single marketing page mockup', False)]),
            (TRUE_FALSE, 'Editing a main component updates all of its instances.',
             'Instances inherit changes from their main component, except the properties overridden locally.',
             [True]),
        ],
    },
    {
        'key': 'growth-metrics',
        'course_title': 'Growth Hacking & SaaS Marketing Blueprint',
        'module_order': 1,
        'lesson': {'title': 'Quiz: Growth metrics', 'duration_in_minutes': 10, 'order': 4},
        'title': 'Growth metrics',
        'description': 'CAC, LTV, churn and how to read them to choose acquisition channels.',
        'questions': [
            (SINGLE, 'You spend 5,000 on ads and acquire 40 customers. What is your CAC?',
             'CAC = spend / new customers = 5,000 / 40 = 125.',
             [('40', False), ('125', True), ('200', False), ('5,000', False)]),
            (SINGLE, 'Which LTV / CAC ratio is usually considered healthy for a SaaS?',
             'A ratio of at least 3 means a customer brings three times what it costs to acquire.',
             [('Below 1', False), ('Around 1', False), ('3 or more', True)]),
            (MULTIPLE, 'Which levers increase customer lifetime value? (select all that apply)',
             'LTV grows with revenue per customer and margin, and when churn goes down.',
             [('Reducing churn', True), ('Raising revenue per customer', True),
              ('Spending more on ads', False)]),
            (TRUE_FALSE, 'A monthly churn of 2% means an average customer stays about 50 months.',
             'Average lifetime ≈ 1 / churn = 1 / 0.02 = 50 months.',
             [True]),
        ],
    },
]


def _choices(question_type, answers):
    if question_type == TRUE_FALSE:
        return [('True', answers[0] is True), ('False', answers[0] is False)]
    return answers


def ensure_seed_quiz(data):
    """Crée le quiz et ses questions s'ils n'existent pas ; un quiz existant est renvoyé tel quel."""
    marker = f"seed:{data['key']}"
    quiz = Quiz.objects.filter(created_by=marker).first()
    if quiz:
        return quiz
    quiz = Quiz.objects.create(
        title=data['title'],
        description=data['description'],
        pass_score=70,
        shuffle=True,
        created_by=marker,
    )
    for order, (question_type, statement, explanation, answers) in enumerate(data['questions'], start=1):
        question = Question.objects.create(
            quiz=quiz, type=question_type, statement=statement, explanation=explanation, order=order,
        )
        Choice.objects.bulk_create(
            Choice(question=question, text=text, is_correct=correct, order=position)
            for position, (text, correct) in enumerate(_choices(question_type, answers), start=1)
        )
    return quiz


def quiz_lessons_by_module(course_title):
    """{module_order: [(données de leçon, quiz)]} des leçons QUIZ d'un cours de démonstration."""
    lessons = {}
    for item in COURSE_QUIZZES:
        if item['course_title'] == course_title:
            lessons.setdefault(item['module_order'], []).append((item['lesson'], ensure_seed_quiz(item)))
    return lessons
