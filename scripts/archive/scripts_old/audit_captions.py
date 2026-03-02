#!/usr/bin/env python3
"""
Find all places where sign descriptions exist without accompanying images.
Pattern: indented <em> text (padding-left paragraphs) that act as captions
but have no <img> nearby.
"""
import os, sys, django, re
os.chdir('/Users/colizej/Documents/webApp/prava')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle

print("=" * 80)
print("SEARCHING FOR SIGN CAPTIONS WITHOUT IMAGES")
print("=" * 80)

# Pattern: <p style="padding-left..."><em>some text</em> where no img in same or previous paragraph
# Also: bare sign codes like "F1 F3" in text without img tags

orphan_captions = []

for db_art in CodeArticle.objects.all().order_by('category__order', 'order'):
    content = db_art.content or ''
    if not content:
        continue

    # Split into paragraphs for analysis
    # Find all <p> with padding-left (indented = typically sign captions)
    indented_paras = re.findall(
        r'<p[^>]*style=["\'][^"\']*padding-left[^"\']*["\'][^>]*>(.*?)</p>',
        content, re.DOTALL | re.IGNORECASE
    )

    for para_content in indented_paras:
        # Does this paragraph have an img?
        has_img = bool(re.search(r'<img', para_content, re.IGNORECASE))
        # Strip tags to get text
        text = re.sub(r'<[^>]+>', '', para_content).strip()

        if not has_img and text and len(text) > 3:
            # Check if it looks like a sign caption (short italic text)
            is_italic = bool(re.search(r'<em>', para_content, re.IGNORECASE))
            if is_italic or len(text) < 100:
                orphan_captions.append({
                    'article': db_art.article_number,
                    'text': text[:100],
                    'has_italic': is_italic
                })

print(f"\nTotal orphan captions found: {len(orphan_captions)}")
print()

# Group by article
from itertools import groupby
from operator import itemgetter

orphan_captions.sort(key=itemgetter('article'))
for article, captions in groupby(orphan_captions, key=itemgetter('article')):
    caps = list(captions)
    print(f"\n  {article} ({len(caps)} captions):")
    for c in caps[:5]:
        indicator = "📝" if c['has_italic'] else "  "
        print(f"    {indicator} {repr(c['text'])}")
    if len(caps) > 5:
        print(f"    ... and {len(caps)-5} more")

# Now specifically show the raw HTML around Art. 85.2 and similar sections
print("\n\n" + "=" * 80)
print("CHECKING ARTICLES WITH SECTIONS = 0 IMGS IN SCRAPED (85, etc.)")
print("=" * 80)

# Also check for "Voir MB" references (official site note for missing model images)
voir_mb_arts = []
for db_art in CodeArticle.objects.all().order_by('category__order', 'order'):
    content = db_art.content or ''
    if 'Voir MB' in content or 'MB ' in content:
        voir_mb_count = len(re.findall(r'Voir MB|<Modèle', content))
        voir_mb_arts.append((db_art.article_number, voir_mb_count, content[:200]))

print(f"\nArticles with 'Voir MB' references: {len(voir_mb_arts)}")
for art, count, preview in voir_mb_arts:
    print(f"  {art}: {count} references")

# Show full 85.2 context with surrounding HTML
print("\n\n=== ART. 85 CONTENT ===")
art85 = CodeArticle.objects.get(article_number='Art. 85')
# Find 85.2 and show context
content = art85.content
idx = content.find('85.2')
if idx >= 0:
    section = content[idx:idx+1000]
    # Highlight paragraphs
    print(section)
