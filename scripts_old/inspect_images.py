#!/usr/bin/env python3
import django
import os
import sys
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle, ArticleImage, TrafficSign

print("=== Model counts ===")
print("CodeArticle:", CodeArticle.objects.count())
print("ArticleImage:", ArticleImage.objects.count())
print("TrafficSign:", TrafficSign.objects.count())

print()
print("=== ArticleImage examples ===")
for ai in ArticleImage.objects.all()[:5]:
    print("  article:", ai.article.article_number, "| caption:", repr(ai.caption)[:60], "| image:", str(ai.image)[:60])

print()
print("=== TrafficSign examples ===")
for ts in TrafficSign.objects.all()[:5]:
    print("  code:", ts.code, "| description:", repr(ts.description)[:60], "| image:", str(ts.image)[:60])

print()
print("=== CodeArticle 'Art. 2' content snippet ===")
try:
    art2 = CodeArticle.objects.get(article_number='Art. 2')
    c = art2.content or ""
    print("Content length:", len(c))
    imgs = re.findall(r'<img[^>]+>', c)
    print("Img tags:", len(imgs))
    if imgs:
        for img in imgs[:3]:
            print(" ", repr(img[:200]))
    # Show content around 2.12
    idx = c.find('2.12')
    if idx >= 0:
        print("Content around 2.12:")
        print(c[idx:idx+500])
except CodeArticle.DoesNotExist:
    print("'Art. 2' not found")
    # Show all articles
    for a in CodeArticle.objects.all()[:20]:
        print(" ", repr(a.article_number))

print()
print("=== CodeArticle 'Art. 85' content around 85.2 ===")
try:
    art85 = CodeArticle.objects.get(article_number='Art. 85')
    c = art85.content or ""
    idx = c.find('85.2')
    if idx >= 0:
        print(c[idx:idx+600])
except CodeArticle.DoesNotExist:
    print("'Art. 85' not found")
