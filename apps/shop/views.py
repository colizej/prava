"""
Shop views — Mollie payment integration.

Flow:
  1. /shop/                     → pricing page (list of plans)
  2. /shop/checkout/<plan_key>/ → summary + confirm (login required)
  3. POST checkout              → create Mollie payment → redirect to Mollie
  4. /shop/return/?order_id=…   → user lands here after Mollie; check status
  5. /shop/webhook/             → Mollie server-side callback; activate premium
  6. /shop/success/<order_id>/  → confirmation page
"""
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Order, Plan

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: get Mollie client
# ---------------------------------------------------------------------------

def _get_mollie_client():
    """Return an initialised Mollie API client, or None if not configured."""
    api_key = getattr(settings, 'MOLLIE_API_KEY', None)
    if not api_key:
        return None
    try:
        from mollie.api.client import Client
        client = Client()
        client.set_api_key(api_key)
        return client
    except ImportError:
        logger.warning('mollie-api-python not installed — payment disabled.')
        return None


# ---------------------------------------------------------------------------
# 1. Pricing page
# ---------------------------------------------------------------------------

def pricing(request):
    """Show all active plans."""
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'shop/pricing.html', {'plans': plans})


# ---------------------------------------------------------------------------
# 2. Checkout — summary + payment initiation
# ---------------------------------------------------------------------------

@login_required
def checkout(request, plan_key):
    """Show order summary and trigger Mollie payment on POST."""
    plan = get_object_or_404(Plan, key=plan_key, is_active=True)

    # Free plan — activate immediately, no payment needed
    if plan.is_free:
        messages.info(request, _('Le plan Gratuit est déjà actif.'))
        return redirect('shop:pricing')

    if request.method == 'POST':
        # Create a pending order
        order = Order.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            status=Order.STATUS_PENDING,
        )

        mollie = _get_mollie_client()
        if mollie is None:
            # Dev fallback: simulate payment
            logger.warning('Mollie not configured — simulating payment for order %s', order.id)
            _activate_premium(order)
            return redirect('shop:success', order_id=order.id)

        # Build absolute URLs for Mollie callbacks
        return_url = request.build_absolute_uri(
            reverse('shop:return') + f'?order_id={order.id}'
        )
        webhook_url = request.build_absolute_uri(reverse('shop:webhook'))

        # In test/debug mode Mollie ignores webhook for localhost, that's fine.
        try:
            payment = mollie.payments.create({
                'amount': {
                    'currency': 'EUR',
                    'value': f'{order.amount:.2f}',
                },
                'description': f'{plan.name} — Prava.be',
                'redirectUrl': return_url,
                'webhookUrl': webhook_url,
                'metadata': {
                    'order_id': str(order.id),
                    'user_id': str(request.user.id),
                    'plan_key': plan.key,
                },
            })
            order.mollie_payment_id = payment.id
            order.save(update_fields=['mollie_payment_id'])
            return redirect(payment.checkout_url)

        except Exception as exc:
            logger.exception('Mollie payment creation failed for order %s: %s', order.id, exc)
            order.status = Order.STATUS_FAILED
            order.save(update_fields=['status'])
            messages.error(request, _('Le paiement n\'a pas pu être initié. Veuillez réessayer.'))
            return redirect('shop:checkout', plan_key=plan_key)

    return render(request, 'shop/checkout.html', {'plan': plan})


# ---------------------------------------------------------------------------
# 3. Return URL — user comes back from Mollie
# ---------------------------------------------------------------------------

@login_required
def payment_return(request):
    """
    Mollie redirects the user here after checkout (paid or not).
    We check the status and redirect to success or back to pricing.
    """
    order_id = request.GET.get('order_id')
    if not order_id:
        return redirect('shop:pricing')

    order = get_object_or_404(Order, id=order_id, user=request.user)

    # If webhook already fired, order may already be paid
    if order.status == Order.STATUS_PAID:
        return redirect('shop:success', order_id=order.id)

    # Otherwise, check Mollie directly
    mollie = _get_mollie_client()
    if mollie and order.mollie_payment_id:
        try:
            payment = mollie.payments.get(order.mollie_payment_id)
            if payment.is_paid():
                _activate_premium(order)
                return redirect('shop:success', order_id=order.id)
            elif payment.is_canceled() or payment.is_failed() or payment.is_expired():
                order.status = Order.STATUS_CANCELED
                order.save(update_fields=['status'])
                messages.warning(request, _('Le paiement a été annulé.'))
                return redirect('shop:pricing')
        except Exception as exc:
            logger.exception('Mollie payment status check failed: %s', exc)

    # Pending — show a waiting page
    return render(request, 'shop/return_pending.html', {'order': order})


# ---------------------------------------------------------------------------
# 4. Webhook — server-side callback from Mollie (CSRF exempt)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def webhook(request):
    """
    Mollie POSTs here with `id` = payment ID.
    We verify the status and activate premium if paid.
    """
    payment_id = request.POST.get('id')
    if not payment_id:
        return HttpResponseBadRequest('Missing id')

    mollie = _get_mollie_client()
    if mollie is None:
        return HttpResponse('OK')  # dev mode — noop

    try:
        payment = mollie.payments.get(payment_id)
    except Exception as exc:
        logger.exception('Webhook: failed to fetch payment %s: %s', payment_id, exc)
        return HttpResponseBadRequest('Payment fetch failed')

    order_id = (payment.metadata or {}).get('order_id')
    if not order_id:
        logger.warning('Webhook: payment %s has no order_id in metadata', payment_id)
        return HttpResponse('OK')

    try:
        order = Order.objects.select_related('user', 'plan').get(id=order_id)
    except Order.DoesNotExist:
        logger.warning('Webhook: order %s not found', order_id)
        return HttpResponse('OK')

    if order.status == Order.STATUS_PAID:
        return HttpResponse('OK')  # idempotent — already processed

    if payment.is_paid():
        order.mollie_payment_id = payment_id
        _activate_premium(order)
        logger.info('Webhook: order %s paid — premium activated for user %s', order_id, order.user_id)
    elif payment.is_canceled():
        order.status = Order.STATUS_CANCELED
        order.save(update_fields=['status'])
    elif payment.is_failed():
        order.status = Order.STATUS_FAILED
        order.save(update_fields=['status'])
    elif payment.is_expired():
        order.status = Order.STATUS_EXPIRED
        order.save(update_fields=['status'])

    return HttpResponse('OK')


# ---------------------------------------------------------------------------
# 5. Success page
# ---------------------------------------------------------------------------

@login_required
def success(request, order_id):
    """Confirmation page after successful payment."""
    order = get_object_or_404(Order, id=order_id, user=request.user, status=Order.STATUS_PAID)
    return render(request, 'shop/success.html', {'order': order})


# ---------------------------------------------------------------------------
# Internal helper: activate premium on a user profile
# ---------------------------------------------------------------------------

def _activate_premium(order: Order) -> None:
    """Mark the order as paid and extend the user's premium access."""
    now = timezone.now()

    # Update order
    order.status = Order.STATUS_PAID
    order.paid_at = now
    order.save(update_fields=['status', 'paid_at', 'mollie_payment_id'])

    # Update user profile
    profile = order.user.profile
    current_until = profile.premium_until if profile.premium_until and profile.premium_until > now else now
    profile.premium_until = current_until + timezone.timedelta(days=order.plan.duration_days)
    profile.is_premium = True
    profile.save(update_fields=['is_premium', 'premium_until'])
