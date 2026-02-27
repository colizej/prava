#!/usr/bin/env python3
"""Check the 15 problematic articles in detail."""
import json
import os
import sys
import django

os.chdir('/Users/colizej/Documents/webApp/prava')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle

# Load scraped data
with open('data/sites/codedelaroute.be/output/code_de_la_route_complet.json') as f:
    data = json.load(f)

# Build scraped map
scraped_map = {}
for art in data['articles']:
    num = art.get('number', '').rstrip('.')
    # Fix truncated numbers
    if num == '22no': num = '22novies'
    elif num == '22un': num = '22undecies'
    elif num == '22' and art.get('title', '') and 'decies' in art.get('title', '').lower():
        num = '22decies'
    scraped_map[num] = art

# Problem articles from deep_compare
problem_nums = ['11', '21', '22ter', '22quater', '22undecies', '35', '40', '40bis',
                '45bis', '48bis', '49', '57', '65', '78', '86']

print("=" * 80)
print("DETAILED CHECK OF 15 PROBLEMATIC ARTICLES")
print("=" * 80)

for num in problem_nums:
    db_art = CodeArticle.objects.filter(article_number=num).first()
    scraped = scraped_map.get(num)

    print(f"\n{'='*60}")
    print(f"ARTICLE {num}")
    print(f"{'='*60}")

    if db_art:
        db_html_len = len(db_art.content) if db_art.content else 0
        print(f"  DB title: {db_art.title[:80]}")
        print(f"  DB content length: {db_html_len}")
        # Check for sign-gallery wrappers (from fix_article_images)
        gallery_count = db_art.content.count('sign-gallery') if db_art.content else 0
        img_count = db_art.content.count('<img') if db_art.content else 0
        print(f"  DB sign-gallery sections: {gallery_count}")
        print(f"  DB <img> tags: {img_count}")
    else:
        print(f"  DB: NOT FOUND")
        db_html_len = 0

    if scraped:
        s_html = scraped.get('html', '')
        s_text = scraped.get('full_text', '')
        s_content = scraped.get('content', '')
        print(f"  Scraped title: {scraped.get('title', '')[:80]}")
        print(f"  Scraped HTML length: {len(s_html)}")
        print(f"  Scraped full_text length: {len(s_text)}")
        if isinstance(s_content, list):
            print(f"  Scraped content: list of {len(s_content)} items")
        else:
            print(f"  Scraped content length: {len(s_content) if s_content else 0}")

        if len(s_html) == 0 and len(s_text) > 0:
            print(f"  >>> HTML empty but full_text has content ({len(s_text)} chars)")
            print(f"  >>> full_text preview: {s_text[:150]}...")
        elif len(s_html) == 0 and isinstance(s_content, list) and len(s_content) > 0:
            print(f"  >>> HTML empty but content list has {len(s_content)} items")
        elif len(s_html) == 0:
            print(f"  >>> ALL scraped fields empty or minimal")
    else:
        print(f"  Scraped: NOT FOUND in scraped data!")

    # Determine likely cause
    if scraped and db_art:
        s_html_len = len(scraped.get('html', ''))
        if s_html_len == 0:
            print(f"  DIAGNOSIS: Scraped HTML was empty - our DB likely has re-scraped content (OK)")
        elif db_html_len > s_html_len * 1.3:
            extra = db_html_len - s_html_len
            if gallery_count > 0:
                print(f"  DIAGNOSIS: DB is {db_html_len - s_html_len} chars longer, likely from {gallery_count} sign-gallery wrappers")
            else:
                print(f"  DIAGNOSIS: DB is {extra} chars longer - NEEDS INVESTIGATION")
        elif s_html_len > db_html_len * 1.1:
            print(f"  DIAGNOSIS: Scraped is longer than DB - CONTENT MIGHT BE TRUNCATED IN DB")
        else:
            print(f"  DIAGNOSIS: Close enough")

print("\n\n" + "=" * 80)
print("TITLE COMPARISON (all 122 articles)")
print("=" * 80)

mismatched_titles = []
for db_art in CodeArticle.objects.all().order_by('category__order', 'order'):
    scraped = scraped_map.get(db_art.article_number)
    if scraped:
        s_title = scraped.get('title', '').strip()
        db_title = db_art.title.strip()
        # Normalize for comparison
        if s_title.lower() != db_title.lower():
            mismatched_titles.append((db_art.article_number, db_title, s_title))

if mismatched_titles:
    print(f"\n{len(mismatched_titles)} title mismatches found:")
    for num, db_t, s_t in mismatched_titles:
        print(f"\n  Art. {num}:")
        print(f"    DB:      {db_t}")
        print(f"    Scraped: {s_t}")
else:
    print("\nAll titles match!")
