import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Plan(models.Model):
    """Subscription plan / access pass."""

    key = models.SlugField('Clé', unique=True, max_length=20)
    name = models.CharField('Nom', max_length=100)
    duration_days = models.PositiveIntegerField(
        'Durée (jours)',
        help_text='0 = gratuit/illimité',
        default=0,
    )
    price = models.DecimalField('Prix (€)', max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField('Actif', default=True)
    is_highlighted = models.BooleanField('Mis en avant', default=False)
    sort_order = models.PositiveSmallIntegerField('Ordre', default=0)
    key_bonus = models.PositiveIntegerField(
        'Bonus clés 🔑', default=0,
        help_text='Clés accordées à l\'achat de ce forfait (0 = aucun bonus)',
    )

    class Meta:
        verbose_name = 'Forfait'
        verbose_name_plural = 'Forfaits'
        ordering = ['sort_order', 'price']

    def __str__(self):
        return f'{self.name} — {self.price}€'

    @property
    def is_free(self):
        return self.price == 0

    @property
    def price_display(self):
        if self.is_free:
            return 'Gratuit'
        return f'{self.price}€'.replace('.', ',')


class Order(models.Model):
    """A purchase attempt (one plan, one user)."""

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELED = 'canceled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_PAID, 'Payé'),
        (STATUS_FAILED, 'Échoué'),
        (STATUS_EXPIRED, 'Expiré'),
        (STATUS_CANCELED, 'Annulé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Utilisateur',
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Forfait',
    )
    amount = models.DecimalField('Montant (€)', max_digits=6, decimal_places=2)
    status = models.CharField(
        'Statut', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    mollie_payment_id = models.CharField(
        'ID Mollie', max_length=50, blank=True, db_index=True
    )
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    paid_at = models.DateTimeField('Payé le', null=True, blank=True)

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.id} — {self.user} — {self.plan.name} — {self.status}'
