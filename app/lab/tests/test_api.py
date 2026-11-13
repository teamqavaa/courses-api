import json
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from core.sso import SSOUser

from lab.models import (
    Lab,
    LabObjective,
    LabSession,
    RateLimit,
    Skill,
    SkillOutcome,
    SkillPrerequisite,
    UserProgress,
)


class FakeUser:
    is_authenticated = True

    def __init__(self, user_id='sso-user-1'):
        self.id = user_id


class LabCatalogTests(APITestCase):
    def setUp(self):
        self.skill = Skill.objects.create(
            title='Lists',
            slug='lists',
            description='Python lists',
        )
        self.published = Lab.objects.create(
            title='Intro to Lists',
            description='',
            language=Lab.Language.PYTHON,
            difficulty=Lab.Difficulty.GUIDED,
            status=Lab.Status.PUBLISHED,
        )
        self.published.skills.add(self.skill)
        LabObjective.objects.create(
            lab=self.published,
            order=1,
            title='Create a list',
            content='Create a list.',
            starter_code='items = []',
        )
        self.draft = Lab.objects.create(
            title='Draft lab',
            status=Lab.Status.DRAFT,
        )

    def test_public_list_only_returns_published_labs(self):
        response = self.client.get('/api/labs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([lab['title'] for lab in response.data], ['Intro to Lists'])
        self.assertEqual(response.data[0]['slug'], 'intro-to-lists')
        self.assertEqual(len(response.data[0]['objectives']), 1)

    def test_public_list_can_filter_by_skill(self):
        response = self.client.get('/api/labs/?skill=lists')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['skill_slugs'], ['lists'])

    def test_public_detail_returns_objectives(self):
        response = self.client.get(f'/api/labs/{self.published.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Intro to Lists')
        self.assertEqual(response.data['slug'], 'intro-to-lists')
        self.assertEqual(response.data['skill_slugs'], ['lists'])

    def test_public_detail_accepts_legacy_uuid(self):
        response = self.client.get(f'/api/labs/{self.published.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['slug'], 'intro-to-lists')

    def test_draft_detail_is_not_public(self):
        response = self.client.get(f'/api/labs/{self.draft.slug}/')
        self.assertEqual(response.status_code, 404)

    def test_slug_is_unique_across_labs(self):
        duplicate = Lab.objects.create(
            title='Intro to Lists',
            status=Lab.Status.DRAFT,
        )

        self.assertEqual(duplicate.slug, 'intro-to-lists-2')

    def test_skills_include_lab_count(self):
        response = self.client.get('/api/skills/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['lab_count'], 1)
        self.assertEqual(response.data[0]['title'], 'Lists')


def sso_user(user_id='sso-user-1', roles=('student',), **claims):
    """Utilisateur SSO tel que construit depuis le token (core/sso.py)."""
    return SSOUser({'sub': user_id, 'email': f'{user_id}@qavaa.com', 'name': user_id, 'roles': list(roles), **claims})


class LabManagementTests(APITestCase):
    """Droits sur les labs : étudiant (lecture), instructeur (ses labs), admin / is_staff / is_superuser (tous)."""

    def setUp(self):
        self.student = sso_user('student-1')
        self.instructor = sso_user('instructor-1', roles=['instructor'])
        self.other_instructor = sso_user('instructor-2', roles=['instructor'])
        self.published = Lab.objects.create(title='Public lab', status=Lab.Status.PUBLISHED)
        self.own_draft = Lab.objects.create(title='Own draft', user_id='instructor-1')
        self.other_draft = Lab.objects.create(title='Other draft', user_id='instructor-2')
        LabObjective.objects.create(lab=self.own_draft, order=1, title='Step 1', content='Do it')

    def titles(self, response):
        return sorted(lab['title'] for lab in response.data)

    def test_admin_variants_see_every_lab(self):
        for admin in (
            sso_user('admin-1', roles=['admin']),
            sso_user('admin-2', roles=['superuser']),
            sso_user('staff-1', is_staff=True),
            sso_user('root-1', is_superuser=True),
        ):
            self.client.force_authenticate(user=admin)
            self.assertEqual(
                self.titles(self.client.get('/api/labs/')),
                ['Other draft', 'Own draft', 'Public lab'],
            )
            self.assertEqual(len(self.client.get('/api/labs/manage/').data), 3)
            detail = self.client.get(f'/api/labs/{self.other_draft.slug}/')
            self.assertEqual(detail.status_code, 200)
            self.assertIn('user_email', detail.data)

    def test_student_sees_published_labs_only(self):
        self.client.force_authenticate(user=self.student)
        self.assertEqual(self.titles(self.client.get('/api/labs/')), ['Public lab'])
        self.assertNotIn('user_email', self.client.get(f'/api/labs/{self.published.slug}/').data)
        self.assertEqual(self.client.get(f'/api/labs/{self.own_draft.slug}/').status_code, 404)
        self.assertEqual(self.client.get('/api/labs/manage/').status_code, 403)
        self.assertEqual(self.client.post('/api/labs/', {'title': 'Nope'}, format='json').status_code, 403)

    def test_anonymous_cannot_write(self):
        self.assertEqual(self.client.post('/api/labs/', {'title': 'Nope'}, format='json').status_code, 401)
        response = self.client.patch(f'/api/labs/{self.published.slug}/', {'title': 'X'}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_instructor_sees_and_manages_only_own_labs(self):
        self.client.force_authenticate(user=self.instructor)
        self.assertEqual(self.titles(self.client.get('/api/labs/')), ['Own draft', 'Public lab'])
        self.assertEqual(self.titles(self.client.get('/api/labs/manage/')), ['Own draft'])
        self.assertEqual(self.client.get(f'/api/labs/{self.other_draft.slug}/').status_code, 404)
        response = self.client.patch(f'/api/labs/{self.published.slug}/', {'title': 'Hijack'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.delete(f'/api/labs/{self.published.slug}/').status_code, 403)

    def test_instructor_creates_lab_with_steps(self):
        self.client.force_authenticate(user=self.instructor)
        skill = Skill.objects.create(title='Loops', slug='loops')
        response = self.client.post('/api/labs/', {
            'title': 'Manage',
            'language': 'php',
            'skills': [str(skill.id)],
            'objectives': [
                {'title': 'First', 'content': 'One'},
                {'title': 'Second', 'content': 'Two', 'hint': 'Look', 'starter_code': '<?php'},
            ],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user_id'], 'instructor-1')
        self.assertEqual(response.data['status'], 'draft')
        self.assertEqual(response.data['slug'], 'manage-2')  # "manage" est réservé
        self.assertEqual(response.data['skill_slugs'], ['loops'])
        self.assertEqual([o['order'] for o in response.data['objectives']], [1, 2])

    def test_instructor_cannot_publish(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post('/api/labs/', {'title': 'X', 'status': 'published'}, format='json')
        self.assertEqual(response.status_code, 403)
        url = f'/api/labs/{self.own_draft.slug}/status/'
        self.assertEqual(self.client.post(url, {'status': 'review'}, format='json').status_code, 200)
        self.assertEqual(self.client.post(url, {'status': 'published'}, format='json').status_code, 403)

    def test_update_syncs_objectives(self):
        self.client.force_authenticate(user=self.instructor)
        step = self.own_draft.objectives.get()
        response = self.client.patch(f'/api/labs/{self.own_draft.slug}/', {
            'title': 'Renamed',
            'objectives': [
                {'title': 'New first', 'content': 'A'},
                {'id': str(step.id), 'title': 'Step 1 edited', 'content': 'B'},
            ],
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Renamed')
        self.assertEqual(response.data['slug'], 'own-draft')  # le slug ne change pas
        objectives = list(self.own_draft.objectives.order_by('order'))
        self.assertEqual([o.title for o in objectives], ['New first', 'Step 1 edited'])
        self.assertEqual(objectives[1].id, step.id)

    def test_admin_publishes_and_deletes_any_lab(self):
        self.client.force_authenticate(user=sso_user('staff-1', is_staff=True))
        url = f'/api/labs/{self.other_draft.slug}/'
        response = self.client.post(f'{url}status/', {'status': 'published'}, format='json')
        self.assertEqual(response.data['status'], 'published')
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Lab.objects.filter(pk=self.other_draft.pk).exists())

    def test_instructor_cannot_delete_a_lab_learners_started(self):
        LabSession.objects.create(user_id='student-1', lab=self.own_draft)
        self.client.force_authenticate(user=self.instructor)
        self.assertEqual(self.client.delete(f'/api/labs/{self.own_draft.slug}/').status_code, 409)

    def test_owner_can_practise_own_draft(self):
        self.client.force_authenticate(user=self.instructor)
        self.assertEqual(self.client.get(f'/api/sessions/{self.own_draft.id}/').status_code, 200)
        self.client.force_authenticate(user=self.student)
        self.assertEqual(self.client.get(f'/api/sessions/{self.own_draft.id}/').status_code, 404)


class LabSessionTests(APITestCase):
    def setUp(self):
        self.user = FakeUser()
        self.lab = Lab.objects.create(
            title='Intro to Lists',
            description='',
            language=Lab.Language.PYTHON,
            difficulty=Lab.Difficulty.GUIDED,
            status=Lab.Status.PUBLISHED,
        )
        LabObjective.objects.create(
            lab=self.lab,
            order=1,
            title='Step one',
            content='Do the first thing.',
        )
        LabObjective.objects.create(
            lab=self.lab,
            order=2,
            title='Step two',
            content='Do the second thing.',
        )
        self.client.force_authenticate(user=self.user)

    def test_session_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/sessions/{self.lab.id}/')
        self.assertIn(response.status_code, (401, 403))

    def test_session_starts_empty_without_creating_a_row(self):
        response = self.client.get(f'/api/sessions/{self.lab.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'not_started')
        self.assertIsNone(response.data['current_code'])
        self.assertFalse(LabSession.objects.exists())

    def test_save_creates_session_and_progress(self):
        response = self.client.post(
            f'/api/sessions/{self.lab.id}/',
            {'current_code': 'print(1)', 'completed_steps': 1},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], LabSession.Status.ACTIVE)
        session = LabSession.objects.get(user_id=self.user.id, lab=self.lab)
        self.assertEqual(session.current_code, 'print(1)')
        progress = UserProgress.objects.get(user_id=self.user.id, lab=self.lab)
        self.assertEqual(progress.completed_steps, 1)
        self.assertEqual(progress.attempts, 1)
        self.assertEqual(progress.status, UserProgress.Status.IN_PROGRESS)

    def test_save_does_not_reopen_a_completed_session(self):
        self.client.post(
            f'/api/sessions/{self.lab.id}/',
            {'current_code': 'print(1)'},
            format='json',
        )
        self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        response = self.client.post(
            f'/api/sessions/{self.lab.id}/',
            {'current_code': 'print(2)'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        session = LabSession.objects.get(user_id=self.user.id, lab=self.lab)
        self.assertEqual(session.status, LabSession.Status.COMPLETED)
        self.assertEqual(session.current_code, 'print(2)')
        progress = UserProgress.objects.get(user_id=self.user.id, lab=self.lab)
        self.assertEqual(progress.status, UserProgress.Status.COMPLETED)

    def test_save_accumulates_practice_time(self):
        self.client.post(
            f'/api/sessions/{self.lab.id}/',
            {'current_code': 'print(1)'},
            format='json',
        )
        LabSession.objects.filter(user_id=self.user.id, lab=self.lab).update(
            last_active_at=timezone.now() - timedelta(minutes=5)
        )
        response = self.client.post(
            f'/api/sessions/{self.lab.id}/',
            {'current_code': 'print(2)'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        progress = UserProgress.objects.get(user_id=self.user.id, lab=self.lab)
        self.assertGreaterEqual(progress.seconds_practiced, 290)
        self.assertLessEqual(progress.seconds_practiced, 310)

    def test_complete_uncomplete_and_reset(self):
        self.client.post(
            f'/api/sessions/{self.lab.id}/',
            {'completed_steps': 2},
            format='json',
        )
        response = self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        self.assertEqual(response.status_code, 200)
        session = LabSession.objects.get(user_id=self.user.id, lab=self.lab)
        self.assertEqual(session.status, LabSession.Status.COMPLETED)
        self.assertIsNotNone(session.completed_at)
        progress = UserProgress.objects.get(user_id=self.user.id, lab=self.lab)
        self.assertEqual(progress.status, UserProgress.Status.COMPLETED)

        response = self.client.post(f'/api/sessions/{self.lab.id}/uncomplete/')
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.status, LabSession.Status.ACTIVE)
        self.assertIsNone(session.completed_at)
        progress.refresh_from_db()
        self.assertEqual(progress.status, UserProgress.Status.IN_PROGRESS)

        response = self.client.post(f'/api/sessions/{self.lab.id}/reset/')
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        progress.refresh_from_db()
        self.assertEqual(session.status, LabSession.Status.ACTIVE)
        self.assertIsNone(session.current_code)
        self.assertEqual(progress.status, UserProgress.Status.IN_PROGRESS)
        self.assertEqual(progress.attempts, 0)
        self.assertEqual(progress.completed_steps, 0)

    def test_heartbeat_accumulates_practice_time(self):
        self.client.post(
            f'/api/sessions/{self.lab.id}/',
            {'current_code': 'print(1)'},
            format='json',
        )
        LabSession.objects.filter(user_id=self.user.id, lab=self.lab).update(
            last_active_at=timezone.now() - timedelta(minutes=3)
        )
        response = self.client.post(f'/api/sessions/{self.lab.id}/heartbeat/')
        self.assertEqual(response.status_code, 200)
        progress = UserProgress.objects.get(user_id=self.user.id, lab=self.lab)
        self.assertGreaterEqual(progress.seconds_practiced, 170)

    def test_heartbeat_without_session_returns_404(self):
        response = self.client.post(f'/api/sessions/{self.lab.id}/heartbeat/')
        self.assertEqual(response.status_code, 404)

    def test_uncomplete_without_session_returns_404(self):
        response = self.client.post(f'/api/sessions/{self.lab.id}/uncomplete/')
        self.assertEqual(response.status_code, 404)

    def test_progress_detail_and_list(self):
        self.client.post(
            f'/api/sessions/{self.lab.id}/',
            {'completed_steps': 1},
            format='json',
        )
        detail = self.client.get(f'/api/progress/{self.lab.id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['completed_steps'], 1)
        self.assertEqual(detail.data['total_steps'], 2)
        self.assertEqual(detail.data['progress_percent'], 50)
        self.assertEqual(detail.data['status'], UserProgress.Status.IN_PROGRESS)

        listing = self.client.get('/api/progress/')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)
        self.assertEqual(str(listing.data[0]['lab_id']), str(self.lab.id))

    def test_progress_detail_starts_not_started(self):
        response = self.client.get(f'/api/progress/{self.lab.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'not_started')
        self.assertEqual(response.data['progress_percent'], 0)

    def test_stats_start_at_zero(self):
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['labs_completed'], 0)
        self.assertEqual(response.data['hours_practiced'], 0)
        self.assertEqual(len(response.data['week']), 7)

    def test_stats_count_completed_lab(self):
        self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['labs_completed'], 1)
        self.assertEqual(response.data['current_streak'], 1)
        today_index = timezone.now().date().weekday()
        self.assertTrue(response.data['week'][today_index]['practiced'])
        self.assertTrue(response.data['week'][today_index]['is_today'])


class LabExecutionTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(user=FakeUser())
        self.payload = {
            'language': 'python',
            'version': '3.12.0',
            'filename': 'main.py',
            'code': 'print(1)',
        }

    @patch('lab.views.execution.requests.post')
    def test_execute_returns_piston_output(self, post):
        piston_response = Mock()
        piston_response.status_code = 200
        piston_response.json.return_value = {
            'language': 'python',
            'version': '3.12.0',
            'run': {'stdout': '1\n', 'stderr': '', 'code': 0},
        }
        post.return_value = piston_response

        response = self.client.post('/api/execute/', self.payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['run']['stdout'], '1\n')

    @patch('lab.views.execution.requests.post')
    def test_execute_is_rate_limited_after_ten_requests(self, post):
        piston_response = Mock()
        piston_response.status_code = 200
        piston_response.json.return_value = {'run': {'stdout': '', 'stderr': '', 'code': 0}}
        post.return_value = piston_response

        for _ in range(10):
            response = self.client.post('/api/execute/', self.payload, format='json')
            self.assertEqual(response.status_code, 200)

        response = self.client.post('/api/execute/', self.payload, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(RateLimit.objects.get(pk='sso-user-1').request_count, 10)

    def test_execute_rejects_unknown_language(self):
        payload = {**self.payload, 'language': 'ruby'}
        response = self.client.post('/api/execute/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(RateLimit.objects.exists())

    def test_execute_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/execute/', self.payload, format='json')
        self.assertIn(response.status_code, (401, 403))


class CatalogImportTests(TestCase):
    def _fixture(self, models):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / 'catalog.json'
        path.write_text(json.dumps(models), encoding='utf-8')
        self.addCleanup(directory.cleanup)
        return path

    def test_import_loads_catalog_only(self):
        skill_id = str(uuid.uuid4())
        lab_id = str(uuid.uuid4())
        objective_id = str(uuid.uuid4())
        path = self._fixture([
            {
                'model': 'lab.skill',
                'pk': skill_id,
                'fields': {
                    'title': 'Lists',
                    'slug': 'lists',
                    'description': '',
                    'icon': '',
                    'order': 1,
                    'is_active': True,
                    'duration_weeks': 2,
                    'pace': 'self-paced',
                    'includes_certificate': False,
                    'created_at': '2026-01-01T00:00:00Z',
                },
            },
            {
                'model': 'lab.skilloutcome',
                'pk': 1,
                'fields': {
                    'skill': skill_id,
                    'order': 1,
                    'content': 'Understand lists.',
                },
            },
            {
                'model': 'lab.skillprerequisite',
                'pk': 1,
                'fields': {
                    'skill': skill_id,
                    'order': 1,
                    'content': 'Know variables.',
                },
            },
            {
                'model': 'lab.lab',
                'pk': lab_id,
                'fields': {
                    'title': 'Intro to Lists',
                    'description': '',
                    'language': 'python',
                    'status': 'published',
                    'difficulty': 'guided',
                    'starter_code': '',
                    'skills': [skill_id],
                    'created_at': '2026-01-01T00:00:00Z',
                },
            },
            {
                'model': 'lab.labobjective',
                'pk': objective_id,
                'fields': {
                    'lab': lab_id,
                    'order': 1,
                    'title': 'Step one',
                    'content': 'Do it.',
                    'hint': None,
                    'starter_code': '',
                },
            },
        ])

        call_command('import_drl_catalog', str(path), verbosity=0)

        self.assertEqual(Skill.objects.count(), 1)
        self.assertEqual(SkillOutcome.objects.count(), 1)
        self.assertEqual(SkillPrerequisite.objects.count(), 1)
        self.assertEqual(Lab.objects.count(), 1)
        self.assertEqual(LabObjective.objects.count(), 1)
        self.assertEqual(Lab.objects.get().slug, 'intro-to-lists')
        self.assertEqual(Lab.objects.get().skills.get().slug, 'lists')
        self.assertEqual(Skill.objects.get().title, 'Lists')

    def test_import_preserves_existing_slug(self):
        lab_id = str(uuid.uuid4())
        Lab.objects.create(
            id=lab_id,
            title='Old title',
            slug='stable-slug',
            status=Lab.Status.PUBLISHED,
        )
        path = self._fixture([
            {
                'model': 'lab.lab',
                'pk': lab_id,
                'fields': {
                    'title': 'New title',
                    'description': '',
                    'language': 'python',
                    'status': 'published',
                    'difficulty': 'guided',
                    'starter_code': '',
                    'skills': [],
                    'created_at': '2026-01-01T00:00:00Z',
                },
            },
        ])

        call_command('import_drl_catalog', str(path), verbosity=0)

        lab = Lab.objects.get(pk=lab_id)
        self.assertEqual(lab.title, 'New title')
        self.assertEqual(lab.slug, 'stable-slug')

    def test_import_rejects_user_data(self):
        path = self._fixture([
            {
                'model': 'users.user',
                'pk': 1,
                'fields': {'email': 'legacy@example.com'},
            },
        ])
        with self.assertRaises(CommandError):
            call_command('import_drl_catalog', str(path), verbosity=0)
