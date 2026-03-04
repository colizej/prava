#!/usr/bin/env python
"""
Update TrafficSign.name in the DB to match the corrected SIGN_REGISTRY.
Runs within the Django context. Does NOT touch images or reimport.

Usage:
    cd /Users/colizej/Documents/webApp/prava
    python scripts/update_sign_names.py
"""
import os
import sys
import django

# ── Django setup ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.reglementation.models import TrafficSign
from apps.reglementation.management.commands.import_signs import SIGN_REGISTRY

# ── Corrected names only (A/B/C series principal corrections) ────────────────
# The full SIGN_REGISTRY now contains the correct current Belgian law names.
# We update EVERY sign whose current DB name differs from the registry.

updated = 0
skipped = 0
not_found = 0

for code, (correct_name, sign_type) in SIGN_REGISTRY.items():
    qs = TrafficSign.objects.filter(code=code)
    if not qs.exists():
        not_found += 1
        continue
    sign = qs.first()
    if sign.name != correct_name:
        print(f"  [{code}]  '{sign.name}'  →  '{correct_name}'")
        sign.name = correct_name
        sign.save(update_fields=['name'])
        updated += 1
    else:
        skipped += 1

print(f"\n✅ Done: {updated} updated, {skipped} already correct, {not_found} not in DB")
