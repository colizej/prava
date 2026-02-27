"""
Restructure 3 categories into 5 Titres matching the official 1975 royal decree.

Before:
  1. Règles de circulation (91 articles: Art. 1-59/1)
  2. Infrastructure et signalisation (23 articles: Art. 60-80)
  3. Conditions techniques (8 articles: Art. 81-87)

After:
  1. Titre I. Dispositions préliminaires (6 articles: Art. 1-6)
  2. Titre II. Règles d'usage de la voie publique (85 articles: Art. 7-59/1)
  3. Titre III. Signalisation routière (23 articles: Art. 60-80)
  4. Titre IV. Prescriptions techniques (4 articles: Art. 81-83)
  5. Titre V. Dispositions abrogatoires et transitoires (4 articles: Art. 84-87)
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.utils.text import slugify
from apps.reglementation.models import RuleCategory, CodeArticle

# Article numbers for Titre I (Dispositions préliminaires)
TITRE_I_ARTICLES = {'Art. 1', 'Art. 2', 'Art. 3', 'Art. 4', 'Art. 5', 'Art. 6'}

# Article numbers for Titre V (Dispositions abrogatoires et transitoires)
TITRE_V_ARTICLES = {'Art. 84', 'Art. 85', 'Art. 86', 'Art. 87'}


def main():
    # ── Step 1: Get existing categories ──
    cat_regles = RuleCategory.objects.get(slug='regles-de-circulation')
    cat_signal = RuleCategory.objects.get(slug='infrastructure-et-signalisation')
    cat_tech = RuleCategory.objects.get(slug='conditions-techniques')

    print(f"[1] Current: {cat_regles.name} ({cat_regles.articles.count()} articles)")
    print(f"[2] Current: {cat_signal.name} ({cat_signal.articles.count()} articles)")
    print(f"[3] Current: {cat_tech.name} ({cat_tech.articles.count()} articles)")
    print()

    # ── Step 2: Create Titre I ──
    titre_i, created = RuleCategory.objects.get_or_create(
        slug='dispositions-preliminaires',
        defaults={
            'name': 'Titre I. Dispositions préliminaires',
            'name_nl': 'Titel I. Inleidende bepalingen',
            'name_ru': 'Раздел I. Предварительные положения',
            'description': 'Champ d\'application, définitions, agents qualifiés et force obligatoire de la signalisation.',
            'description_nl': 'Toepassingsgebied, definities, bevoegde agenten en bindende kracht van de verkeerstekens.',
            'description_ru': 'Область применения, определения, уполномоченные агенты и обязательная сила дорожной сигнализации.',
            'icon': 'book-open',
            'order': 1,
            'is_active': True,
        }
    )
    if created:
        print(f"✓ Created: {titre_i.name}")
    else:
        print(f"• Already exists: {titre_i.name}")

    # ── Step 3: Create Titre V ──
    titre_v, created = RuleCategory.objects.get_or_create(
        slug='dispositions-finales',
        defaults={
            'name': 'Titre V. Dispositions abrogatoires et transitoires',
            'name_nl': 'Titel V. Opheffings- en overgangsbepalingen',
            'name_ru': 'Раздел V. Отменяющие и переходные положения',
            'description': 'Dispositions abrogatoires, transitoires et mise en vigueur.',
            'description_nl': 'Opheffingsbepalingen, overgangsbepalingen en inwerkingtreding.',
            'description_ru': 'Отменяющие положения, переходные положения и вступление в силу.',
            'icon': 'file-text',
            'order': 5,
            'is_active': True,
        }
    )
    if created:
        print(f"✓ Created: {titre_v.name}")
    else:
        print(f"• Already exists: {titre_v.name}")

    # ── Step 4: Rename existing categories ──
    cat_regles.name = 'Titre II. Règles d\'usage de la voie publique'
    cat_regles.name_nl = 'Titel II. Regels voor het gebruik van de openbare weg'
    cat_regles.name_ru = 'Раздел II. Правила пользования дорогами'
    cat_regles.slug = 'regles-usage-voie-publique'
    cat_regles.description = 'Conducteurs, vitesse, priorité, dépassement, stationnement, piétons, cyclistes et dispositions diverses.'
    cat_regles.description_nl = 'Bestuurders, snelheid, voorrang, inhalen, parkeren, voetgangers, fietsers en diverse bepalingen.'
    cat_regles.description_ru = 'Водители, скорость, приоритет, обгон, стоянка, пешеходы, велосипедисты и прочие положения.'
    cat_regles.icon = 'car'
    cat_regles.order = 2
    cat_regles.save()
    print(f"✓ Renamed: → {cat_regles.name}")

    cat_signal.name = 'Titre III. Signalisation routière'
    cat_signal.name_nl = 'Titel III. Verkeerstekens'
    cat_signal.name_ru = 'Раздел III. Дорожная сигнализация'
    cat_signal.slug = 'signalisation-routiere'
    cat_signal.description = 'Signaux lumineux, signaux routiers, marques routières et dispositions diverses.'
    cat_signal.description_nl = 'Verkeerslichten, verkeersborden, wegmarkeringen en diverse bepalingen.'
    cat_signal.description_ru = 'Светофоры, дорожные знаки, дорожная разметка и прочие положения.'
    cat_signal.icon = 'alert-triangle'
    cat_signal.order = 3
    cat_signal.save()
    print(f"✓ Renamed: → {cat_signal.name}")

    cat_tech.name = 'Titre IV. Prescriptions techniques'
    cat_tech.name_nl = 'Titel IV. Technische voorschriften'
    cat_tech.name_ru = 'Раздел IV. Технические предписания'
    cat_tech.slug = 'prescriptions-techniques'
    cat_tech.description = 'Conditions techniques pour véhicules à moteur, cycles, engins de déplacement et véhicules attelés.'
    cat_tech.description_nl = 'Technische voorwaarden voor motorvoertuigen, fietsen, voortbewegingstoestellen en bespannen voertuigen.'
    cat_tech.description_ru = 'Технические требования к автомобилям, велосипедам, средствам передвижения и гужевым транспортным средствам.'
    cat_tech.icon = 'settings'
    cat_tech.order = 4
    cat_tech.save()
    print(f"✓ Renamed: → {cat_tech.name}")
    print()

    # ── Step 5: Move Art. 1-6 from Titre II → Titre I ──
    moved_t1 = 0
    for art in CodeArticle.objects.filter(category=cat_regles):
        if art.article_number in TITRE_I_ARTICLES:
            art.category = titre_i
            art.save()
            moved_t1 += 1
            print(f"  → Titre I: {art.article_number}")
    print(f"✓ Moved {moved_t1} articles to Titre I")

    # ── Step 6: Move Art. 84-87 from Titre IV → Titre V ──
    moved_t5 = 0
    for art in CodeArticle.objects.filter(category=cat_tech):
        if art.article_number in TITRE_V_ARTICLES:
            art.category = titre_v
            art.save()
            moved_t5 += 1
            print(f"  → Titre V: {art.article_number}")
    print(f"✓ Moved {moved_t5} articles to Titre V")
    print()

    # ── Step 7: Verify ──
    print("=" * 60)
    print("RESULT:")
    print("=" * 60)
    for cat in RuleCategory.objects.all().order_by('order'):
        count = cat.articles.count()
        arts = list(cat.articles.order_by('order').values_list('article_number', flat=True))
        print(f"  [{cat.order}] {cat.name}")
        print(f"      {count} articles: {arts[0]} ... {arts[-1]}")
    print()
    total = CodeArticle.objects.count()
    print(f"Total: {total} articles")


if __name__ == '__main__':
    main()
