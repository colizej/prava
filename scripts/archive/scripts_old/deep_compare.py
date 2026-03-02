#!/usr/bin/env python
"""Deep comparison of DB articles vs scraped official data."""
import django, os, json, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.reglementation.models import RuleCategory, CodeArticle

# Load scraped data
with open('data/sites/codedelaroute.be/output/code_de_la_route_complet.json') as f:
    scraped = json.load(f)

# Build maps: article_number -> title, content length
scraped_map = {}
for art in scraped['articles']:
    num = art.get('number', '').rstrip('.')
    # Fix known truncated numbers in scraped data
    if num == '22no':
        num = '22novies'
    elif num == '22un':
        num = '22undecies'
    elif num == '22' and art.get('title', '').startswith('Article 22decies'):
        num = '22decies'

    key = f"Art. {num}"
    scraped_map[key] = {
        'title': art.get('title', ''),
        'html_len': len(art.get('html', '')),
        'text_len': len(art.get('full_text', '')),
        'html': art.get('html', ''),
    }

# Compare with DB
db_articles = CodeArticle.objects.all().order_by('category__order', 'order')

print("=" * 110)
print(f"{'DB article_number':25s} | {'Status':12s} | {'DB html':>8s} | {'Scrape':>8s} | {'Ratio':>6s} | Notes")
print("=" * 110)

issues = []
ok_count = 0

for art in db_articles:
    key = art.article_number
    if key not in scraped_map:
        print(f"{key:25s} | {'EXTRA':12s} | {len(art.content):>8d} | {'N/A':>8s} | {'N/A':>6s} | Not in scraped data")
        issues.append(f"EXTRA: {key}")
        continue

    s = scraped_map[key]
    db_title = art.title
    s_title = s['title']

    # Title comparison
    title_ok = db_title == s_title

    # Content length comparison
    db_len = len(art.content)
    s_len = s['html_len']
    ratio = db_len / s_len if s_len > 0 else 0

    notes = []
    if not title_ok:
        if s_title.startswith(db_title):
            notes.append(f"TITLE TRUNCATED")
        else:
            notes.append(f"TITLE DIFF")

    if ratio < 0.8:
        notes.append(f"CONTENT SHORTER ({ratio:.0%})")
    elif ratio > 1.3:
        notes.append(f"CONTENT LONGER ({ratio:.0%})")

    if notes:
        status = 'ISSUE'
        note_str = '; '.join(notes)
        print(f"{key:25s} | {status:12s} | {db_len:>8d} | {s_len:>8d} | {ratio:>6.2f} | {note_str}")
        issues.append(f"{key}: {note_str}")
    else:
        ok_count += 1

# Check for articles in scraped but not in DB
for key in scraped_map:
    if not CodeArticle.objects.filter(article_number=key).exists():
        s = scraped_map[key]
        print(f"{'MISSING':25s} | {'MISSING':12s} | {'N/A':>8s} | {s['html_len']:>8d} | {'N/A':>6s} | {key}")
        issues.append(f"MISSING: {key}")

print("\n" + "=" * 110)
print(f"SUMMARY: {ok_count} OK, {len(issues)} issues")
for i in issues:
    print(f"  - {i}")

# Category comparison
print("\n\n=== CATEGORY STRUCTURE ===")
print("Official structure from codedelaroute.be:")
OFFICIAL = {
    "Titre I. Dispositions préliminaires": ["Art. 1", "Art. 2", "Art. 3", "Art. 4", "Art. 5", "Art. 6"],
    "Titre II. Règles d'usage de la voie publique": [f"Art. {n}" for n in [
        "7", "7bis", "7ter", "8", "9", "10", "11", "12", "12bis", "13", "14", "15", "16", "17", "18", "19",
        "20", "21", "22", "22bis", "22ter", "22quater", "22quinquies", "22sexies", "22septies", "22octies",
        "22novies", "22decies", "22undecies",
        "23", "24", "25", "26", "27", "27bis", "27ter", "27quater", "27quinquies",
        "28", "29", "30", "30bis", "31", "32", "32bis", "33", "34", "34bis", "35", "36", "37", "38",
        "39", "39bis", "40", "40bis", "40ter", "40quater",
        "41", "42", "43", "43bis", "43ter", "44", "45", "45bis", "46", "47", "47bis",
        "48", "48bis", "49", "50", "51", "52", "53", "54", "55", "55bis", "56", "56bis",
        "57", "58", "59", "59/1"
    ]],
    "Titre III. Signalisation routière": [f"Art. {n}" for n in [
        "60", "61", "62", "62bis", "62ter", "63", "64", "65", "66", "67", "68", "69", "70", "71",
        "72", "73", "74", "75", "76", "77", "78", "79", "80"
    ]],
    "Titre IV. Prescriptions techniques": [f"Art. {n}" for n in ["81", "82", "82bis", "83"]],
    "Titre V. Dispositions abrogatoires et transitoires, et mise en vigueur": [f"Art. {n}" for n in ["84", "85", "86", "87"]],
}

for cat in RuleCategory.objects.all().order_by('order'):
    db_arts = list(CodeArticle.objects.filter(category=cat).order_by('order').values_list('article_number', flat=True))
    # Find matching official category
    matched = None
    for off_name, off_arts in OFFICIAL.items():
        if db_arts and db_arts[0] in off_arts:
            matched = off_name
            break

    if matched:
        off_arts = OFFICIAL[matched]
        if db_arts == off_arts:
            print(f"\n  {cat.name}: OK ({len(db_arts)} articles match)")
        else:
            extra = set(db_arts) - set(off_arts)
            missing = set(off_arts) - set(db_arts)
            print(f"\n  {cat.name} vs {matched}:")
            print(f"    DB: {len(db_arts)} articles, Official: {len(off_arts)} articles")
            if extra:
                print(f"    EXTRA in DB: {sorted(extra)}")
            if missing:
                print(f"    MISSING from DB: {sorted(missing)}")
    else:
        print(f"\n  {cat.name}: NO MATCH FOUND in official structure")
