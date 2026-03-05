from django.contrib.auth.models import User
from django.test import TestCase

from .models import KeyTransaction, KeyWallet
from .service import award, award_test_pass, get_or_create_wallet, spend


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_user(username='rewarduser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)


# ─── award() ─────────────────────────────────────────────────────────────────

class AwardTests(TestCase):

    def test_award_increases_balance(self):
        user = make_user('aw1')
        new_balance = award(user, 10, 'test_pass')
        self.assertEqual(new_balance, 10)
        wallet = get_or_create_wallet(user)
        self.assertEqual(wallet.balance, 10)

    def test_award_creates_transaction(self):
        user = make_user('aw2')
        award(user, 5, 'test_pass')
        wallet = get_or_create_wallet(user)
        tx = KeyTransaction.objects.filter(wallet=wallet).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, 5)
        self.assertEqual(tx.balance_after, 5)

    def test_award_zero_does_nothing(self):
        user = make_user('aw3')
        new_balance = award(user, 0, 'test_pass')
        self.assertEqual(new_balance, 0)
        wallet = get_or_create_wallet(user)
        self.assertFalse(KeyTransaction.objects.filter(wallet=wallet).exists())

    def test_award_accumulates(self):
        user = make_user('aw4')
        award(user, 10, 'test_pass')
        new_balance = award(user, 5, 'daily_visit')
        self.assertEqual(new_balance, 15)

    def test_balance_after_is_cumulative(self):
        user = make_user('aw5')
        award(user, 10, 'test_pass')
        award(user, 5, 'daily_visit')
        wallet = get_or_create_wallet(user)
        txs = list(KeyTransaction.objects.filter(wallet=wallet).order_by('id'))
        self.assertEqual(txs[0].balance_after, 10)
        self.assertEqual(txs[1].balance_after, 15)


# ─── spend() ─────────────────────────────────────────────────────────────────

class SpendTests(TestCase):

    def test_spend_sufficient_balance(self):
        user = make_user('sp1')
        award(user, 20, 'test_pass')
        success, new_balance = spend(user, 10, 'unlock')
        self.assertTrue(success)
        self.assertEqual(new_balance, 10)

    def test_spend_creates_negative_transaction(self):
        user = make_user('sp2')
        award(user, 20, 'test_pass')
        spend(user, 10, 'unlock')
        wallet = get_or_create_wallet(user)
        tx = KeyTransaction.objects.filter(wallet=wallet, amount__lt=0).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, -10)
        self.assertEqual(tx.balance_after, 10)

    def test_spend_insufficient_balance_returns_false(self):
        user = make_user('sp3')
        award(user, 5, 'test_pass')
        success, balance = spend(user, 10, 'unlock')
        self.assertFalse(success)
        self.assertEqual(balance, 5)

    def test_spend_insufficient_does_not_change_balance(self):
        user = make_user('sp4')
        award(user, 5, 'test_pass')
        spend(user, 10, 'unlock')
        wallet = get_or_create_wallet(user)
        self.assertEqual(wallet.balance, 5)

    def test_spend_zero_succeeds_without_transaction(self):
        user = make_user('sp5')
        success, balance = spend(user, 0, 'unlock')
        self.assertTrue(success)
        wallet = get_or_create_wallet(user)
        self.assertFalse(KeyTransaction.objects.filter(wallet=wallet).exists())

    def test_spend_exact_balance(self):
        user = make_user('sp6')
        award(user, 10, 'test_pass')
        success, balance = spend(user, 10, 'unlock')
        self.assertTrue(success)
        self.assertEqual(balance, 0)


# ─── award_test_pass() ────────────────────────────────────────────────────────

class AwardTestPassTests(TestCase):

    def test_award_test_pass_uses_settings_amount(self):
        from .models import KeySettings
        settings = KeySettings.get()
        user = make_user('tp1')
        new_balance = award_test_pass(user)
        self.assertEqual(new_balance, settings.test_pass_award)

    def test_award_test_pass_creates_transaction(self):
        user = make_user('tp2')
        award_test_pass(user)
        wallet = get_or_create_wallet(user)
        self.assertTrue(KeyTransaction.objects.filter(wallet=wallet).exists())
