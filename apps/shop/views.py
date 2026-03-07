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
import re as _re
import uuid as _uuid
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
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
# Helpers: guest checkout
# ---------------------------------------------------------------------------

def _get_or_create_guest_user(email):
    """Return (user, created).  Reuses an existing inactive guest account."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        return User.objects.get(email__iexact=email), False
    except User.DoesNotExist:
        base = _re.sub(r'[^a-z0-9_]', '', email.split('@')[0][:15].lower()) or 'user'
        username = f'{base}_{_uuid.uuid4().hex[:8]}'
        user = User(username=username, email=email, is_active=False)
        user.set_unusable_password()
        user.save()
        return user, True


def _send_complete_registration_email(user, request=None):
    """Send a 'set your password' email to a newly-activated guest account."""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    if request:
        confirm_url = request.build_absolute_uri(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        )
    else:
        base_url = getattr(settings, 'SITE_URL', 'https://prava.be')
        confirm_url = f'{base_url}/accounts/password-reset/confirm/{uid}/{token}/'
    send_mail(
        subject='Finalisez votre inscription — Prava.be',
        message=(
            'Bonjour,\n\n'
            'Votre paiement a bien été reçu et votre accès Premium est actif.\n\n'
            'Pour définir votre mot de passe et finaliser votre compte :\n'
            f'{confirm_url}\n\n'
            'Ce lien est valable 7 jours.\n\n'
            "— L'équipe Prava"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    logger.info('Complete-registration email sent to %s', user.email)


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

def checkout(request, plan_key):
    """Show order summary and trigger Mollie payment on POST."""
    plan = get_object_or_404(Plan, key=plan_key, is_active=True)
    guest_mode = not request.user.is_authenticated

    # Free plan — activate immediately, no payment needed
    if plan.is_free:
        messages.info(request, _('Le plan Gratuit est déjà actif.'))
        return redirect('shop:pricing')

    if request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
        else:
            from django.core.exceptions import ValidationError as DjValidationError
            from django.core.validators import validate_email
            email = request.POST.get('email', '').strip().lower()
            try:
                validate_email(email)
            except DjValidationError:
                messages.error(request, _('Adresse e-mail invalide.'))
                return render(request, 'shop/checkout.html', {'plan': plan, 'guest_mode': True})
            guest_user, created = _get_or_create_guest_user(email)
            # If an active account already exists, prompt to log in
            if not created and guest_user.is_active and guest_user.has_usable_password():
                messages.info(request, _('Vous avez déjà un compte. Connectez-vous pour continuer.'))
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
            user = guest_user

        # Create a pending order
        order = Order.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            status=Order.STATUS_PENDING,
        )

        mollie = _get_mollie_client()
        if mollie is None:
            # Dev fallback: simulate payment
            logger.warning('Mollie not configured — simulating payment for order %s', order.id)
            _activate_premium(order, request)
            if not request.user.is_authenticated:
                from django.contrib.auth import login as auth_login
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('shop:success', order_id=order.id)

        # Build absolute URLs for Mollie callbacks
        return_url = request.build_absolute_uri(
            reverse('shop:return') + f'?order_id={order.id}'
        )
        webhook_url = request.build_absolute_uri(reverse('shop:webhook'))

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
                    'user_id': str(user.id),
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
            return render(request, 'shop/checkout.html', {'plan': plan, 'guest_mode': guest_mode})

    return render(request, 'shop/checkout.html', {'plan': plan, 'guest_mode': guest_mode})


# ---------------------------------------------------------------------------
# 3. Return URL — user comes back from Mollie
# ---------------------------------------------------------------------------

def payment_return(request):
    """
    Mollie redirects the user here after checkout (paid or not).
    We check the status and redirect to success or back to pricing.
    """
    order_id = request.GET.get('order_id')
    if not order_id:
        return redirect('shop:pricing')

    # Guests arrive here unauthenticated — look up by id only
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)

    # Auto-login guest if webhook already activated their account
    if not request.user.is_authenticated and order.user.is_active:
        from django.contrib.auth import login as auth_login
        auth_login(request, order.user, backend='django.contrib.auth.backends.ModelBackend')

    # If webhook already fired, order may already be paid
    if order.status == Order.STATUS_PAID:
        return redirect('shop:success', order_id=order.id)

    # Otherwise, check Mollie directly
    mollie = _get_mollie_client()
    if mollie and order.mollie_payment_id:
        try:
            payment = mollie.payments.get(order.mollie_payment_id)
            if payment.is_paid():
                _activate_premium(order, request)
                if not request.user.is_authenticated:
                    from django.contrib.auth import login as auth_login
                    auth_login(request, order.user, backend='django.contrib.auth.backends.ModelBackend')
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

def success(request, order_id):
    """Confirmation page after successful payment."""
    order = get_object_or_404(Order, id=order_id, status=Order.STATUS_PAID)
    if not request.user.is_authenticated or order.user != request.user:
        return redirect('shop:pricing')
    guest_signup = not order.user.has_usable_password()
    return render(request, 'shop/success.html', {'order': order, 'guest_signup': guest_signup})


# ---------------------------------------------------------------------------
# Internal helper: activate premium on a user profile
# ---------------------------------------------------------------------------

def _activate_premium(order: Order, request=None) -> None:
    """Mark the order as paid and extend the user's premium access."""
    now = timezone.now()
    user = order.user

    # Activate an inactive guest account so they can log in
    was_inactive = not user.is_active
    if was_inactive:
        user.is_active = True
        user.save(update_fields=['is_active'])

    # Update order
    order.status = Order.STATUS_PAID
    order.paid_at = now
    order.save(update_fields=['status', 'paid_at', 'mollie_payment_id'])

    # Update user profile
    profile = user.profile
    current_until = profile.premium_until if profile.premium_until and profile.premium_until > now else now
    profile.premium_until = current_until + timezone.timedelta(days=order.plan.duration_days)
    profile.is_premium = True
    profile.save(update_fields=['is_premium', 'premium_until'])

    # Award purchase key bonus (non-critical)
    try:
        from apps.rewards.service import award_purchase_bonus
        award_purchase_bonus(user, order.plan)
    except Exception:
        pass

    # For guest accounts: send 'complete registration' email and skip standard confirmation
    if was_inactive and not user.has_usable_password():
        _send_complete_registration_email(user, request)
        return

    # Send purchase confirmation email (non-critical)
    try:
        plan = order.plan
        until_str = profile.premium_until.strftime('%d/%m/%Y') if profile.premium_until else '—'
        bonus_line = f'\nBonus carburant : +{plan.key_bonus} L offerts ⛽' if plan.key_bonus else ''
        body = (
            f'Bonjour {user.get_full_name() or user.username},\n\n'
            f'Merci pour votre achat ! Votre accès premium est maintenant actif.\n\n'
            f'Forfait    : {plan.name}\n'
            f'Montant    : {order.amount} \u20ac\n'
            f"Valable jusqu'au : {until_str}"
            f'{bonus_line}\n\n'
            f'Connectez-vous sur https://prava.be pour commencer.\n\n'
            f'— L\'équipe Prava'
        )
        send_mail(
            subject=f'✅ Confirmation d\'achat — {plan.name}',
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info('Purchase confirmation email sent to %s for order %s', user.email, order.id)
    except Exception:
        logger.exception('Failed to send purchase confirmation email for order %s', order.id)
