from django import template

from apps.rewards.service import get_or_create_wallet, get_settings

register = template.Library()


@register.inclusion_tag('rewards/widget.html', takes_context=True)
def keys_widget(context):
    """
    Renders the 🔑 Clés widget for the navbar.
    Safe to call even for anonymous users — returns empty context in that case.
    """
    request = context.get('request')
    if request is None or not request.user.is_authenticated:
        return {'show': False}

    settings = get_settings()
    wallet = get_or_create_wallet(request.user)

    remaining = max(0, settings.min_visit_minutes - wallet.today_minutes)

    return {
        'show': True,
        'icon': settings.icon,
        'balance': wallet.balance,
        'today_minutes': wallet.today_minutes,
        'min_minutes': settings.min_visit_minutes,
        'awarded_today': wallet.awarded_today,
        'award_amount': settings.daily_visit_award,
        'remaining_minutes': remaining,
        'keys_per_pack': settings.keys_per_pack,
        'questions_per_pack': settings.questions_per_pack,
    }
