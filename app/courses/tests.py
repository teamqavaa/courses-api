"""
Tests de la gestion des cours par les instructeurs et les administrateurs :
visibilité selon le statut, CRUD, workflow de validation (draft -> review -> published)
et édition du programme (modules, leçons, vidéos) réservée au propriétaire du cours.
"""
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from categories.models import Category
from core.sso import SSOUser
from core.tests import FakeSigningKey, make_token
from lessons.models import Lesson
from modules.models import Module
from order_items.models import OrderItem
from orders.models import Order
from .models import Course

INSTRUCTOR_ID = '00000000-0000-0000-0000-00000000000a'
OTHER_INSTRUCTOR_ID = '00000000-0000-0000-0000-00000000000b'
ADMIN_ID = '00000000-0000-0000-0000-00000000000c'
STUDENT_ID = '00000000-0000-0000-0000-00000000000d'


def auth_client(sub, roles, **claims):
    client = APIClient()
    token = make_token(sub=sub, roles=roles, email=f'{sub[-1]}@qavaa.com', **claims)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


class SSOUserAdminFlagsTests(TestCase):

    def test_staff_and_superuser_claims_are_admins(self):
        self.assertTrue(SSOUser({'sub': ADMIN_ID, 'roles': [], 'is_staff': True}).is_admin)
        self.assertTrue(SSOUser({'sub': ADMIN_ID, 'roles': [], 'is_superuser': True}).is_admin)
        self.assertTrue(SSOUser({'sub': ADMIN_ID, 'roles': ['superadmin']}).is_admin)
        self.assertFalse(SSOUser({'sub': ADMIN_ID, 'roles': ['student'], 'is_staff': False}).is_admin)


@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class CourseManagementTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(name='Développement', slug='developpement')
        self.instructor = auth_client(INSTRUCTOR_ID, ['instructor'])
        self.other_instructor = auth_client(OTHER_INSTRUCTOR_ID, ['instructor'])
        self.admin = auth_client(ADMIN_ID, ['student'], is_staff=True)
        self.student = auth_client(STUDENT_ID, ['student'])
        self.published = self._course('Python publié', INSTRUCTOR_ID, 'published')
        self.draft = self._course('Brouillon instructeur', INSTRUCTOR_ID, 'draft')
        self.other_draft = self._course('Brouillon autre', OTHER_INSTRUCTOR_ID, 'review')

    def _course(self, title, owner, status):
        return Course.objects.create(
            category=self.category, title=title, description='desc', price='20.00',
            user_id=owner, user_email='owner@qavaa.com', status=status,
        )

    def _payload(self, **extra):
        return {
            'title': 'Nouveau cours', 'description': 'Description', 'price': '15.00',
            'category': str(self.category.id), 'level': 'beginner', **extra,
        }

    # --- Visibilité ---

    def test_public_catalog_only_lists_published_courses(self, _):
        res = APIClient().get('/api/courses/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual([c['slug'] for c in res.data], [self.published.slug])

    def test_draft_course_is_hidden_from_public_detail(self, _):
        self.assertEqual(APIClient().get(f'/api/courses/{self.draft.slug}/').status_code, 404)
        self.assertEqual(self.instructor.get(f'/api/courses/{self.draft.slug}/').status_code, 200)

    def test_invalid_token_still_reads_public_catalog(self, _):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer invalide')
        self.assertEqual(client.get('/api/courses/').status_code, 200)

    def test_manage_lists_own_courses_for_instructor(self, _):
        res = self.instructor.get('/api/courses/manage/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual({c['slug'] for c in res.data}, {self.published.slug, self.draft.slug})
        self.assertIn('lessons_count', res.data[0])

    def test_manage_lists_all_courses_for_admin_with_filters(self, _):
        res = self.admin.get('/api/courses/manage/')
        self.assertEqual(len(res.data), 3)
        res = self.admin.get('/api/courses/manage/?status=review')
        self.assertEqual([c['slug'] for c in res.data], [self.other_draft.slug])

    def test_manage_is_forbidden_for_students(self, _):
        self.assertEqual(self.student.get('/api/courses/manage/').status_code, 403)
        self.assertIn(APIClient().get('/api/courses/manage/').status_code, (401, 403))

    # --- Création / modification / suppression ---

    def test_student_cannot_create_course(self, _):
        res = self.student.post('/api/courses/', self._payload(), format='json')
        self.assertEqual(res.status_code, 403)

    def test_anonymous_cannot_create_course(self, _):
        res = APIClient().post('/api/courses/', self._payload(), format='json')
        self.assertIn(res.status_code, (401, 403))

    def test_instructor_creates_draft_course_owned_by_him(self, _):
        res = self.instructor.post('/api/courses/', self._payload(), format='json')
        self.assertEqual(res.status_code, 201, res.data)
        course = Course.objects.get(slug=res.data['slug'])
        self.assertEqual(course.user_id, INSTRUCTOR_ID)
        self.assertEqual(course.status, 'draft')

    def test_instructor_cannot_publish(self, _):
        res = self.instructor.post('/api/courses/', self._payload(status='published'), format='json')
        self.assertEqual(res.status_code, 403)
        res = self.instructor.patch(f'/api/courses/{self.draft.slug}/', {'status': 'published'}, format='json')
        self.assertEqual(res.status_code, 403)

    def test_instructor_updates_and_deletes_own_course(self, _):
        res = self.instructor.patch(f'/api/courses/{self.draft.slug}/', {'title': 'Titre modifié'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['title'], 'Titre modifié')
        self.assertEqual(self.instructor.delete(f'/api/courses/{self.draft.slug}/').status_code, 204)

    def test_instructor_cannot_touch_other_instructor_course(self, _):
        url = f'/api/courses/{self.other_draft.slug}/'
        self.assertIn(self.instructor.patch(url, {'title': 'x'}, format='json').status_code, (403, 404))
        self.assertIn(self.instructor.delete(url).status_code, (403, 404))
        self.assertTrue(Course.objects.filter(pk=self.other_draft.pk).exists())

    def test_admin_updates_and_deletes_any_course(self, _):
        url = f'/api/courses/{self.other_draft.slug}/'
        self.assertEqual(self.admin.patch(url, {'title': 'Par admin'}, format='json').status_code, 200)
        self.assertEqual(self.admin.delete(url).status_code, 204)

    def test_ordered_course_cannot_be_deleted(self, _):
        order = Order.objects.create(user_id=STUDENT_ID, user_email='s@qavaa.com', total_amount='20.00')
        OrderItem.objects.create(order=order, course=self.published, price_paid='20.00')
        res = self.admin.delete(f'/api/courses/{self.published.slug}/')
        self.assertEqual(res.status_code, 409)
        self.assertIn('detail', res.data)

    # --- Workflow de validation ---

    def test_instructor_submits_course_for_review(self, _):
        res = self.instructor.post(f'/api/courses/{self.draft.slug}/status/', {'status': 'review'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, 'review')

    def test_instructor_cannot_validate_course(self, _):
        res = self.instructor.post(f'/api/courses/{self.draft.slug}/status/', {'status': 'published'}, format='json')
        self.assertEqual(res.status_code, 403)

    def test_admin_publishes_and_unpublishes(self, _):
        url = f'/api/courses/{self.other_draft.slug}/status/'
        self.assertEqual(self.admin.post(url, {'status': 'published'}, format='json').status_code, 200)
        self.other_draft.refresh_from_db()
        self.assertEqual(self.other_draft.status, 'published')
        self.assertEqual(self.admin.post(url, {'status': 'draft'}, format='json').data['status'], 'draft')

    def test_invalid_status_is_rejected(self, _):
        res = self.admin.post(f'/api/courses/{self.draft.slug}/status/', {'status': 'archived'}, format='json')
        self.assertEqual(res.status_code, 400)

    # --- Programme du cours ---

    def test_instructor_builds_curriculum_of_own_course(self, _):
        res = self.instructor.post('/api/modules/', {
            'course': str(self.draft.id), 'title': 'Bases', 'description': 'Intro', 'order': 1,
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        res = self.instructor.post('/api/lessons/', {
            'module': res.data['id'], 'title': 'Variables', 'order': 1, 'duration_in_minutes': 12,
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        res = self.instructor.post('/api/videos/', {
            'lesson': res.data['id'], 'title': 'Variables', 'provider': 'YOUTUBE',
            'video_url': 'https://www.youtube.com/watch?v=abc',
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)

    def test_instructor_cannot_edit_curriculum_of_other_course(self, _):
        res = self.instructor.post('/api/modules/', {
            'course': str(self.other_draft.id), 'title': 'Intrus', 'order': 1,
        }, format='json')
        self.assertEqual(res.status_code, 403)

        module = Module.objects.create(course=self.other_draft, title='M', order=1)
        lesson = Lesson.objects.create(module=module, title='L', order=1)
        url = f'/api/modules/{module.id}/'
        self.assertEqual(self.instructor.patch(url, {'title': 'x'}, format='json').status_code, 403)
        self.assertEqual(self.instructor.delete(f'/api/lessons/{lesson.id}/').status_code, 403)
        self.assertEqual(self.admin.delete(f'/api/lessons/{lesson.id}/').status_code, 204)

    def test_student_cannot_create_module(self, _):
        payload = {'course': str(self.published.id), 'title': 'x', 'order': 2}
        res = self.student.post('/api/modules/', payload, format='json')
        self.assertEqual(res.status_code, 403)
