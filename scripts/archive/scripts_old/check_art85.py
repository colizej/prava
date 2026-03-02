#!/usr/bin/env python3
"""Check article 85 content and image situation."""
import os, sys, django
os.chdir('/Users/colizej/Documents/webApp/prava')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle
import re

art = CodeArticle.objects.get(article_number='Art. 85')
print(f"Title: {art.title}")
print(f"Content length: {len(art.content)}")
print()

# Find all img tags
imgs = re.findall(r'<img[^>]+>', art.content, re.IGNORECASE)
print(f"=== IMG TAGS ({len(imgs)}) ===")
for img in imgs:
    src = re.search(r'src=["\']([^"\']+)["\']', img)
    alt = re.search(r'alt=["\']([^"\']*)["\']', img)
    print(f"  src: {src.group(1) if src else 'N/A'}")
    print(f"  alt: {alt.group(1) if alt else 'N/A'}")
    print()

# Find sign-gallery sections
galleries = re.findall(r'<div class="sign-gallery">.*?</div>\s*</div>', art.content, re.DOTALL)
print(f"=== SIGN GALLERIES ({len(galleries)}) ===")
for i, g in enumerate(galleries):
    print(f"\n--- Gallery {i+1} ---")
    print(g[:500])

# Find sign labels without images (text after sign codes like B22, C43 etc.)
print("\n\n=== FULL CONTENT (sections around '85.2') ===")
idx = art.content.find('85.2')
if idx >= 0:
    print(art.content[max(0, idx-100):idx+2000])
