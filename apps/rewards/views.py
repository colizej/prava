import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .service import get_or_create_wallet, get_settings, heartbeat, spend


@login_required
@require_POST
def heartbeat_view(request):
    """
    Called by the JS widget every 60 seconds.
    Tracks active minutes and awards daily keys when threshold is reached.
    """
    result = heartbeat(request.user)
    return JsonResponse(result)


@login_required
@require_POST
def spend_keys(request):
    """
    Spend `keys_per_pack` keys to add `questions_per_pack` extra questions
    to today's DailyQuota.
    """
    from apps.accounts.models import DailyQuota

    settings = get_settings()
    wallet = get_or_create_wallet(request.user)

    if wallet.balance < settings.keys_per_pack:
        return JsonResponse({
            'ok': False,
            'reason': 'insufficient',
            'balance': wallet.balance,
            'icon': settings.icon,
        })

    success, new_balance = spend(
        request.user,
        settings.keys_per_pack,
        'spend_questions',
        f'+{settings.questions_per_pack} questions échangées',
    )

    if success:
        quota = DailyQuota.get_or_create_today(request.user)
        quota.max_questions += settings.questions_per_pack
        quota.save(update_fields=['max_questions'])
        return JsonResponse({
            'ok': True,
            'balance': new_balance,
            'added_questions': settings.questions_per_pack,
            'icon': settings.icon,
        })

    return JsonResponse({'ok': False, 'reason': 'unexpected', 'balance': new_balance})
