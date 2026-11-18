"""
Quiz d'une leçon (Lesson.quiz) : questions, choix et tentatives corrigées côté serveur.

Types de question et forme de la réponse attendue dans QuizAttempt.answers[<question_id>] :
- single / true_false : id d'un Choice (une seule bonne réponse) ;
- multiple : liste d'ids de Choice — tout ou rien (toutes les bonnes, aucune mauvaise) ;
- short : texte libre, comparé sans casse ni espaces superflus aux Choice `is_correct` (réponses acceptées) ;
- code : code source exécuté avec Piston sur `tests` ([{"stdin", "expected"}]), points au prorata des tests réussis.
"""
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Titre")
    description = models.TextField(blank=True, default='', verbose_name="Consignes")
    pass_score = models.PositiveSmallIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score de réussite (%)",
    )
    max_attempts = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Tentatives maximum", help_text="Vide = illimité",
    )
    time_limit_min = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Durée limite (minutes)", help_text="Vide = pas de limite",
    )
    shuffle = models.BooleanField(default=False, verbose_name="Mélanger questions et choix")
    # Auteur (sub du token SSO)
    created_by = models.CharField(max_length=255, blank=True, default='', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"

    def __str__(self):
        return self.title

    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE = 'single', 'Choix unique'
        MULTIPLE = 'multiple', 'Choix multiples'
        TRUE_FALSE = 'true_false', 'Vrai / Faux'
        SHORT = 'short', 'Réponse courte'
        CODE = 'code', 'Code'

    class Language(models.TextChoices):
        PYTHON = 'python', 'Python'
        PHP = 'php', 'PHP'
        TYPESCRIPT = 'typescript', 'TypeScript'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SINGLE)
    statement = models.TextField(verbose_name="Énoncé")
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, default='', verbose_name="Explication (après correction)")
    # Questions de code
    language = models.CharField(max_length=20, choices=Language.choices, blank=True, default='')
    starter_code = models.TextField(blank=True, default='')
    tests = models.JSONField(default=list, blank=True, help_text='[{"stdin": "...", "expected": "..."}]')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.quiz.title} - {self.order}. {self.statement[:60]}'


class Choice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user_id = models.CharField(max_length=255, db_index=True, verbose_name="ID Utilisateur (sub)")
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Score (%)")
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default=dict, blank=True)
    details = models.JSONField(default=list, blank=True, help_text="Résultat par question après correction")

    class Meta:
        ordering = ['-started_at']
        indexes = [models.Index(fields=['quiz', 'user_id'])]

    def __str__(self):
        return f'{self.user_id} - {self.quiz.title}'
