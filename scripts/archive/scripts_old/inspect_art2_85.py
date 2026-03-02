#!/usr/bin/env python3
import django
import os
import sys
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle, ArticleImage

print("=== Art. 2 ArticleImage entries ===")
try:
    art2 = CodeArticle.objects.get(article_number='Art. 2')
    for ai in art2.images.all()[:10]:
        print("  sign_code:", ai.sign_code, "| alt_text:", ai.alt_text, "| image:", str(ai.image))
    print("  Total:", art2.images.count())

    print()
    print("=== Art. 2 content img tags ===")
    imgs = re.findall(r'<img[^>]+>', art2.content or "")
    print("Inline img tags:", len(imgs))
    if imgs:
        for img in imgs[:5]:
            print(" ", repr(img[:200]))

    # What about the content structure?
    print()
    print("F1/F3 in Art.2 content:")
    for m in re.finditer(r'(?:F1|F3)[^a-z0-9]', art2.content or ""):
        start = max(0, m.start()-30)
        end = min(len(art2.content), m.end()+60)
        print(" ", repr(art2.content[start:end]))
except CodeArticle.DoesNotExist:
    print("'Art. 2' not found")

print()
print("=== Art. 85 ArticleImage entries ===")
try:
    art85 = CodeArticle.objects.get(article_number='Art. 85')
    for ai in art85.images.all()[:10]:
        print("  sign_code:", ai.sign_code, "| alt_text:", ai.alt_text, "| image:", str(ai.image))
    print("  Total:", art85.images.count())

    print()
    print("=== Art. 85 content img tags ===")
    imgs = re.findall(r'<img[^>]+>', art85.content or "")
    print("Inline img tags:", len(imgs))
    for img in imgs:
        print(" ", repr(img[:200]))

    print()
    print("=== Art. 85.2 section ===")
    c = art85.content or ""
    idx = c.find('85.2')
    if idx >= 0:
        print(c[idx:idx+500])
except CodeArticle.DoesNotExist:
    print("'Art. 85' not found")

print()
print("=== ArticleImages for F1/F3 signs ===")
for ai in ArticleImage.objects.filter(sign_code__in=['F1', 'F3']):
    print("  article:", ai.article.article_number, "| sign_code:", ai.sign_code, "| image:", str(ai.image))
