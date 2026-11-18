"""
Tests de la commande seed_courses : chaque cours de démonstration a une leçon LAB rattachée
à un lab publié qui contient des étapes (LabObjective). La commande tourne à chaque déploiement :
elle doit rester idempotente et ne jamais écraser un lab modifié depuis l'administration.
"""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from courses.models import Course
from lab.models import Lab
from lessons.models import Lesson
from quizzes.models import Question, Quiz, QuizAttempt


def run_seed():
    call_command('seed_courses', stdout=StringIO())


class SeedCourseLabsTests(TestCase):
    def test_chaque_cours_a_une_lecon_lab_avec_des_etapes(self):
        run_seed()
        courses = Course.objects.all()
        self.assertEqual(courses.count(), 4)
        for course in courses:
            lab_lessons = Lesson.objects.filter(module__course=course, lesson_type=Lesson.LessonType.LAB)
            self.assertEqual(lab_lessons.count(), 1, course.slug)
            lesson = lab_lessons.get()
            self.assertIsNotNone(lesson.lab, course.slug)
            self.assertEqual(lesson.lab.status, Lab.Status.PUBLISHED)
            self.assertFalse(hasattr(lesson, 'video') and lesson.video, 'une leçon LAB n\'a pas de vidéo')
            objectives = list(lesson.lab.objectives.all())
            self.assertGreaterEqual(len(objectives), 3, lesson.lab.slug)
            self.assertEqual([o.order for o in objectives], list(range(1, len(objectives) + 1)))
            for objective in objectives:
                self.assertTrue(objective.title and objective.content and objective.starter_code)

    def test_relancer_le_seed_ne_duplique_rien(self):
        run_seed()
        run_seed()
        self.assertEqual(Lab.objects.count(), 4)
        for lab in Lab.objects.all():
            self.assertEqual(lab.objectives.count(), 3, lab.slug)
            self.assertEqual(lab.lessons.count(), 1, lab.slug)

    def test_un_lab_modifie_par_un_admin_n_est_pas_ecrase(self):
        run_seed()
        lab = Lab.objects.get(slug='validate-api-payloads-in-python')
        lab.title = 'Titre modifié'
        lab.save()
        lab.objectives.filter(order=1).update(title='Étape modifiée')
        lab.objectives.filter(order=3).delete()

        run_seed()

        lab.refresh_from_db()
        self.assertEqual(lab.title, 'Titre modifié')
        self.assertEqual(lab.objectives.count(), 2)
        self.assertEqual(lab.objectives.get(order=1).title, 'Étape modifiée')


class SeedCourseQuizzesTests(TestCase):
    """Chaque cours a aussi une leçon QUIZ (QCM) distincte des labs, avec des questions à choix valides."""

    def test_chaque_cours_a_un_qcm_valide(self):
        run_seed()
        for course in Course.objects.all():
            quiz_lessons = Lesson.objects.filter(module__course=course, lesson_type=Lesson.LessonType.QUIZ)
            self.assertEqual(quiz_lessons.count(), 1, course.slug)
            quiz = quiz_lessons.get().quiz
            self.assertIsNotNone(quiz, course.slug)
            questions = list(quiz.questions.prefetch_related('choices'))
            self.assertGreaterEqual(len(questions), 4, quiz.title)
            self.assertEqual([q.order for q in questions], list(range(1, len(questions) + 1)))
            for question in questions:
                # QCM uniquement : pas de question de code (les exercices de code sont dans les labs)
                self.assertIn(question.type, [Question.Type.SINGLE, Question.Type.MULTIPLE, Question.Type.TRUE_FALSE])
                self.assertTrue(question.explanation, question.statement)
                choices = list(question.choices.all())
                correct = sum(choice.is_correct for choice in choices)
                self.assertGreaterEqual(len(choices), 2, question.statement)
                if question.type == Question.Type.MULTIPLE:
                    self.assertGreaterEqual(correct, 1, question.statement)
                else:
                    self.assertEqual(correct, 1, question.statement)

    def test_relancer_le_seed_garde_le_meme_quiz_et_ses_tentatives(self):
        run_seed()
        lesson = Lesson.objects.get(title='Quiz: Docker essentials')
        quiz = lesson.quiz
        QuizAttempt.objects.create(quiz=quiz, user_id='student')
        quiz.questions.filter(order=1).update(statement='Énoncé modifié')

        run_seed()

        self.assertEqual(Quiz.objects.count(), 4)
        lesson = Lesson.objects.get(title='Quiz: Docker essentials')
        self.assertEqual(lesson.quiz_id, quiz.id)
        self.assertEqual(quiz.attempts.count(), 1)
        self.assertEqual(quiz.questions.get(order=1).statement, 'Énoncé modifié')
