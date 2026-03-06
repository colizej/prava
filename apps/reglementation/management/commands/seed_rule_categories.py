"""
seed_rule_categories — Update RuleCategory names and icons for law 1975.

Usage:
    python manage.py seed_rule_categories
"""
from django.core.management.base import BaseCommand
from apps.reglementation.models import RuleCategory

CATEGORIES_1975 = [
    {"slug": "1975-titre-i",   "name": "Titre I. Dispositions préliminaires",               "name_nl": "Titel I. Inleidende bepalingen",                              "icon": "book-open", "order": 1},
    {"slug": "1975-titre-ii",  "name": "Titre II. Règles d'usage de la voie publique",       "name_nl": "Titel II. Regels voor het gebruik van de openbare weg",       "icon": "car",       "order": 2},
    {"slug": "1975-titre-iii", "name": "Titre III. Signalisation routière",                  "name_nl": "Titel III. Wegbebakening",                                    "icon": "sign-post", "order": 3},
    {"slug": "1975-titre-iv",  "name": "Titre IV. Prescriptions techniques",                 "name_nl": "Titel IV. Technische voorschriften",                          "icon": "wrench",    "order": 4},
    {"slug": "1975-titre-v",   "name": "Titre V. Dispositions abrogatoires et transitoires", "name_nl": "Titel V. Opheffings- en overgangsbepalingen",                 "icon": "gavel",     "order": 5},
]


class Command(BaseCommand):
    help = "Update RuleCategory names and icons for law 1975."

    def handle(self, *args, **options):
        for data in CATEGORIES_1975:
            n = RuleCategory.objects.filter(slug=data["slug"]).update(
                name=data["name"],
                name_nl=data["name_nl"],
                icon=data["icon"],
                order=data["order"],
            )
            status = "✅" if n else "⚠️  non trouvée"
            self.stdout.write(f"  {status} {data['slug']} — {data['name']}")
        self.stdout.write(self.style.SUCCESS("\nCatégories 1975 mises à jour."))
