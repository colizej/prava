#!/usr/bin/env python3
"""
Detailed content comparison: strip sign-gallery wrappers from DB content,
then compare with scraped HTML to find REAL differences.
Also fetch live pages for articles with empty scraped HTML.
"""
import django, os, json, sys, re
from html.parser import HTMLParser

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.reglementation.models import CodeArticle

# Load scraped data
with open('data/sites/codedelaroute.be/output/code_de_la_route_complet.json') as f:
    scraped = json.load(f)

# Build scraped map
scraped_map = {}
for art in scraped['articles']:
    num = art.get('number', '').rstrip('.')
    if num == '22no': num = '22novies'
    elif num == '22un': num = '22undecies'
    elif num == '22' and art.get('title', '').startswith('Article 22decies'):
        num = '22decies'
    key = f"Art. {num}"
    scraped_map[key] = art

def strip_galleries(html):
    """Remove sign-gallery sections added by fix_article_images."""
    # Remove <div class="sign-gallery">...</div> blocks
    cleaned = re.sub(r'<div class="sign-gallery">.*?</div>\s*</div>', '', html, flags=re.DOTALL)
    # Also remove standalone sign figures if any leftover
    cleaned = re.sub(r'<figure class="sign-figure">.*?</figure>', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

def extract_text(html):
    """Extract plain text from HTML."""
    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.result = []
        def handle_data(self, data):
            self.result.append(data)

    if not html:
        return ''
    e = TextExtractor()
    e.feed(html)
    return ' '.join(''.join(e.result).split())

def normalize_html(html):
    """Normalize HTML for comparison."""
    if not html:
        return ''
    # Remove excessive whitespace
    h = re.sub(r'\s+', ' ', html)
    # Remove style attributes
    h = re.sub(r'\s*style="[^"]*"', '', h)
    # Remove class attributes
    h = re.sub(r'\s*class="[^"]*"', '', h)
    # Remove data attributes
    h = re.sub(r'\s*data-\w+="[^"]*"', '', h)
    return h.strip()

# Problem articles from deep_compare
problem_keys = [
    'Art. 11', 'Art. 21', 'Art. 22ter', 'Art. 22quater', 'Art. 22undecies',
    'Art. 35', 'Art. 40', 'Art. 40bis', 'Art. 45bis', 'Art. 48bis',
    'Art. 49', 'Art. 57', 'Art. 65', 'Art. 78', 'Art. 86'
]

print("=" * 100)
print("DETAILED CONTENT ANALYSIS OF 15 PROBLEMATIC ARTICLES")
print("=" * 100)

for key in problem_keys:
    db_art = CodeArticle.objects.filter(article_number=key).first()
    s_art = scraped_map.get(key)

    if not db_art or not s_art:
        print(f"\n{'='*80}")
        print(f"{key}: {'DB missing' if not db_art else 'Scraped missing'}")
        continue

    db_html = db_art.content or ''
    s_html = s_art.get('html', '')

    # Strip galleries from DB content
    db_cleaned = strip_galleries(db_html)

    # Extract text
    db_text = extract_text(db_cleaned)
    s_text = extract_text(s_html)

    # Lengths
    db_raw_len = len(db_html)
    db_clean_len = len(db_cleaned)
    s_len = len(s_html)
    gallery_overhead = db_raw_len - db_clean_len

    print(f"\n{'='*80}")
    print(f"{key}: {db_art.title[:60]}")
    print(f"  DB raw HTML:     {db_raw_len:>6d} chars")
    print(f"  DB cleaned HTML: {db_clean_len:>6d} chars (gallery overhead: {gallery_overhead})")
    print(f"  Scraped HTML:    {s_len:>6d} chars")

    if s_len == 0:
        print(f"  >>> Scraped HTML is EMPTY - article was not scraped properly")
        print(f"  >>> DB has content ({db_raw_len} chars) - likely from manual/re-import")
        print(f"  DB text preview: {db_text[:200]}")
        continue

    # Compare cleaned DB vs scraped
    clean_ratio = db_clean_len / s_len if s_len > 0 else 0
    text_ratio = len(db_text) / len(s_text) if len(s_text) > 0 else 0

    print(f"  Clean HTML ratio: {clean_ratio:.2f}")
    print(f"  Text ratio:       {text_ratio:.2f}")

    if 0.85 <= clean_ratio <= 1.15 and 0.85 <= text_ratio <= 1.15:
        print(f"  VERDICT: OK after stripping galleries")
        continue

    # Show differences
    print(f"\n  --- DB text ({len(db_text)} chars) ---")
    print(f"  {db_text[:300]}")
    print(f"\n  --- Scraped text ({len(s_text)} chars) ---")
    print(f"  {s_text[:300]}")

    # Check if DB text contains scraped text
    if s_text and s_text in db_text:
        extra = len(db_text) - len(s_text)
        print(f"\n  VERDICT: DB CONTAINS all scraped text + {extra} extra chars")
    elif db_text and db_text in s_text:
        missing = len(s_text) - len(db_text)
        print(f"\n  VERDICT: DB text is SUBSET of scraped ({missing} chars missing)")
    else:
        # Find common prefix length
        common = 0
        min_len = min(len(db_text), len(s_text))
        for i in range(min_len):
            if db_text[i] == s_text[i]:
                common += 1
            else:
                break
        print(f"\n  VERDICT: DIFFERENT CONTENT (common prefix: {common} chars)")
        if common < min_len:
            print(f"  Diverges at char {common}:")
            print(f"    DB:      ...{db_text[max(0,common-20):common+50]}...")
            print(f"    Scraped: ...{s_text[max(0,common-20):common+50]}...")

print("\n\n" + "=" * 100)
print("FULL COMPARISON: ALL 122 ARTICLES (after gallery stripping)")
print("=" * 100)

categories = {
    'empty_scraped': [],
    'gallery_only_diff': [],
    'real_content_diff': [],
    'ok': [],
}

for db_art in CodeArticle.objects.all().order_by('category__order', 'order'):
    key = db_art.article_number
    s_art = scraped_map.get(key)

    if not s_art:
        categories['real_content_diff'].append((key, "NOT IN SCRAPED DATA"))
        continue

    db_html = db_art.content or ''
    s_html = s_art.get('html', '')

    if len(s_html) == 0:
        categories['empty_scraped'].append(key)
        continue

    db_cleaned = strip_galleries(db_html)
    clean_ratio = len(db_cleaned) / len(s_html) if len(s_html) > 0 else 0

    if 0.85 <= clean_ratio <= 1.15:
        categories['ok'].append(key)
    elif len(db_html) > len(db_cleaned) and 0.85 <= clean_ratio <= 1.15:
        # Gallery overhead was the issue
        categories['gallery_only_diff'].append(key)
    else:
        db_text = extract_text(db_cleaned)
        s_text = extract_text(s_html)
        text_ratio = len(db_text) / len(s_text) if len(s_text) > 0 else 0
        categories['real_content_diff'].append((key, f"clean_ratio={clean_ratio:.2f}, text_ratio={text_ratio:.2f}"))

print(f"\n  OK articles (content matches after cleanup): {len(categories['ok'])}")
print(f"  Empty scraped HTML (our DB has content): {len(categories['empty_scraped'])}")
print(f"    {', '.join(categories['empty_scraped'])}")
print(f"  Gallery-only difference: {len(categories['gallery_only_diff'])}")
print(f"    {', '.join(categories['gallery_only_diff'])}")
print(f"  REAL content differences: {len(categories['real_content_diff'])}")
for item in categories['real_content_diff']:
    if isinstance(item, tuple):
        print(f"    {item[0]}: {item[1]}")
    else:
        print(f"    {item}")
