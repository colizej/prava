"""
Rewards models — Clés (🔑) gamification system.

KeySettings  — singleton, all parameters editable in admin
KeyWallet    — one per user, tracks balance + daily visit state
KeyTransaction — full audit log (positive = earn, negative = spend/decay)
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


# ---------------------------------------------------------------------------
# Singleton settings — all params editable from admin
# ---------------------------------------------------------------------------

class KeySettings(models.Model):
    """
    Singleton (pk=1).  All parameters of the keys system are here — no code
    changes needed to tweak values.
    """

    # ── Appearance ──────────────────────────────────────────────────────────
    icon = models.CharField(
        'Icône', max_length=10, default='🔑',
        help_text='Emoji ou caractère affiché comme monnaie',
    )
    currency_plural = models.CharField(
        'Nom (pluriel)', max_length=30, default='clés',
    )
    currency_singular = models.CharField(
        'Nom (singulier)', max_length=30, default='clé',
    )

    # ── Earning ─────────────────────────────────────────────────────────────
    daily_visit_award = models.PositiveIntegerField(
        'Clés / visite quotidienne', default=10,
        help_text='Accordées après min_visit_minutes minutes passées sur le site',
    )
    min_visit_minutes = models.PositiveIntegerField(
        'Durée minimale de visite (min)', default=5,
    )
    test_pass_award = models.PositiveIntegerField(
        'Clés / test réussi', default=1,
    )

    # ── Spending ────────────────────────────────────────────────────────────
    keys_per_pack = models.PositiveIntegerField(
        'Coût en clés / pack de questions', default=10,
    )
    questions_per_pack = models.PositiveIntegerField(
        'Questions ajoutées / pack', default=10,
    )

    # ── Decay ───────────────────────────────────────────────────────────────
    inactivity_grace_days = models.PositiveIntegerField(
        'Jours de grâce avant pénalité', default=3,
    )
    decay_per_day = models.PositiveIntegerField(
        'Clés retirées / jour d\'inactivité (après grâce)', default=10,
    )

    class Meta:
        verbose_name = 'Paramètres des clés'
        verbose_name_plural = 'Paramètres des clés'

    def __str__(self):
        return f'Paramètres clés — {self.icon} {self.currency_plural}'

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ---------------------------------------------------------------------------
# Per-user wallet
# ---------------------------------------------------------------------------

class KeyWallet(models.Model):
    """One wallet per user — balance + daily tracking."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='key_wallet',
        verbose_name='Utilisateur',
    )
    balance = models.PositiveIntegerField('Solde (clés)', default=0)

    # Daily visit tracking
    last_active_date = models.DateField('Dernière activité', null=True, blank=True)
    today_minutes = models.PositiveSmallIntegerField('Minutes aujourd\'hui', default=0)
    awarded_today = models.BooleanField('Clés accordées aujourd\'hui', default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Portefeuille'
        verbose_name_plural = 'Portefeuilles'

    def __str__(self):
        s = KeySettings.get()
        return f'{self.user.username} — {self.balance} {s.icon}'


# ---------------------------------------------------------------------------
# Transaction log
# ---------------------------------------------------------------------------

class KeyTransaction(models.Model):
    """Full audit trail — positive = earned, negative = spent/decayed."""

    REASON_DAILY_VISIT = 'daily_visit'
    REASON_TEST_PASS = 'test_pass'
    REASON_PURCHASE_BONUS = 'purchase_bonus'
    REASON_SPEND_QUESTIONS = 'spend_questions'
    REASON_DECAY = 'decay'
    REASON_ADMIN = 'admin'

    REASON_CHOICES = [
        (REASON_DAILY_VISIT, 'Visite quotidienne'),
        (REASON_TEST_PASS, 'Test réussi'),
        (REASON_PURCHASE_BONUS, 'Bonus achat'),
        (REASON_SPEND_QUESTIONS, 'Échange questions'),
        (REASON_DECAY, 'Pénalité inactivité'),
        (REASON_ADMIN, 'Ajustement admin'),
    ]

    wallet = models.ForeignKey(
        KeyWallet, on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Portefeuille',
    )
    amount = models.IntegerField('Montant')  # positive = earn, negative = spend
    reason = models.CharField('Raison', max_length=30, choices=REASON_CHOICES)
    note = models.CharField('Note', max_length=200, blank=True)
    balance_after = models.PositiveIntegerField('Solde après', default=0)
    created_at = models.DateTimeField('Date', auto_now_add=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f'{self.wallet.user.username} {sign}{self.amount} ({self.get_reason_display()})'
