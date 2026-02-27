"""
import_reglementation — Import regulation JSON files into the database.

Usage:
    python manage.py import_reglementation                  # all files
    python manage.py import_reglementation 01_regles_circulation.json
    python manage.py import_reglementation --clear           # wipe + reimport
"""
import json
import os
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.reglementation.models import RuleCategory, CodeArticle, ArticleImage


DATA_DIR = Path("data/reglementation")
IMAGES_SRC = Path("data/sites/codedelaroute.be/output/images")
IMAGES_DST = Path("media/reglementation")


class Command(BaseCommand):
    help = "Import regulation articles from JSON files in data/reglementation/"

    def add_arguments(self, parser):
        parser.add_argument(
            "files",
            nargs="*",
            help="Specific JSON filenames to import (default: all *.json in data/reglementation/)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing categories & articles before import.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            n_img, _ = ArticleImage.objects.all().delete()
            n_art, _ = CodeArticle.objects.all().delete()
            n_cat, _ = RuleCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"  🗑  Cleared {n_cat} categories, {n_art} articles, {n_img} images."
            ))

        # Ensure images dir exists
        IMAGES_DST.mkdir(parents=True, exist_ok=True)

        # Determine files to process
        if options["files"]:
            json_files = [DATA_DIR / f for f in options["files"]]
        else:
            json_files = sorted(DATA_DIR.glob("*.json"))

        if not json_files:
            self.stdout.write(self.style.ERROR("No JSON files found in data/reglementation/"))
            return

        total_articles = 0
        total_images = 0

        for json_path in json_files:
            if not json_path.exists():
                self.stdout.write(self.style.ERROR(f"  ✗ File not found: {json_path}"))
                continue

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            theme = data["theme"]
            articles = data["articles"]

            # Create or update category
            cat, created = RuleCategory.objects.update_or_create(
                slug=theme["slug"],
                defaults={
                    "name": theme["name"],
                    "name_nl": theme.get("name_nl", ""),
                    "name_ru": theme.get("name_ru", ""),
                    "icon": theme.get("icon", ""),
                    "description": theme.get("description", ""),
                    "description_nl": theme.get("description_nl", ""),
                    "description_ru": theme.get("description_ru", ""),
                    "order": int(json_path.stem.split("_")[0]) if json_path.stem[0].isdigit() else 0,
                    "is_active": True,
                },
            )
            action = "created" if created else "updated"
            self.stdout.write(f"  📂 Category «{cat.name}» — {action}")

            # Import articles
            art_count = 0
            img_count = 0
            for art_data in articles:
                slug = slugify(f"{art_data['article_number']}-{art_data['title']}")[:250]

                # Build HTML content from available data
                content_html = art_data.get("content_html", "")
                if not content_html and art_data.get("content_paragraphs"):
                    content_html = "\n".join(
                        f"<p>{p}</p>" for p in art_data["content_paragraphs"]
                    )

                content_text = art_data.get("content_text", "")

                article_obj, _ = CodeArticle.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "article_number": art_data["article_number"],
                        "category": cat,
                        "title": art_data["title"],
                        "content": content_html,
                        "content_text": content_text,
                        "is_free": True,
                        "order": art_data.get("order", 0),
                    },
                )
                art_count += 1

                # Import images if present
                images = art_data.get("images", [])
                if images:
                    # Clear existing images for this article
                    article_obj.images.all().delete()

                    for i, img_data in enumerate(images):
                        fname = img_data["filename"]
                        src_path = IMAGES_SRC / fname
                        dst_path = IMAGES_DST / fname

                        # Copy image file if not already there
                        if src_path.exists() and not dst_path.exists():
                            shutil.copy2(src_path, dst_path)

                        if dst_path.exists():
                            ArticleImage.objects.create(
                                article=article_obj,
                                image=f"reglementation/{fname}",
                                alt_text=img_data.get("alt", ""),
                                sign_code=img_data.get("sign_code", ""),
                                order=i,
                            )
                            img_count += 1

            total_articles += art_count
            total_images += img_count
            self.stdout.write(self.style.SUCCESS(
                f"      ✅ {art_count} articles, {img_count} images imported"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\n  🎉 Done! {total_articles} articles, {total_images} images "
            f"across {len(json_files)} theme(s)."
        ))
