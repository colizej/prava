"""
Migration 0002 — Switch rewards system from Clés to Réservoir (⛽).

Changes to KeySettings:
  - Add tank_capacity, tier1/2/3 fuel+questions fields
  - Update singleton defaults: icon=⛽, currency, test_pass_award
"""
from django.db import migrations, models


def update_singleton(apps, schema_editor):
    """Update the existing KeySettings singleton with fuel-tank defaults."""
    KeySettings = apps.get_model('rewards', 'KeySettings')
    ks, _ = KeySettings.objects.get_or_create(pk=1)
    ks.icon = '⛽'
    ks.currency_plural = 'litres'
    ks.currency_singular = 'litre'
    ks.test_pass_award = 5
    ks.tank_capacity = 60
    ks.tier1_fuel = 20
    ks.tier1_questions = 10
    ks.tier2_fuel = 40
    ks.tier2_questions = 30
    ks.tier3_fuel = 60
    ks.tier3_questions = 50
    ks.save()


def reverse_singleton(apps, schema_editor):
    """Revert to Clés defaults."""
    KeySettings = apps.get_model('rewards', 'KeySettings')
    try:
        ks = KeySettings.objects.get(pk=1)
        ks.icon = '🔑'
        ks.currency_plural = 'clés'
        ks.currency_singular = 'clé'
        ks.test_pass_award = 1
        ks.save()
    except KeySettings.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='keysettings',
            name='tank_capacity',
            field=models.PositiveIntegerField(default=60, verbose_name='Capacité du réservoir (L)'),
        ),
        migrations.AddField(
            model_name='keysettings',
            name='tier1_fuel',
            field=models.PositiveIntegerField(default=20, verbose_name='Palier 1 — carburant (L)'),
        ),
        migrations.AddField(
            model_name='keysettings',
            name='tier1_questions',
            field=models.PositiveIntegerField(default=10, verbose_name='Palier 1 — questions ajoutées'),
        ),
        migrations.AddField(
            model_name='keysettings',
            name='tier2_fuel',
            field=models.PositiveIntegerField(default=40, verbose_name='Palier 2 — carburant (L)'),
        ),
        migrations.AddField(
            model_name='keysettings',
            name='tier2_questions',
            field=models.PositiveIntegerField(default=30, verbose_name='Palier 2 — questions ajoutées'),
        ),
        migrations.AddField(
            model_name='keysettings',
            name='tier3_fuel',
            field=models.PositiveIntegerField(default=60, verbose_name='Palier 3 — carburant (L, plein)'),
        ),
        migrations.AddField(
            model_name='keysettings',
            name='tier3_questions',
            field=models.PositiveIntegerField(default=50, verbose_name='Palier 3 — questions ajoutées'),
        ),
        migrations.RunPython(update_singleton, reverse_code=reverse_singleton),
    ]
