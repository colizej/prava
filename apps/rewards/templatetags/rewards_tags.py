import json

from django import template

from apps.rewards.service import get_exchange_tiers, get_or_create_wallet, get_settings

register = template.Library()


@register.inclusion_tag('rewards/widget.html', takes_context=True)
def keys_widget(context):
    """
    Renders the fuel-tank (⛽) widget for the navbar.
    Safe to call even for anonymous users — returns empty context in that case.
    """
    request = context.get('request')
    if request is None or not request.user.is_authenticated:
        return {'show': False}

    user = request.user
    ks     = get_settings()
    wallet = get_or_create_wallet(user)
    tiers  = get_exchange_tiers(ks)

    # Avatar
    avatar_url = None
    try:
        if user.profile.avatar:
            avatar_url = user.profile.avatar.url
    except Exception:
        pass

    initial = (user.first_name[:1] or user.username[:1]).upper()

    return {
        'show': True,
        'icon': ks.icon,
        'balance': wallet.balance,
        'tank_capacity': ks.tank_capacity,
        'today_minutes': wallet.today_minutes,
        'min_minutes': ks.min_visit_minutes,
        'awarded_today': wallet.awarded_today,
        'award_amount': ks.daily_visit_award,
        'tiers_json': json.dumps(tiers),
        'avatar_url': avatar_url,
        'initial': initial,
    }
