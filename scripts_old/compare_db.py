"""Compare our DB articles against the codedelaroute.be 1975 royal decree structure."""
import os, sys, re, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.reglementation.models import RuleCategory, CodeArticle

# ============================================================
# Complete list of articles from codedelaroute.be (1975 AR)
# ============================================================
EXPECTED_ARTICLES = {
    "Titre I. Dispositions préliminaires": [
        "1", "2", "3", "4", "5", "6",
    ],
    "Titre II. Règles d'usage de la voie publique": [
        "7", "7bis", "7ter", "8", "9", "10", "11", "12", "12bis",
        "13", "14", "15", "16", "17", "18", "19", "20", "21", "22",
        "22bis", "22ter", "22quater", "22quinquies", "22sexies",
        "22septies", "22octies", "22novies", "22decies", "22undecies",
        "23", "24", "25", "26", "27", "27bis", "27ter", "27quater",
        "27quinquies", "28", "29", "30", "30bis", "31", "32", "32bis",
        "33", "34", "34bis", "35", "36", "37", "38", "39", "40",
        "40bis", "41", "42", "43", "43bis", "43ter", "44", "45",
        "45bis", "46", "47", "47bis", "48", "48bis", "49", "50",
        "51", "52", "53", "54", "55", "55bis", "56", "56bis", "57",
        "58", "59", "59/1",
    ],
    "Titre III. Signalisation routière": [
        "60", "61", "62", "62bis", "62ter", "63", "64", "65", "66",
        "67", "68", "69", "70", "71", "72", "73", "74", "75", "76",
        "77", "78", "79", "80",
    ],
    "Titre IV. Prescriptions techniques": [
        "81", "82", "82bis", "83",
    ],
    "Titre V. Dispositions abrogatoires et transitoires": [
        "84", "85", "86", "87",
    ],
}

# Flatten to a set
all_expected = set()
for titre, articles in EXPECTED_ARTICLES.items():
    for a in articles:
        all_expected.add(a)

print(f"="*70)
print(f"EXPECTED (codedelaroute.be 1975 AR): {len(all_expected)} articles")
print(f"="*70)

# ============================================================
# Our database
# ============================================================
print(f"\n{'='*70}")
print(f"OUR DATABASE:")
print(f"{'='*70}")

categories = RuleCategory.objects.all().order_by("order")
for cat in categories:
    articles = CodeArticle.objects.filter(category=cat).order_by("order")
    print(f"\n📁 {cat.name} ({articles.count()} articles)")
    for art in articles:
        print(f"   {art.article_number} — {art.title[:60]}")

# ============================================================
# Comparison
# ============================================================
# Extract article numbers from our DB
our_articles = set()
our_article_map = {}
for art in CodeArticle.objects.all():
    # Parse "Art. 22bis" -> "22bis"
    num = art.article_number.replace("Art. ", "").strip()
    our_articles.add(num)
    our_article_map[num] = art

print(f"\n{'='*70}")
print(f"COMPARISON:")
print(f"{'='*70}")
print(f"Expected: {len(all_expected)} articles")
print(f"In our DB: {len(our_articles)} articles")

# What we have that's expected
matching = our_articles & all_expected
print(f"Matching:  {len(matching)} articles")

# What's missing from our DB
missing = all_expected - our_articles
if missing:
    print(f"\n❌ MISSING from our DB ({len(missing)} articles):")
    for titre, articles in EXPECTED_ARTICLES.items():
        titre_missing = [a for a in articles if a in missing]
        if titre_missing:
            print(f"   {titre}:")
            for a in titre_missing:
                print(f"      Art. {a}")

# What we have extra (not in the 1975 law)
extra = our_articles - all_expected
if extra:
    print(f"\n⚠️  EXTRA in our DB (not in 1975 law) ({len(extra)} articles):")
    for a in sorted(extra, key=lambda x: x.zfill(10)):
        art = our_article_map[a]
        print(f"   Art. {a} — {art.title[:60]}")

# ============================================================
# Category mapping analysis
# ============================================================
print(f"\n{'='*70}")
print(f"CATEGORY MAPPING (our DB → 1975 law):")
print(f"{'='*70}")

our_titres = {}
for cat in categories:
    articles = CodeArticle.objects.filter(category=cat).order_by("order")
    nums = [a.article_number.replace("Art. ", "").strip() for a in articles]
    our_titres[cat.name] = nums

for cat_name, nums in our_titres.items():
    print(f"\n📁 Our '{cat_name}' → maps to:")
    for titre, articles in EXPECTED_ARTICLES.items():
        overlap = set(nums) & set(articles)
        if overlap:
            print(f"   {titre}: {len(overlap)}/{len(articles)} articles")
