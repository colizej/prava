import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .service import get_or_create_wallet, get_settings, heartbeat, spend_for_questions


@login_required
@require_POST
def heartbeat_view(request):
    """
    Called by the JS widget every 60 seconds.
    Tracks active minutes and awards daily fuel when threshold is reached.
    """
    from .service import heartbeat as _heartbeat
    result = _heartbeat(request.user)
    return JsonResponse(result)


@login_required
@require_POST
def spend_keys(request):
    """
    Spend fuel (litres) from the tank to add bonus questions to today's DailyQuota.
    Expects JSON body: {"fuel": <int>}  where fuel must match one of the 3 exchange tiers.
    """
    try:
        body = json.loads(request.body)
        fuel = int(body.get('fuel', 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'reason': 'bad_request'}, status=400)

    ok, new_balance, questions = spend_for_questions(request.user, fuel)
    settings = get_settings()

    if ok:
        return JsonResponse({
            'ok': True,
            'balance': new_balance,
            'added_questions': questions,
            'icon': settings.icon,
        })

    if new_balance < fuel:
        return JsonResponse({
            'ok': False,
            'reason': 'insufficient',
            'balance': new_balance,
            'icon': settings.icon,
        })

    return JsonResponse({
        'ok': False,
        'reason': 'invalid_tier',
        'balance': new_balance,
        'icon': settings.icon,
    })
