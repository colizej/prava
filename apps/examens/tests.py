import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AnswerOption, ExamCategory, Question, TestAttempt


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_user(username='examuser', password='testpass123', **kwargs):
    return User.objects.create_user(username=username, password=password, **kwargs)


def make_category(name='Catégorie test', slug='cat-test'):
    return ExamCategory.objects.create(name=name, slug=slug)


def make_question(category, text='Question?'):
    q = Question.objects.create(category=category, text=text)
    AnswerOption.objects.create(question=q, letter='A', text='Oui', is_correct=True, order=0)
    AnswerOption.objects.create(question=q, letter='B', text='Non', is_correct=False, order=1)
    return q


def _make_answers(n_correct, n_wrong, q_id=1):
    answers = [{'question_id': q_id, 'is_correct': True}] * n_correct
    answers += [{'question_id': q_id, 'is_correct': False}] * n_wrong
    return answers


# ─── TestAttempt.calculate_results ────────────────────────────────────────────

class CalculateResultsTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def _attempt(self, answers):
        attempt = TestAttempt.objects.create(
            user=self.user,
            answers_data=answers,
            total_questions=len(answers),
        )
        attempt.calculate_results()
        attempt.refresh_from_db()
        return attempt

    def test_empty_answers_data_no_crash(self):
        """calculate_results() with empty list should be a no-op (early return)."""
        attempt = TestAttempt.objects.create(user=self.user, answers_data=[])
        attempt.calculate_results()  # must not raise
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 0)

    def test_pass_at_exactly_80_percent(self):
        answers = _make_answers(40, 10)  # 40/50 = 80%
        attempt = self._attempt(answers)
        self.assertEqual(attempt.score, 40)
        self.assertEqual(attempt.total_questions, 50)
        self.assertAlmostEqual(float(attempt.percentage), 80.0)
        self.assertTrue(attempt.passed)

    def test_fail_at_79_percent(self):
        answers = _make_answers(39, 11)  # 39/50 = 78%
        attempt = self._attempt(answers)
        self.assertFalse(attempt.passed)

    def test_full_score(self):
        answers = _make_answers(10, 0)
        attempt = self._attempt(answers)
        self.assertTrue(attempt.passed)
        self.assertAlmostEqual(float(attempt.percentage), 100.0)

    def test_zero_score(self):
        answers = _make_answers(0, 5)
        attempt = self._attempt(answers)
        self.assertFalse(attempt.passed)
        self.assertAlmostEqual(float(attempt.percentage), 0.0)

    def test_completed_at_is_set(self):
        answers = _make_answers(5, 5)
        attempt = self._attempt(answers)
        self.assertIsNotNone(attempt.completed_at)

    def test_time_spent_positive(self):
        answers = _make_answers(5, 5)
        attempt = self._attempt(answers)
        # started_at is auto_now_add; completed_at set in calculate_results
        self.assertGreaterEqual(attempt.time_spent, 0)


# ─── Question.record_answer ───────────────────────────────────────────────────

class RecordAnswerTests(TestCase):

    def setUp(self):
        cat = make_category()
        self.q = make_question(cat)

    def test_increments_times_answered(self):
        self.q.record_answer(True)
        self.q.refresh_from_db()
        self.assertEqual(self.q.times_answered, 1)

    def test_increments_times_correct_on_correct(self):
        self.q.record_answer(True)
        self.q.refresh_from_db()
        self.assertEqual(self.q.times_correct, 1)

    def test_does_not_increment_correct_on_wrong(self):
        self.q.record_answer(False)
        self.q.refresh_from_db()
        self.assertEqual(self.q.times_answered, 1)
        self.assertEqual(self.q.times_correct, 0)

    def test_success_rate_zero_when_no_answers(self):
        self.assertEqual(self.q.success_rate, 0)

    def test_success_rate_calculation(self):
        self.q.times_answered = 10
        self.q.times_correct = 7
        self.q.save(update_fields=['times_answered', 'times_correct'])
        self.assertEqual(self.q.success_rate, 70.0)


# ─── exam_mode view ───────────────────────────────────────────────────────────

class ExamModeViewTests(TestCase):

    def setUp(self):
        self.url = reverse('examens:exam')

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_non_premium_redirected_to_pricing(self):
        user = make_user('noprem')
        user.profile.is_premium = False
        user.profile.save(update_fields=['is_premium'])
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/pricing/', response['Location'])

    def test_staff_bypasses_premium_check(self):
        cat = make_category('ExamCat', 'exam-cat')
        # Create at least some questions so page doesn't crash
        for i in range(3):
            make_question(cat, f'Q{i}')
        user = make_user('staffexam', is_staff=True)
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_premium_user_gets_200(self):
        cat = make_category('ExamCat2', 'exam-cat-2')
        for i in range(3):
            make_question(cat, f'Q{i}')
        user = make_user('premuser')
        user.profile.is_premium = True
        user.profile.premium_until = None
        user.profile.save(update_fields=['is_premium', 'premium_until'])
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# ─── results view (ownership) ─────────────────────────────────────────────────

class ResultsOwnershipTests(TestCase):

    def test_owner_can_view(self):
        user = make_user('owner1')
        attempt = TestAttempt.objects.create(user=user, answers_data=[], total_questions=0)
        attempt.calculate_results()
        self.client.force_login(user)
        response = self.client.get(reverse('examens:results', kwargs={'uuid': attempt.uuid}))
        self.assertEqual(response.status_code, 200)

    def test_other_user_gets_404(self):
        owner = make_user('owner2')
        other = make_user('other2')
        attempt = TestAttempt.objects.create(user=owner, answers_data=[], total_questions=0)
        self.client.force_login(other)
        response = self.client.get(reverse('examens:results', kwargs={'uuid': attempt.uuid}))
        self.assertEqual(response.status_code, 404)


# ─── api_record_answer ────────────────────────────────────────────────────────

class ApiRecordAnswerTests(TestCase):

    def setUp(self):
        self.url = reverse('examens:api_record_answer')
        self.cat = make_category('APICat', 'api-cat')
        self.q = make_question(self.cat)
        self.user = make_user('apiuser')

    def test_unauthenticated_gets_302(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'question_id': self.q.id, 'is_correct': True}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_invalid_json_returns_400(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data='not-json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_question_returns_404(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            data=json.dumps({'question_id': 99999, 'is_correct': True}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_valid_answer_returns_ok(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            data=json.dumps({'question_id': self.q.id, 'is_correct': True}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')


# ─── api_finish_quiz ──────────────────────────────────────────────────────────

class ApiFinishQuizTests(TestCase):

    def setUp(self):
        self.url = reverse('examens:api_finish_quiz')
        self.user = make_user('finishuser')
        self.client.force_login(self.user)

    def test_creates_attempt_and_returns_uuid(self):
        answers = _make_answers(8, 2)
        response = self.client.post(
            self.url,
            data=json.dumps({'answers': answers}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('uuid', data)
        self.assertEqual(data['score'], 8)
        self.assertEqual(data['total'], 10)
        self.assertAlmostEqual(data['percentage'], 80.0)
        self.assertTrue(data['passed'])

    def test_unauthenticated_redirected(self):
        self.client.logout()
        response = self.client.post(
            self.url,
            data=json.dumps({'answers': []}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)
