"""Fix truncated article numbers in the database."""
import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils.text import slugify
from apps.reglementation.models import CodeArticle

# Fix Art. 22no -> Art. 22novies
# Fix Art. 22un -> Art. 22undecies
fixes = [
    ("Art. 22no", "Art. 22novies"),
    ("Art. 22un", "Art. 22undecies"),
]

for old_num, new_num in fixes:
    try:
        art = CodeArticle.objects.get(article_number=old_num)
        old_slug = art.slug
        art.article_number = new_num
        art.slug = slugify(f"{new_num} {art.title}")[:200]
        art.save(update_fields=["article_number", "slug"])
        print(f"OK {old_num} -> {new_num} (slug: {art.slug})")
    except CodeArticle.DoesNotExist:
        print(f"NOT FOUND: {old_num}")

# Fix the duplicate Art. 22 -> Art. 22decies
for art in CodeArticle.objects.filter(article_number="Art. 22"):
    if "22decies" in art.title:
        art.article_number = "Art. 22decies"
        art.slug = slugify(f"Art. 22decies {art.title}")[:200]
        art.save(update_fields=["article_number", "slug"])
        print(f"OK Art. 22 (decies) -> Art. 22decies (slug: {art.slug})")

# Verify
print("\nVerification:")
for num in ["Art. 22novies", "Art. 22decies", "Art. 22undecies", "Art. 22"]:
    for a in CodeArticle.objects.filter(article_number=num):
        print(f"  {a.article_number} -- {a.title[:70]}")
