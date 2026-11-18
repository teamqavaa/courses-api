"""
Tests du signal activity_completed (core/signals.py) et de son receiver (enrollments/receivers.py) :
réussir un lab (ou un quiz) marque terminées les leçons qui le référencent, uniquement dans les
cours où l'utilisateur est inscrit ; une nouvelle inscription rattrape les labs déjà réussis.
"""
from decimal import Decimal

from django.test import TestCase

from categories.models import Category
from core.signals import activity_completed, enrollments_created
from courses.models import Course
from lab.models import Lab, UserProgress
from lessons.models import Lesson
from modules.models import Module
from order_items.models import OrderItem
from orders.models import Order
from payment_providers.models import PaymentProvider
from payments.models import Payment
from payments.services import PaymentService
from .models import Enrollment, LessonProgress

USER_ID = '00000000-0000-0000-0000-0000000000b1'
OTHER_USER_ID = '00000000-0000-0000-0000-0000000000b2'


def create_course(title, category, lab):
    """Cours publié de 4 leçons : 3 vidéos et 1 leçon LAB (ordre 2)."""
    course = Course.objects.create(
        category=category, title=title, description='desc', price='10.00',
        user_id='instructor', status='published',
    )
    module = Module.objects.create(course=course, title='Module 1', order=1)
    Lesson.objects.create(module=module, title='Vidéo 1', order=1)
    Lesson.objects.create(module=module, title='Pratique', order=2, lesson_type='LAB', lab=lab)
    Lesson.objects.create(module=module, title='Vidéo 2', order=3)
    Lesson.objects.create(module=module, title='Vidéo 3', order=4)
    return course


class ActivityCompletedTests(TestCase):

    def setUp(self):
        category = Category.objects.create(name='Back End', slug='back-end')
        self.lab = Lab.objects.create(title='Listes', status=Lab.Status.PUBLISHED)
        self.other_lab = Lab.objects.create(title='Dictionnaires', status=Lab.Status.PUBLISHED)
        self.course = create_course('Python', category, self.lab)
        self.second_course = create_course('Python avancé', category, self.lab)
        self.lab_lesson = Lesson.objects.get(module__course=self.course, lesson_type='LAB')

    def send(self, user_id=USER_ID, lab=None):
        activity_completed.send(sender=Lab, user_id=user_id, lab=lab or self.lab, score=100)

    def test_lab_lesson_is_completed_when_enrolled(self):
        enrollment = Enrollment.objects.create(user_id=USER_ID, course=self.course)
        self.send()
        progress = LessonProgress.objects.get(enrollment=enrollment, lesson=self.lab_lesson)
        self.assertTrue(progress.is_completed)
        self.assertIsNotNone(progress.completed_at)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress_percentage, Decimal('25.00'))

    def test_nothing_happens_when_not_enrolled(self):
        self.send()
        self.assertFalse(LessonProgress.objects.exists())

    def test_only_the_user_enrollments_are_touched(self):
        Enrollment.objects.create(user_id=OTHER_USER_ID, course=self.course)
        self.send()
        self.assertFalse(LessonProgress.objects.exists())

    def test_every_enrolled_course_using_the_lab_is_updated(self):
        Enrollment.objects.create(user_id=USER_ID, course=self.course)
        Enrollment.objects.create(user_id=USER_ID, course=self.second_course)
        self.send()
        self.assertEqual(LessonProgress.objects.filter(is_completed=True).count(), 2)

    def test_suspended_enrollment_is_ignored(self):
        Enrollment.objects.create(user_id=USER_ID, course=self.course, status='suspended')
        self.send()
        self.assertFalse(LessonProgress.objects.exists())

    def test_another_lab_does_not_complete_the_lesson(self):
        Enrollment.objects.create(user_id=USER_ID, course=self.course)
        self.send(lab=self.other_lab)
        self.assertFalse(LessonProgress.objects.exists())

    def test_completing_twice_creates_no_duplicate(self):
        Enrollment.objects.create(user_id=USER_ID, course=self.course)
        self.send()
        first = LessonProgress.objects.get().completed_at
        self.send()
        self.assertEqual(LessonProgress.objects.count(), 1)
        self.assertEqual(LessonProgress.objects.get().completed_at, first)

    def test_signal_without_activity_is_ignored(self):
        Enrollment.objects.create(user_id=USER_ID, course=self.course)
        activity_completed.send(sender=Lab, user_id=USER_ID, score=100)
        self.assertFalse(LessonProgress.objects.exists())

    # --- Rattrapage à l'inscription -------------------------------------------

    def complete_lab_in_labs(self, user_id=USER_ID, status=UserProgress.Status.COMPLETED):
        UserProgress.objects.create(user_id=user_id, lab=self.lab, status=status)

    def test_new_enrollment_catches_up_labs_already_completed(self):
        self.complete_lab_in_labs()
        enrollment = Enrollment.objects.create(user_id=USER_ID, course=self.course)
        progress = LessonProgress.objects.get(enrollment=enrollment)
        self.assertEqual(progress.lesson, self.lab_lesson)
        self.assertTrue(progress.is_completed)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress_percentage, Decimal('25.00'))

    def test_catch_up_ignores_labs_in_progress_and_other_users(self):
        self.complete_lab_in_labs(status=UserProgress.Status.IN_PROGRESS)
        self.complete_lab_in_labs(user_id=OTHER_USER_ID)
        Enrollment.objects.create(user_id=USER_ID, course=self.course)
        self.assertFalse(LessonProgress.objects.exists())

    def test_updating_an_enrollment_does_not_trigger_catch_up(self):
        enrollment = Enrollment.objects.create(user_id=USER_ID, course=self.course)
        self.complete_lab_in_labs()
        enrollment.status = 'completed'
        enrollment.save()
        self.assertFalse(LessonProgress.objects.exists())

    def test_enrollments_created_signal_catches_up(self):
        self.complete_lab_in_labs()
        enrollments = Enrollment.objects.bulk_create([Enrollment(user_id=USER_ID, course=self.course)])
        self.assertFalse(LessonProgress.objects.exists())  # bulk_create n'émet pas post_save
        enrollments_created.send(sender=Enrollment, enrollments=enrollments)
        self.assertTrue(LessonProgress.objects.get().is_completed)

    def test_paid_order_catches_up_labs_already_completed(self):
        """Parcours réel : le paiement crée les inscriptions par bulk_create."""
        self.complete_lab_in_labs()
        order = Order.objects.create(user_id=USER_ID, user_email='s@qavaa.com', total_amount='10.00')
        OrderItem.objects.create(order=order, course=self.course, price_paid='10.00')
        provider = PaymentProvider.objects.create(name='Qavaa', code='QAVAA')
        Payment.objects.create(order=order, provider=provider, amount='10.00', transaction_reference='tx_1')

        PaymentService.fulfill_payment_success('tx_1', {'status': 'SUCCESS'}, amount_paid='10.00')

        enrollment = Enrollment.objects.get(user_id=USER_ID, course=self.course)
        progress = LessonProgress.objects.get(enrollment=enrollment)
        self.assertEqual(progress.lesson, self.lab_lesson)
        self.assertTrue(progress.is_completed)
