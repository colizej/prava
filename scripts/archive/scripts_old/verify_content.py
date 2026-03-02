#!/usr/bin/env python3
"""Verify content completeness after re-import."""
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle, ArticleImage

print(f"Articles: {CodeArticle.objects.count()}")
print(f"ArticleImages: {ArticleImage.objects.count()}")

# Check ALL articles for images
print("\n=== Articles with images ===")
total_imgs = 0
for a in CodeArticle.objects.all().order_by('order'):
    img_count = a.content.count('<img')
    total_imgs += img_count
    has_table = '<table' in a.content
    has_list = '<ul>' in a.content or '<ol>' in a.content
    has_notif = 'notification' in a.content
    if img_count or has_table or has_list or has_notif:
        markers = []
        if img_count: markers.append(f"🖼{img_count}")
        if has_table: markers.append("📊")
        if has_list: markers.append("📝")
        if has_notif: markers.append("ℹ️")
        print(f"  {a.article_number}: {' '.join(markers)}  len={len(a.content)}")

print(f"\nTotal inline images: {total_imgs}")

# Check previously-truncated articles
print("\n=== Previously truncated articles ===")
for num in ['Art. 2', 'Art. 16', 'Art. 18', 'Art. 21', 'Art. 23',
            'Art. 40', 'Art. 47bis', 'Art. 49', 'Art. 77', 'Art. 82', 'Art. 82bis', 'Art. 86']:
    try:
        a = CodeArticle.objects.get(article_number=num)
        ends_colon = a.content.rstrip().rstrip('</p>').rstrip().endswith(':')
        print(f"  {num}: len={len(a.content)}, ends_colon={ends_colon}")
    except CodeArticle.DoesNotExist:
        print(f"  {num}: NOT FOUND")

# Chapitre III - road markings
print("\n=== Chapitre III. Marques routières ===")
for num in ['Art. 72', 'Art. 73', 'Art. 74', 'Art. 75', 'Art. 76', 'Art. 77']:
    a = CodeArticle.objects.get(article_number=num)
    img_count = a.content.count('<img')
    print(f"  {num}: {img_count} images, len={len(a.content)}")

# Count local vs remote image paths
import re
local = 0
remote = 0
for a in CodeArticle.objects.all():
    local += len(re.findall(r'src="/media/signs/', a.content))
    remote += len(re.findall(r'src="/media/image/orig/', a.content))
print(f"\nImage paths: {local} local (/media/signs/), {remote} remote (/media/image/orig/)")

# Files on disk
import glob
signs = glob.glob('/Users/colizej/Documents/webApp/prava/media/signs/*')
print(f"Files in media/signs/: {len(signs)}")

