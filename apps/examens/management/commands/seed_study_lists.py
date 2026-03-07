"""
seed_study_lists — Create canonical StudyList entries.

Usage:
    python manage.py seed_study_lists
"""
from django.core.management.base import BaseCommand
from apps.examens.models import StudyList

LISTS = [
    {"slug": "a-revoir",   "name": "À revoir",    "icon": "🔖", "order": 1,
     "description": "Questions à revoir plus tard"},
    {"slug": "difficile",  "name": "Difficile",   "icon": "⚠️",  "order": 2,
     "description": "Questions que vous trouvez difficiles"},
    {"slug": "favoris",    "name": "Favoris",     "icon": "⭐", "order": 3,
     "description": "Vos questions préférées"},
]


class Command(BaseCommand):
    help = "Create or update canonical StudyList records"

    def handle(self, *args, **options):
        for data in LISTS:
            obj, created = StudyList.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name":        data["name"],
                    "icon":        data["icon"],
                    "description": data["description"],
                    "order":       data["order"],
                    "is_active":   True,
                },
            )
            action = "créé" if created else "mis à jour"
            self.stdout.write(f"  {data['icon']} {data['name']} — {action}")
        self.stdout.write(self.style.SUCCESS("✅ seed_study_lists terminé"))
