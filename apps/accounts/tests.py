from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import DailyQuota, UserProfile


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_user(username='testuser', password='testpass123', **kwargs):
    return User.objects.create_user(username=username, password=password, **kwargs)


# ─── UserProfile.has_active_premium ───────────────────────────────────────────

class HasActivePremiumTests(TestCase):

    def test_false_when_is_premium_false(self):
        user = make_user('u1')
        user.profile.is_premium = False
        user.profile.save(update_fields=['is_premium'])
        self.assertFalse(user.profile.has_active_premium)

    def test_true_when_premium_no_expiry(self):
        """is_premium=True with no premium_until → infinite premium."""
        user = make_user('u2')
        user.profile.is_premium = True
        user.profile.premium_until = None
        user.profile.save(update_fields=['is_premium', 'premium_until'])
        self.assertTrue(user.profile.has_active_premium)

    def test_true_when_premium_future_expiry(self):
        user = make_user('u3')
        user.profile.is_premium = True
        user.profile.premium_until = timezone.now() + timedelta(days=30)
        user.profile.save(update_fields=['is_premium', 'premium_until'])
        self.assertTrue(user.profile.has_active_premium)

    def test_false_and_side_effect_when_expired(self):
        """Expired premium → returns False AND sets is_premium=False in DB."""
        user = make_user('u4')
        user.profile.is_premium = True
        user.profile.premium_until = timezone.now() - timedelta(seconds=1)
        user.profile.save(update_fields=['is_premium', 'premium_until'])

        result = user.profile.has_active_premium

        self.assertFalse(result)
        # Check the DB was updated too
        refreshed = UserProfile.objects.get(pk=user.profile.pk)
        self.assertFalse(refreshed.is_premium)


# ─── DailyQuota.can_answer ────────────────────────────────────────────────────

class DailyQuotaTests(TestCase):

    def test_staff_always_allowed(self):
        user = make_user('staff1', is_staff=True)
        can, quota = DailyQuota.can_answer(user)
        self.assertTrue(can)
        self.assertIsNone(quota)

    def test_superuser_always_allowed(self):
        user = make_user('super1', is_superuser=True)
        can, quota = DailyQuota.can_answer(user)
        self.assertTrue(can)
        self.assertIsNone(quota)

    def test_premium_user_always_allowed(self):
        user = make_user('prem1')
        user.profile.is_premium = True
        user.profile.premium_until = None
        user.profile.save(update_fields=['is_premium', 'premium_until'])
        can, quota = DailyQuota.can_answer(user)
        self.assertTrue(can)
        self.assertIsNone(quota)

    def test_free_user_allowed_under_limit(self):
        user = make_user('free1')
        can, quota = DailyQuota.can_answer(user)
        self.assertTrue(can)
        self.assertIsNotNone(quota)

    def test_free_user_blocked_when_exhausted(self):
        user = make_user('free2')
        quota = DailyQuota.get_or_create_today(user)
        quota.questions_answered = quota.max_questions
        quota.save(update_fields=['questions_answered'])
        can, q = DailyQuota.can_answer(user)
        self.assertFalse(can)

    def test_quota_date_rollover(self):
        """Yesterday's quota does not block today's questions."""
        user = make_user('free3')
        yesterday = (timezone.now() - timedelta(days=1)).date()
        old_quota = DailyQuota.objects.create(
            user=user,
            date=yesterday,
            questions_answered=15,
            max_questions=15,
        )
        # Today's quota should be fresh
        today_quota = DailyQuota.get_or_create_today(user)
        self.assertEqual(today_quota.questions_answered, 0)
        self.assertFalse(today_quota.is_exhausted)

    def test_remaining_decrements(self):
        user = make_user('free4')
        quota = DailyQuota.get_or_create_today(user)
        initial_remaining = quota.remaining
        quota.increment()
        quota.refresh_from_db()
        self.assertEqual(quota.remaining, initial_remaining - 1)


# ─── UserProfile.success_rate ────────────────────────────────────────────────

class SuccessRateTests(TestCase):

    def test_zero_when_no_answers(self):
        user = make_user('s1')
        self.assertEqual(user.profile.success_rate, 0)

    def test_correct_percentage(self):
        user = make_user('s2')
        user.profile.total_questions_answered = 10
        user.profile.correct_answers = 7
        user.profile.save(update_fields=['total_questions_answered', 'correct_answers'])
        self.assertEqual(user.profile.success_rate, 70.0)


# ─── Registration and auth views ─────────────────────────────────────────────

class RegisterViewTests(TestCase):

    def test_get_returns_200(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_profile(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass999!',
            'password2': 'SecurePass999!',
        })
        # Should redirect after success
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)

    def test_authenticated_user_redirected(self):
        user = make_user('existing')
        self.client.force_login(user)
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 302)


class LoginViewTests(TestCase):

    def test_get_returns_200(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirects(self):
        make_user('loginuser', password='pass123!')
        response = self.client.post(reverse('accounts:login'), {
            'username': 'loginuser',
            'password': 'pass123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_login_stays_on_page(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'nobody',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)


class ProfileViewTests(TestCase):

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    def test_profile_accessible_when_logged_in(self):
        user = make_user('puser')
        self.client.force_login(user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
