"""
seed_exam_categories — Create or update ExamCategory with canonical names, icons,
descriptions and order.

Usage:
    python manage.py seed_exam_categories
"""
from django.core.management.base import BaseCommand
from apps.examens.models import ExamCategory

CATEGORIES = [
    {
        "slug": "voie-publique",
        "name": "La voie publique",
        "icon": "road",
        "description": "Définitions, types de voies, usagers, chaussée, trottoir, accotements.",
        "order": 1,
    },
    {
        "slug": "vitesse-freinage",
        "name": "Vitesse et freinage",
        "icon": "gauge",
        "description": "Limitations de vitesse, zones 30, distances de freinage, autoroute.",
        "order": 2,
    },
    {
        "slug": "priorites",
        "name": "Priorités",
        "icon": "arrow-right-circle",
        "description": "Règles de priorité, carrefours, ronds-points, trams.",
        "order": 3,
    },
    {
        "slug": "depassement",
        "name": "Dépassement et croisement",
        "icon": "arrows-pointing-out",
        "description": "Règles de dépassement, interdictions, croisement.",
        "order": 4,
    },
    {
        "slug": "signalisation",
        "name": "Signalisation",
        "icon": "sign-post",
        "description": "Panneaux de danger, interdiction, obligation, indication, feux.",
        "order": 5,
    },
    {
        "slug": "arret-stationnement",
        "name": "Arrêt et stationnement",
        "icon": "parking",
        "description": "Règles d'arrêt, de stationnement, zones bleues, interdictions.",
        "order": 6,
    },
    {
        "slug": "obligations",
        "name": "Obligations du conducteur",
        "icon": "id-card",
        "description": "Ceinture, GSM, alcool, documents, éclairage, clignotants.",
        "order": 7,
    },
    {
        "slug": "situations",
        "name": "Situations de conduite",
        "icon": "map",
        "description": "Autoroute, tunnel, rond-point, piétons, cyclistes, conditions météo.",
        "order": 8,
    },
]


class Command(BaseCommand):
    help = "Seed or update ExamCategory with canonical names, icons and descriptions."

    def handle(self, *args, **options):
        for data in CATEGORIES:
            slug = data["slug"]
            cat, created = ExamCategory.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": data["name"],
                    "icon": data["icon"],
                    "description": data.get("description", ""),
                    "order": data["order"],
                },
            )
            action = "créée" if created else "mise à jour"
            self.stdout.write(f"  ✅ {slug} — {action}")
        self.stdout.write(self.style.SUCCESS(f"\n{len(CATEGORIES)} catégories synchronisées."))
