#!/usr/bin/env python3
"""Check Art. 72 images in scraped JSON and DB."""
import json, re, sys, os

# Check scraped JSON
with open('data/sites/codedelaroute.be/output/code_de_la_route_complet.json') as f:
    data = json.load(f)

articles = data['articles']
for art in articles:
    num = art.get('article_number', '')
    if num == 'Art. 72':
        content = art['content']
        img_count = content.count('<img')
        print(f"SCRAPED {num}: len={len(content)}, imgs={img_count}")
        for m in re.finditer(r'<img[^>]+>', content):
            print(f"  IMG: {m.group()[:150]}")
        break

# Check split JSON
for fname in ['03_signalisation_routiere.json']:
    fpath = f'data/reglementation/{fname}'
    if os.path.exists(fpath):
        with open(fpath) as f:
            theme = json.load(f)
        for art in theme['articles']:
            if art['article_number'] == 'Art. 72':
                content = art.get('content_html', art.get('content', ''))
                img_count = content.count('<img')
                print(f"\nSPLIT {art['article_number']}: len={len(content)}, imgs={img_count}")
                for m in re.finditer(r'<img[^>]+>', content):
                    print(f"  IMG: {m.group()[:150]}")
                break

# Check DB
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '.')
import django
django.setup()
from apps.reglementation.models import CodeArticle
a = CodeArticle.objects.get(article_number='Art. 72')
img_count = a.content.count('<img')
print(f"\nDB Art. 72: len={len(a.content)}, imgs={img_count}")
for m in re.finditer(r'<img[^>]+>', a.content):
    print(f"  IMG: {m.group()[:150]}")
