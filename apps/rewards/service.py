"""
Service layer for the rewards (Réservoir ⛽) app.

All business logic lives here — views and signals just call these functions.

Public API:
    get_settings()                  → KeySettings singleton
    get_or_create_wallet(u)         → KeyWallet
    get_exchange_tiers(settings)    → list of {fuel, questions} dicts
    award(user, amount, reason, note) → int (new balance)
    spend(user, amount, reason, note) → (bool, int)
    apply_decay(user)               → void (called internally on new day)
    heartbeat(user)                 → dict (called by AJAX every minute)
    award_test_pass(user)           → int (new balance)
    award_purchase_bonus(user, plan) → int (new balance) — plan has .key_bonus
    spend_for_questions(user, fuel) → (ok: bool, new_balance: int, questions: int)
"""
from django.utils import timezone

from .models import KeySettings, KeyTransaction, KeyWallet


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_settings() -> KeySettings:
    return KeySettings.get()


def get_or_create_wallet(user) -> KeyWallet:
    wallet, _ = KeyWallet.objects.get_or_create(user=user)
    return wallet


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def award(user, amount: int, reason: str, note: str = '') -> int:
    """
    Credit `amount` keys to the user.  Returns the new balance.
    Always positive — this function is for earning only.
    """
    if amount <= 0:
        return get_or_create_wallet(user).balance

    wallet = get_or_create_wallet(user)
    wallet.balance += amount
    wallet.save(update_fields=['balance'])

    KeyTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        reason=reason,
        note=note,
        balance_after=wallet.balance,
    )
    return wallet.balance


def spend(user, amount: int, reason: str, note: str = '') -> tuple:
    """
    Debit `amount` keys.  Returns (success: bool, new_balance: int).
    Does nothing and returns (False, balance) if insufficient funds.
    """
    if amount <= 0:
        return True, get_or_create_wallet(user).balance

    wallet = get_or_create_wallet(user)
    if wallet.balance < amount:
        return False, wallet.balance

    wallet.balance -= amount
    wallet.save(update_fields=['balance'])

    KeyTransaction.objects.create(
        wallet=wallet,
        amount=-amount,
        reason=reason,
        note=note,
        balance_after=wallet.balance,
    )
    return True, wallet.balance


# ---------------------------------------------------------------------------
# Decay logic
# ---------------------------------------------------------------------------

def apply_decay(user) -> int:
    """
    Apply inactivity penalty based on days since last_active_date.
    Called internally at the start of a new day (inside heartbeat).
    Returns the amount deducted (>= 0).
    """
    settings = get_settings()
    wallet = get_or_create_wallet(user)
    today = timezone.now().date()

    if wallet.last_active_date is None:
        return 0  # first ever visit — no penalty

    days_inactive = (today - wallet.last_active_date).days
    if days_inactive <= settings.inactivity_grace_days:
        return 0  # within grace period

    decay_days = days_inactive - settings.inactivity_grace_days
    penalty = min(decay_days * settings.decay_per_day, wallet.balance)

    if penalty > 0:
        wallet.balance = max(0, wallet.balance - penalty)
        wallet.save(update_fields=['balance'])
        KeyTransaction.objects.create(
            wallet=wallet,
            amount=-penalty,
            reason=KeyTransaction.REASON_DECAY,
            note=f'Pénalité inactivité — {days_inactive} jour(s) sans connexion',
            balance_after=wallet.balance,
        )

    return penalty


# ---------------------------------------------------------------------------
# Heartbeat — called every minute from the browser
# ---------------------------------------------------------------------------

def heartbeat(user) -> dict:
    """
    Main function called by the AJAX heartbeat every 60 seconds.

    1. If a new day has started:
       - apply_decay
       - reset today_minutes and awarded_today
    2. Increment today_minutes (capped at 60)
    3. If threshold reached and not yet awarded → award daily keys
    4. Return a dict consumed by the JS widget.
    """
    settings = get_settings()
    wallet = get_or_create_wallet(user)
    today = timezone.now().date()
    awarded_now = False

    # ── New day reset ────────────────────────────────────────────────────────
    if wallet.last_active_date != today:
        apply_decay(user)
        wallet.refresh_from_db()
        wallet.today_minutes = 0
        wallet.awarded_today = False
        wallet.last_active_date = today
        wallet.save(update_fields=['today_minutes', 'awarded_today', 'last_active_date'])

    # ── Increment active minutes (cap at 60 to avoid runaway) ───────────────
    wallet.today_minutes = min(wallet.today_minutes + 1, 60)
    wallet.save(update_fields=['today_minutes'])

    # ── Award daily keys if threshold reached ────────────────────────────────
    if not wallet.awarded_today and wallet.today_minutes >= settings.min_visit_minutes:
        wallet.awarded_today = True
        wallet.save(update_fields=['awarded_today'])
        award(
            user,
            settings.daily_visit_award,
            KeyTransaction.REASON_DAILY_VISIT,
            f'+{settings.daily_visit_award} {settings.icon} — visite du {today}',
        )
        awarded_now = True
        wallet.refresh_from_db()

    remaining = max(0, settings.min_visit_minutes - wallet.today_minutes)

    return {
        'balance': wallet.balance,
        'today_minutes': wallet.today_minutes,
        'min_minutes': settings.min_visit_minutes,
        'awarded_today': wallet.awarded_today,
        'awarded_now': awarded_now,
        'award_amount': settings.daily_visit_award,
        'remaining_minutes': remaining,
        'icon': settings.icon,
    }


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def award_test_pass(user) -> int:
    """Award keys for passing a test.  Returns new balance."""
    settings = get_settings()
    return award(
        user,
        settings.test_pass_award,
        KeyTransaction.REASON_TEST_PASS,
        f'+{settings.test_pass_award} {settings.icon} — test réussi',
    )


def award_purchase_bonus(user, plan) -> int:
    """
    Award the purchase bonus attached to a shop Plan.
    `plan` is a `apps.shop.models.Plan` instance with a `key_bonus` field.
    Returns new balance (0 if no bonus on this plan).
    """
    if not hasattr(plan, 'key_bonus') or plan.key_bonus <= 0:
        return get_or_create_wallet(user).balance

    settings = get_settings()
    return award(
        user,
        plan.key_bonus,
        KeyTransaction.REASON_PURCHASE_BONUS,
        f'+{plan.key_bonus} {settings.icon} — bonus achat {plan.name}',
    )


# ---------------------------------------------------------------------------
# Exchange tiers
# ---------------------------------------------------------------------------

def get_exchange_tiers(settings=None) -> list:
    """Return the 3 exchange tiers as a list of dicts."""
    if settings is None:
        settings = get_settings()
    return [
        {'fuel': settings.tier1_fuel, 'questions': settings.tier1_questions},
        {'fuel': settings.tier2_fuel, 'questions': settings.tier2_questions},
        {'fuel': settings.tier3_fuel, 'questions': settings.tier3_questions},
    ]


def spend_for_questions(user, fuel: int) -> tuple:
    """
    Spend `fuel` litres for bonus questions based on the configured tiers.

    Returns (ok: bool, new_balance: int, questions_added: int).
    - ok=False + questions=0 if insufficient fuel or invalid tier.
    """
    settings = get_settings()
    tiers = get_exchange_tiers(settings)

    tier = next((t for t in tiers if t['fuel'] == fuel), None)
    if not tier:
        return False, get_or_create_wallet(user).balance, 0

    wallet = get_or_create_wallet(user)
    if wallet.balance < tier['fuel']:
        return False, wallet.balance, 0

    success, new_balance = spend(
        user,
        tier['fuel'],
        KeyTransaction.REASON_SPEND_QUESTIONS,
        f'+{tier["questions"]} questions — {tier["fuel"]} L échangés',
    )

    if success:
        from apps.accounts.models import DailyQuota
        quota = DailyQuota.get_or_create_today(user)
        quota.max_questions += tier['questions']
        quota.save(update_fields=['max_questions'])
        return True, new_balance, tier['questions']

    return False, new_balance, 0
