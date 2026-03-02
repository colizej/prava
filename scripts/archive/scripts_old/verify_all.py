"""Full verification of all articles with inline images"""
import os, sys, re, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.reglementation.models import CodeArticle
from bs4 import BeautifulSoup

total_figures = 0
total_labels = 0
total_imgs = 0

for art in CodeArticle.objects.all().order_by("article_number"):
    soup = BeautifulSoup(art.content, "html.parser")
    # Check for old remote paths
    old_srcs = soup.find_all("img", src=re.compile(r"/media/image/orig/"))
    sign_imgs = soup.find_all("img", class_="sign-img")
    figures = soup.find_all("figure", class_="sign-figure")
    labels = soup.find_all("figcaption", class_="sign-label")

    if old_srcs or sign_imgs:
        total_imgs += len(sign_imgs)
        total_figures += len(figures)
        total_labels += len(labels)
        status = "✅" if not old_srcs else "❌ STILL HAS REMOTE PATHS"
        label_str = ", ".join(l.string for l in labels) if labels else "(none)"
        print(f"{status} {art.article_number}: {len(sign_imgs)} imgs, "
              f"{len(labels)} labels [{label_str}]"
              f"{f' ⚠ {len(old_srcs)} remote!' if old_srcs else ''}")

print(f"\nSUMMARY: {total_imgs} images, {total_figures} figures, "
      f"{total_labels} labels across all articles")
