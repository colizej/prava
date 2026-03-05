"""
management command: python manage.py seed_plans
Creates the default subscription plans for the shop.
Safe to run multiple times (uses update_or_create).
"""
from django.core.management.base import BaseCommand
from apps.shop.models import Plan


PLANS = [
    {
        'key': 'gratuit',
        'name': 'Gratuit',
        'duration_days': 0,
        'price': '0.00',
        'is_active': True,
        'is_highlighted': False,
        'sort_order': 0,
    },
    {
        'key': 'journalier',
        'name': 'Journalier',
        'duration_days': 1,
        'price': '1.99',
        'is_active': True,
        'is_highlighted': False,
        'sort_order': 1,
    },
    {
        'key': '3-jours',
        'name': '3 jours',
        'duration_days': 3,
        'price': '4.99',
        'is_active': True,
        'is_highlighted': False,
        'sort_order': 2,
    },
    {
        'key': 'hebdomadaire',
        'name': 'Hebdomadaire',
        'duration_days': 7,
        'price': '9.99',
        'is_active': True,
        'is_highlighted': True,
        'sort_order': 3,
    },
    {
        'key': 'mensuel',
        'name': 'Mensuel',
        'duration_days': 30,
        'price': '24.99',
        'is_active': True,
        'is_highlighted': False,
        'sort_order': 4,
    },
]


class Command(BaseCommand):
    help = 'Seed default subscription plans in the shop.'

    def handle(self, *args, **options):
        for data in PLANS:
            plan, created = Plan.objects.update_or_create(
                key=data['key'],
                defaults={k: v for k, v in data.items() if k != 'key'},
            )
            status = 'created' if created else 'updated'
            self.stdout.write(f'  {status}: {plan}')
        self.stdout.write(self.style.SUCCESS(f'\n✓ {len(PLANS)} plans seeded.'))
