"""
Tests de l'app quizzes : exposition des questions sans réponses, tentatives, correction côté serveur
de chaque type de question (Piston simulé), droits, gestion imbriquée et lien avec les leçons.
"""
import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from categories.models import Category
from core.signals import activity_completed
from core.tests import FakeSigningKey, make_token
from courses.models import Course
from enrollments.models import Enrollment, LessonProgress
from lab.piston import PistonError, run_code
from lessons.models import Lesson
from modules.models import Module

from .models import Choice, Question, Quiz, QuizAttempt

INSTRUCTOR_ID = '00000000-0000-0000-0000-0000000000c1'
OTHER_INSTRUCTOR_ID = '00000000-0000-0000-0000-0000000000c2'
ADMIN_ID = '00000000-0000-0000-0000-0000000000c3'
STUDENT_ID = '00000000-0000-0000-0000-0000000000c4'
OUTSIDER_ID = '00000000-0000-0000-0000-0000000000c5'


def auth_client(sub, roles):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token(sub=sub, roles=roles)}')
    return client


def fake_run(language, code, stdin='', timeout=None):
    """Piston simulé : le « programme » double l'entier lu si le code contient `* 2`."""
    value = int(stdin or 0)
    return {'stdout': f'{value * 2 if "* 2" in code else value}\n', 'stderr': '', 'exit_code': 0}


class QuizFixtureMixin:

    def build(self):
        category = Category.objects.create(name='Back End', slug='back-end')
        self.course = Course.objects.create(
            category=category, title='Python', description='desc', price='10.00',
            user_id=INSTRUCTOR_ID, status='published',
        )
        module = Module.objects.create(course=self.course, title='Module 1', order=1)
        Lesson.objects.create(module=module, title='Vidéo', order=1)
        self.quiz = Quiz.objects.create(title='Bases', pass_score=70, created_by=ADMIN_ID)
        self.lesson = Lesson.objects.create(
            module=module, title='Quiz', order=2, lesson_type='QUIZ', quiz=self.quiz,
        )

        self.single = Question.objects.create(quiz=self.quiz, type='single', statement='2+2 ?', order=1,
                                              explanation='Quatre.')
        self.single_ok = Choice.objects.create(question=self.single, text='4', is_correct=True, order=1)
        self.single_ko = Choice.objects.create(question=self.single, text='5', order=2)

        self.multiple = Question.objects.create(quiz=self.quiz, type='multiple', statement='Pairs ?', order=2)
        self.multi_a = Choice.objects.create(question=self.multiple, text='2', is_correct=True, order=1)
        self.multi_b = Choice.objects.create(question=self.multiple, text='4', is_correct=True, order=2)
        self.multi_c = Choice.objects.create(question=self.multiple, text='5', order=3)

        self.true_false = Question.objects.create(quiz=self.quiz, type='true_false', statement='Vrai ?', order=3)
        self.tf_true = Choice.objects.create(question=self.true_false, text='True', is_correct=True, order=1)
        self.tf_false = Choice.objects.create(question=self.true_false, text='False', order=2)

        self.short = Question.objects.create(quiz=self.quiz, type='short', statement='Capitale ?', order=4)
        Choice.objects.create(question=self.short, text='Paris', is_correct=True, order=1)

        self.code = Question.objects.create(
            quiz=self.quiz, type='code', statement='Doublez', order=5, points=2, language='python',
            starter_code='n = int(input())', tests=[{'stdin': '2', 'expected': '4'}, {'stdin': '0', 'expected': '0'}],
        )

        self.enrollment = Enrollment.objects.create(user_id=STUDENT_ID, course=self.course)
        self.student = auth_client(STUDENT_ID, ['student'])
        self.outsider = auth_client(OUTSIDER_ID, ['student'])
        self.instructor = auth_client(INSTRUCTOR_ID, ['instructor'])
        self.other_instructor = auth_client(OTHER_INSTRUCTOR_ID, ['instructor'])
        self.admin = auth_client(ADMIN_ID, ['admin'])

    def perfect_answers(self):
        return {
            str(self.single.id): str(self.single_ok.id),
            str(self.multiple.id): [str(self.multi_b.id), str(self.multi_a.id)],
            str(self.true_false.id): str(self.tf_true.id),
            str(self.short.id): '  paris ',
            str(self.code.id): 'print(int(input()) * 2)',
        }

    def start(self, client=None):
        return (client or self.student).post(f'/api/quizzes/{self.quiz.id}/attempts/')

    def submit(self, attempt_id, answers, client=None):
        return (client or self.student).post(
            f'/api/quiz-attempts/{attempt_id}/submit/', {'answers': answers}, format='json',
        )


@patch('quizzes.services.run_code', side_effect=fake_run)
@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class QuizStudentTests(QuizFixtureMixin, TestCase):

    def setUp(self):
        self.build()

    # --- Lecture sans bonnes réponses ---------------------------------------------------------

    def test_quiz_never_exposes_correct_answers(self, *_):
        res = self.student.get(f'/api/quizzes/{self.quiz.id}/')
        self.assertEqual(res.status_code, 200)
        raw = json.dumps(res.data, default=str)
        for secret in ('is_correct', 'tests', 'explanation', 'Paris', 'Quatre.', 'expected'):
            self.assertNotIn(secret, raw)
        self.assertEqual(res.data['question_count'], 5)
        self.assertEqual(res.data['total_points'], 6)
        by_type = {question['type']: question for question in res.data['questions']}
        self.assertEqual(len(by_type['single']['choices']), 2)
        self.assertEqual(by_type['short']['choices'], [])
        self.assertEqual(by_type['code']['starter_code'], 'n = int(input())')
        self.assertEqual(res.data['lesson']['course_slug'], self.course.slug)
        self.assertEqual(res.data['my_attempts']['count'], 0)

    def test_not_enrolled_student_is_refused(self, *_):
        self.assertEqual(self.outsider.get(f'/api/quizzes/{self.quiz.id}/').status_code, 403)
        self.assertEqual(self.start(self.outsider).status_code, 403)

    def test_suspended_enrollment_is_refused(self, *_):
        self.enrollment.status = 'suspended'
        self.enrollment.save()
        self.assertEqual(self.student.get(f'/api/quizzes/{self.quiz.id}/').status_code, 403)

    def test_anonymous_is_refused(self, *_):
        self.assertIn(APIClient().get(f'/api/quizzes/{self.quiz.id}/').status_code, (401, 403))

    def test_quiz_without_lesson_is_only_for_its_managers(self, *_):
        orphan = Quiz.objects.create(title='Orphelin', created_by=OTHER_INSTRUCTOR_ID)
        self.assertEqual(self.student.get(f'/api/quizzes/{orphan.id}/').status_code, 403)
        self.assertEqual(self.other_instructor.get(f'/api/quizzes/{orphan.id}/').status_code, 200)

    def test_course_owner_can_preview(self, *_):
        self.assertEqual(self.instructor.get(f'/api/quizzes/{self.quiz.id}/').status_code, 200)

    # --- Tentatives --------------------------------------------------------------------------

    def test_start_then_resume_the_same_attempt(self, *_):
        first = self.start()
        self.assertEqual(first.status_code, 201)
        self.assertNotIn('score', first.data)
        again = self.start()
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.data['id'], first.data['id'])
        self.assertEqual(QuizAttempt.objects.count(), 1)

    def test_max_attempts_is_enforced(self, *_):
        self.quiz.max_attempts = 1
        self.quiz.save()
        attempt = self.start().data['id']
        self.submit(attempt, {})
        res = self.start()
        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.student.get(f'/api/quizzes/{self.quiz.id}/').data['my_attempts']['remaining'], 0)

    def test_perfect_submission_passes_and_completes_the_lesson(self, *_):
        attempt = self.start().data['id']
        res = self.submit(attempt, self.perfect_answers())
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(Decimal(res.data['score']), Decimal('100.00'))
        self.assertTrue(res.data['passed'])
        details = {item['question_id']: item for item in res.data['details']}
        self.assertEqual(details[str(self.single.id)]['explanation'], 'Quatre.')
        progress = LessonProgress.objects.get(enrollment=self.enrollment, lesson=self.lesson)
        self.assertTrue(progress.is_completed)

    def test_passing_emits_activity_completed_with_the_score(self, *_):
        calls = []
        activity_completed.connect(lambda sender, **kw: calls.append((sender, kw)), dispatch_uid='quiz_test', weak=False)
        self.addCleanup(activity_completed.disconnect, dispatch_uid='quiz_test')
        self.submit(self.start().data['id'], self.perfect_answers())
        self.assertEqual(len(calls), 1)
        sender, kwargs = calls[0]
        self.assertIs(sender, Quiz)
        self.assertEqual(kwargs['quiz'], self.quiz)
        self.assertEqual(kwargs['user_id'], STUDENT_ID)
        self.assertEqual(kwargs['score'], 100.0)

    def test_failed_quiz_does_not_complete_the_lesson(self, *_):
        res = self.submit(self.start().data['id'], {str(self.single.id): str(self.single_ok.id)})
        self.assertFalse(res.data['passed'])
        self.assertFalse(LessonProgress.objects.filter(lesson=self.lesson, is_completed=True).exists())

    def test_double_submission_is_refused(self, *_):
        attempt = self.start().data['id']
        self.submit(attempt, self.perfect_answers())
        res = self.submit(attempt, {})
        self.assertEqual(res.status_code, 409)
        self.assertEqual(QuizAttempt.objects.get().score, Decimal('100.00'))

    def test_other_users_attempt_is_invisible(self, *_):
        attempt = self.start().data['id']
        self.assertEqual(self.outsider.get(f'/api/quiz-attempts/{attempt}/').status_code, 404)
        self.assertEqual(self.submit(attempt, {}, client=self.outsider).status_code, 404)

    def test_correction_is_hidden_until_submitted(self, *_):
        attempt = self.start().data['id']
        before = self.student.get(f'/api/quiz-attempts/{attempt}/')
        self.assertNotIn('details', before.data)
        self.submit(attempt, self.perfect_answers())
        after = self.student.get(f'/api/quiz-attempts/{attempt}/')
        self.assertIn('details', after.data)
        self.assertTrue(after.data['passed'])

    def test_late_submission_scores_zero(self, *_):
        self.quiz.time_limit_min = 5
        self.quiz.save()
        attempt = self.start().data['id']
        QuizAttempt.objects.filter(pk=attempt).update(started_at=timezone.now() - timedelta(minutes=10))
        res = self.submit(attempt, self.perfect_answers())
        self.assertEqual(Decimal(res.data['score']), Decimal('0.00'))
        self.assertFalse(res.data['passed'])
        self.assertTrue(res.data['details'][0]['expired'])

    def test_expired_attempt_is_not_resumed(self, *_):
        self.quiz.time_limit_min = 5
        self.quiz.save()
        first = self.start().data['id']
        QuizAttempt.objects.filter(pk=first).update(started_at=timezone.now() - timedelta(minutes=10))
        second = self.start()
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(second.data['id'], first)
        self.assertIsNotNone(second.data['deadline'])


@patch('quizzes.services.run_code', side_effect=fake_run)
@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class QuizGradingTests(QuizFixtureMixin, TestCase):
    """Barème de chaque type de question."""

    def setUp(self):
        self.build()

    def graded(self, answers):
        res = self.submit(self.start().data['id'], answers)
        return {item['question_id']: item for item in res.data['details']}, res

    def test_single_wrong_choice_scores_zero(self, *_):
        details, _ = self.graded({str(self.single.id): str(self.single_ko.id)})
        self.assertEqual(details[str(self.single.id)]['earned'], 0)
        self.assertEqual(details[str(self.single.id)]['correct_choice_ids'], [str(self.single_ok.id)])

    def test_multiple_is_all_or_nothing(self, *_):
        partial, _ = self.graded({str(self.multiple.id): [str(self.multi_a.id)]})
        self.assertEqual(partial[str(self.multiple.id)]['earned'], 0)

    def test_multiple_with_a_wrong_choice_scores_zero(self, *_):
        details, _ = self.graded({str(self.multiple.id): [str(self.multi_a.id), str(self.multi_b.id), str(self.multi_c.id)]})
        self.assertEqual(details[str(self.multiple.id)]['earned'], 0)

    def test_true_false(self, *_):
        details, _ = self.graded({str(self.true_false.id): str(self.tf_false.id)})
        self.assertFalse(details[str(self.true_false.id)]['correct'])

    def test_short_answer_ignores_case_and_spaces(self, *_):
        details, _ = self.graded({str(self.short.id): ' PARIS'})
        self.assertTrue(details[str(self.short.id)]['correct'])

    def test_code_is_scored_per_passing_test(self, _, run_mock):
        details, res = self.graded({str(self.code.id): 'print(int(input()))'})
        code = details[str(self.code.id)]
        self.assertEqual(code['earned'], 1.0)  # 2 points × 1 test réussi / 2
        self.assertEqual([test['passed'] for test in code['tests']], [False, True])
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(Decimal(res.data['score']), Decimal('16.67'))  # 1 / 6 points

    def test_code_with_piston_down_fails_the_tests_without_error(self, _, run_mock):
        run_mock.side_effect = PistonError('injoignable')
        details, res = self.graded({str(self.code.id): 'print(1)'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(details[str(self.code.id)]['earned'], 0)
        self.assertIn('error', details[str(self.code.id)]['tests'][0])

    def test_empty_code_is_not_executed(self, _, run_mock):
        self.graded({str(self.code.id): '   '})
        run_mock.assert_not_called()

    def test_missing_answers_score_zero(self, *_):
        _, res = self.graded({})
        self.assertEqual(Decimal(res.data['score']), Decimal('0.00'))


@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class QuizManageTests(QuizFixtureMixin, TestCase):

    def setUp(self):
        self.build()

    def payload(self, **extra):
        return {
            'title': 'Nouveau', 'pass_score': 50,
            'questions': [
                {'type': 'single', 'statement': 'Q1', 'choices': [
                    {'text': 'A', 'is_correct': True}, {'text': 'B', 'is_correct': False}]},
                {'type': 'code', 'statement': 'Q2', 'language': 'python', 'points': 3,
                 'tests': [{'stdin': '1', 'expected': '2'}]},
            ],
            **extra,
        }

    def test_student_cannot_manage(self, _):
        self.assertEqual(self.student.get('/api/quizzes/manage/').status_code, 403)
        self.assertEqual(self.student.post('/api/quizzes/manage/', self.payload(), format='json').status_code, 403)

    def test_instructor_creates_a_quiz_with_questions(self, _):
        res = self.instructor.post('/api/quizzes/manage/', self.payload(), format='json')
        self.assertEqual(res.status_code, 201, res.data)
        quiz = Quiz.objects.get(pk=res.data['id'])
        self.assertEqual(quiz.created_by, INSTRUCTOR_ID)
        self.assertEqual(quiz.questions.count(), 2)
        self.assertTrue(res.data['questions'][0]['choices'][0]['is_correct'])

    def test_invalid_questions_are_rejected(self, _):
        two_correct = self.payload(questions=[{'type': 'single', 'statement': 'Q', 'choices': [
            {'text': 'A', 'is_correct': True}, {'text': 'B', 'is_correct': True}]}])
        self.assertEqual(self.instructor.post('/api/quizzes/manage/', two_correct, format='json').status_code, 400)
        no_tests = self.payload(questions=[{'type': 'code', 'statement': 'Q', 'language': 'python', 'tests': []}])
        self.assertEqual(self.instructor.post('/api/quizzes/manage/', no_tests, format='json').status_code, 400)
        no_answer = self.payload(questions=[{'type': 'short', 'statement': 'Q', 'choices': []}])
        self.assertEqual(self.instructor.post('/api/quizzes/manage/', no_answer, format='json').status_code, 400)

    def test_patch_replaces_questions(self, _):
        quiz_id = self.instructor.post('/api/quizzes/manage/', self.payload(), format='json').data['id']
        current = self.instructor.get(f'/api/quizzes/manage/{quiz_id}/').data['questions']
        kept = {**current[0], 'statement': 'Q1 modifiée'}
        res = self.instructor.patch(f'/api/quizzes/manage/{quiz_id}/', {'questions': [kept]}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        questions = Quiz.objects.get(pk=quiz_id).questions.all()
        self.assertEqual([question.statement for question in questions], ['Q1 modifiée'])
        self.assertEqual(str(questions[0].id), current[0]['id'])

    def test_course_owner_manages_the_quiz_of_his_lesson(self, _):
        # Quiz créé par un admin, rattaché à une leçon du cours de l'instructeur
        res = self.instructor.patch(f'/api/quizzes/manage/{self.quiz.id}/', {'title': 'Renommé'}, format='json')
        self.assertEqual(res.status_code, 200)
        ids = [item['id'] for item in self.instructor.get('/api/quizzes/manage/').data]
        self.assertIn(str(self.quiz.id), ids)

    def test_other_instructor_cannot_edit(self, _):
        res = self.other_instructor.patch(f'/api/quizzes/manage/{self.quiz.id}/', {'title': 'X'}, format='json')
        self.assertEqual(res.status_code, 403)
        self.assertNotIn(str(self.quiz.id), [item['id'] for item in self.other_instructor.get('/api/quizzes/manage/').data])

    def test_instructor_cannot_delete_a_quiz_taken_by_learners(self, _):
        QuizAttempt.objects.create(quiz=self.quiz, user_id=STUDENT_ID)
        self.assertEqual(self.instructor.delete(f'/api/quizzes/manage/{self.quiz.id}/').status_code, 409)
        self.assertEqual(self.admin.delete(f'/api/quizzes/manage/{self.quiz.id}/').status_code, 204)
        self.lesson.refresh_from_db()
        self.assertIsNone(self.lesson.quiz)


@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class LessonQuizLinkTests(QuizFixtureMixin, TestCase):

    def setUp(self):
        self.build()
        self.legacy = Lesson.objects.create(module=self.lesson.module, title='Ancien quiz', order=3, lesson_type='QUIZ')

    def test_lesson_exposes_its_quiz(self, _):
        res = self.student.get(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(res.data['quiz'], self.quiz.id)

    def test_existing_quiz_lessons_without_quiz_stay_editable(self, _):
        res = self.instructor.patch(f'/api/lessons/{self.legacy.id}/', {'title': 'Renommée'}, format='json')
        self.assertEqual(res.status_code, 200, res.data)

    def test_owner_links_his_quiz(self, _):
        quiz = Quiz.objects.create(title='À moi', created_by=INSTRUCTOR_ID)
        res = self.instructor.patch(f'/api/lessons/{self.legacy.id}/', {'quiz': str(quiz.id)}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.legacy.refresh_from_db()
        self.assertEqual(self.legacy.quiz, quiz)

    def test_someone_elses_quiz_cannot_be_linked(self, _):
        quiz = Quiz.objects.create(title='Pas à moi', created_by=OTHER_INSTRUCTOR_ID)
        res = self.instructor.patch(f'/api/lessons/{self.legacy.id}/', {'quiz': str(quiz.id)}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('quiz', res.data)

    def test_a_quiz_is_linked_to_one_lesson_only(self, _):
        res = self.instructor.patch(f'/api/lessons/{self.legacy.id}/', {'quiz': str(self.quiz.id)}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_quiz_is_cleared_when_the_lesson_type_changes(self, _):
        res = self.instructor.patch(f'/api/lessons/{self.lesson.id}/', {'lesson_type': 'VIDEO'}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.lesson.refresh_from_db()
        self.assertIsNone(self.lesson.quiz)


class PistonServiceTests(TestCase):
    """lab.piston.run_code : appel direct de Piston (sans passer par /api/execute/)."""

    @patch('lab.piston.requests.post')
    def test_run_code_sends_stdin_and_the_installed_runtime(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {'run': {'stdout': '4\n', 'stderr': '', 'code': 0}})
        result = run_code('python', 'print(4)', '2')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['version'], '3.12.0')
        self.assertEqual(payload['stdin'], '2')
        self.assertEqual(payload['files'][0]['name'], 'main.py')
        self.assertIsNotNone(post.call_args.kwargs['timeout'])
        self.assertEqual(result, {'stdout': '4\n', 'stderr': '', 'exit_code': 0})

    @patch('lab.piston.requests.post')
    def test_compile_error_is_reported_as_a_failed_run(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {'compile': {'code': 1, 'stderr': 'TS2304'}})
        self.assertEqual(run_code('typescript', 'x')['exit_code'], 1)

    @patch('lab.piston.requests.post')
    def test_piston_errors_raise(self, post):
        post.return_value = Mock(status_code=500)
        with self.assertRaises(PistonError):
            run_code('python', 'x')
        with self.assertRaises(PistonError):
            run_code('cobol', 'x')
