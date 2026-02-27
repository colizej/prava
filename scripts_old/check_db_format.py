#!/usr/bin/env python3
"""Check DB article number formats."""
import os, sys, django
os.chdir('/Users/colizej/Documents/webApp/prava')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle

print("ALL DB article numbers:")
for art in CodeArticle.objects.all().order_by('category__order', 'order'):
    print(f"  '{art.article_number}' -> title: {art.title[:60]}")

print(f"\nTotal: {CodeArticle.objects.count()}")

# Check specific searches
for num in ['11', '11.', 'Art. 11', '11. ']:
    found = CodeArticle.objects.filter(article_number=num).exists()
    print(f"  Search '{num}': {'FOUND' if found else 'NOT FOUND'}")

# Try contains
for num in ['11', '21', '35']:
    found = CodeArticle.objects.filter(article_number__contains=num)
    for a in found:
        print(f"  Contains '{num}': article_number='{a.article_number}'")
