"""Verify Art. 65 labels after fix_article_images"""
import os, sys, re, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.reglementation.models import CodeArticle
from bs4 import BeautifulSoup

art = CodeArticle.objects.get(article_number="Art. 65")
soup = BeautifulSoup(art.content, "html.parser")

# Count sign-gallery divs and sign-figure/sign-label elements
galleries = soup.find_all("div", class_="sign-gallery")
figures = soup.find_all("figure", class_="sign-figure")
labels = soup.find_all("figcaption", class_="sign-label")
imgs = soup.find_all("img", class_="sign-img")

print(f"Art. 65 results:")
print(f"  Galleries: {len(galleries)}")
print(f"  Figures:   {len(figures)}")
print(f"  Labels:    {len(labels)}")
print(f"  Images:    {len(imgs)}")
print(f"\nLabels found:")
for label in labels:
    print(f"  {label.string}")

# Also check a few other articles
for art_num in ['Art. 22quater', 'Art. 9', 'Art. 40']:
    try:
        a = CodeArticle.objects.get(article_number=art_num)
        s = BeautifulSoup(a.content, "html.parser")
        fig = s.find_all("figure", class_="sign-figure")
        lab = s.find_all("figcaption", class_="sign-label")
        print(f"\n{art_num}: {len(fig)} figures, {len(lab)} labels")
        for l in lab:
            print(f"  {l.string}")
    except CodeArticle.DoesNotExist:
        print(f"\n{art_num}: not found")
