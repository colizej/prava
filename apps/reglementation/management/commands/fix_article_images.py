"""
Management command to fix inline images in article content.

1) Downloads all referenced images from codedelaroute.be to media/signs/
2) Rewrites <img src="/media/image/orig/HASH.png"> → local paths
3) Wraps each image + adjacent sign label in styled <figure> elements
4) Updates ArticleImage sign_codes from content patterns

Usage:
    python manage.py fix_article_images
    python manage.py fix_article_images --dry-run
"""
import os
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.reglementation.models import ArticleImage, CodeArticle

REMOTE_BASE = "https://www.codedelaroute.be"
LOCAL_SIGNS_DIR = Path(settings.MEDIA_ROOT) / "signs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Regex to match sign/panel codes like B1, F4a, C43, D9, M21, E9a, A23, etc.
SIGN_CODE_RE = re.compile(
    r"^[A-MS]\d{1,3}(?:(?:bis|ter|quater|quinquies|sexies|[a-z])(?:\.\d+)?)?$",
    re.IGNORECASE,
)


class Command(BaseCommand):
    help = "Download inline images and fix article content HTML"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview only")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # 1. Collect all unique remote image URLs across articles
        articles = CodeArticle.objects.all()
        url_map = {}  # remote_path -> local_path
        articles_to_fix = []

        for article in articles:
            remote_srcs = re.findall(
                r'src="(/media/image/orig/[^"]+)"', article.content
            )
            if remote_srcs:
                articles_to_fix.append(article)
                for src in remote_srcs:
                    if src not in url_map:
                        filename = src.split("/")[-1]
                        url_map[src] = f"/media/signs/{filename}"

        self.stdout.write(
            f"Found {len(url_map)} unique images across "
            f"{len(articles_to_fix)} articles"
        )

        if dry_run:
            for art in articles_to_fix:
                count = len(
                    re.findall(r'src="/media/image/orig/', art.content)
                )
                self.stdout.write(f"  {art.article_number}: {count} images")
            self.stdout.write("[DRY RUN] No changes made.")
            return

        # 2. Download images
        LOCAL_SIGNS_DIR.mkdir(parents=True, exist_ok=True)
        session = requests.Session()
        session.headers.update(HEADERS)

        downloaded = 0
        skipped = 0
        for remote_path, local_rel in url_map.items():
            filename = remote_path.split("/")[-1]
            local_path = LOCAL_SIGNS_DIR / filename
            if local_path.exists():
                skipped += 1
                continue

            url = REMOTE_BASE + remote_path
            try:
                resp = session.get(url, timeout=30)
                resp.raise_for_status()
                local_path.write_bytes(resp.content)
                downloaded += 1
                if downloaded % 20 == 0:
                    self.stdout.write(f"  Downloaded {downloaded}...")
                    time.sleep(0.3)
            except Exception as e:
                self.stderr.write(f"  ⚠ Failed to download {url}: {e}")

        self.stdout.write(
            f"📥 Downloaded {downloaded} images "
            f"({skipped} already existed)"
        )

        # 3. Rewrite content HTML for each article
        fixed_count = 0
        for article in articles_to_fix:
            new_content = self._rewrite_content(article.content, url_map)
            if new_content != article.content:
                article.content = new_content
                article.save(update_fields=["content"])
                fixed_count += 1

        self.stdout.write(f"✅ Fixed content in {fixed_count} articles")

        # 4. Update ArticleImage sign_codes
        self._update_article_image_codes()

        self.stdout.write(self.style.SUCCESS("🎉 Done!"))

    def _rewrite_content(self, html: str, url_map: dict) -> str:
        """
        Parse content HTML, replace remote image URLs with local ones,
        and wrap images with their adjacent sign labels in styled figures.
        """
        soup = BeautifulSoup(html, "html.parser")

        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src not in url_map:
                continue

            # Update src to local path
            img["src"] = url_map[src]

            # Don't set alt here — _wrap_sign_groups will handle it
            if "loading" not in img.attrs:
                img["loading"] = "lazy"

        # Wrap images in styled galleries and extract labels
        result = self._wrap_sign_groups(str(soup))
        return result

    def _collect_img_label_pairs(self, p_tag) -> list:
        """
        Walk through a <p> tag's children and build a list of
        (img_tag, label_str) pairs.

        Handles patterns like:
          <img/> M1  <img/> M2  <img/> M3
          M21 <img alt="M21" ...> description text
          <img/>C1 <img/> F19
        """
        pairs = []
        pending_label = ""  # label found BEFORE an img (e.g. "M21 <img ...>")

        for child in p_tag.children:
            if child.name == "img":
                # If we have a pending_label from text before this img, use it
                label = ""
                if pending_label:
                    label = pending_label
                    pending_label = ""
                else:
                    # Check alt attribute
                    alt = (child.get("alt") or "").strip()
                    if alt and SIGN_CODE_RE.match(alt):
                        label = alt

                pairs.append((child, label))

            elif isinstance(child, NavigableString):
                text = str(child).strip()
                if not text:
                    continue

                words = text.split()
                # Try to assign label to the PREVIOUS image (text after img)
                # Pattern: <img/> M1  <img/> M2 — "M1" goes to previous img
                if pairs and not pairs[-1][1]:
                    first_word = words[0]
                    if SIGN_CODE_RE.match(first_word):
                        # Assign to previous image
                        img, _ = pairs[-1]
                        pairs[-1] = (img, first_word)
                        words = words[1:]

                # Check if remaining words contain a label for the NEXT image
                # Pattern: M21 <img ...> — "M21" is a pending label
                if words:
                    last_word = words[-1]
                    if SIGN_CODE_RE.match(last_word):
                        pending_label = last_word

        return pairs

    def _wrap_sign_groups(self, html: str) -> str:
        """
        Find inline <img> tags inside <p> elements and wrap them
        in styled sign-gallery divs with proper labels.
        """
        soup = BeautifulSoup(html, "html.parser")

        for p_tag in soup.find_all("p"):
            imgs_in_p = p_tag.find_all("img")
            if not imgs_in_p:
                continue

            # Collect (img, label) pairs from the original DOM
            pairs = self._collect_img_label_pairs(p_tag)
            if not pairs:
                continue

            # Determine if this is a gallery (mostly images) or text with
            # inline images
            text_content = p_tag.get_text(strip=True)
            all_words = text_content.split()
            sign_words = [w for w in all_words if SIGN_CODE_RE.match(w)]
            non_sign_text = len(text_content) - sum(len(w) for w in sign_words)

            if len(imgs_in_p) >= 2 or (len(imgs_in_p) == 1 and non_sign_text < 30):
                # Sign gallery — rebuild as styled flex container
                new_div = soup.new_tag("div", **{"class": "sign-gallery"})

                for img, label in pairs:
                    figure = soup.new_tag("figure", **{"class": "sign-figure"})

                    new_img = soup.new_tag(
                        "img",
                        src=img.get("src", ""),
                        alt=f"Panneau {label}" if label else (
                            img.get("alt") or "Panneau routier"
                        ),
                        loading="lazy",
                        **{"class": "sign-img"},
                    )
                    figure.append(new_img)

                    if label:
                        caption = soup.new_tag(
                            "figcaption", **{"class": "sign-label"}
                        )
                        caption.string = label
                        figure.append(caption)

                    new_div.append(figure)

                p_tag.replace_with(new_div)
            else:
                # Regular paragraph with a single inline image + description
                # Wrap the image in a figure with label but keep surrounding text
                for img, label in pairs:
                    if label:
                        img["alt"] = f"Panneau {label}"

                        # Create a figure around the img in-place
                        figure = soup.new_tag("figure", **{"class": "sign-figure"})
                        new_img = soup.new_tag(
                            "img",
                            src=img.get("src", ""),
                            alt=f"Panneau {label}",
                            loading="lazy",
                            **{"class": "sign-img"},
                        )
                        figure.append(new_img)
                        caption = soup.new_tag(
                            "figcaption", **{"class": "sign-label"}
                        )
                        caption.string = label
                        figure.append(caption)
                        img.replace_with(figure)
                    elif not img.get("alt"):
                        img["alt"] = "Panneau routier"
                        if not img.get("alt") or img["alt"] == "":
                            img["alt"] = f"Panneau {label}"

        return str(soup)

    def _update_article_image_codes(self):
        """
        Try to fill in empty sign_code fields on ArticleImage records
        by matching image filenames to known sign code patterns.
        """
        updated = 0
        for ai in ArticleImage.objects.filter(sign_code=""):
            filename = os.path.basename(ai.image.name)
            # Try to extract sign code from filename pattern: artXX_CODE_N.png
            # e.g. art22quinquies_F101A_2.png → F101A
            match = re.search(r"_([A-MS]\d{1,3}[a-z]?)_", filename, re.IGNORECASE)
            if match:
                code = match.group(1).upper()
                ai.sign_code = code
                ai.alt_text = f"Panneau {code}"
                ai.save(update_fields=["sign_code", "alt_text"])
                updated += 1
                continue

            # Try to get from the parent article content
            article = ai.article
            content = article.content
            # Look for this image's sign context
            # ArticleImage order corresponds to the order of images in content
            imgs_in_content = re.findall(
                r'<img[^>]*src="[^"]*"[^>]*/?>(\s*[A-MS]\d{1,3}[a-z]?\b)?',
                content,
            )
            idx = ai.order
            if idx < len(imgs_in_content):
                label_text = imgs_in_content[idx].strip()
                if label_text and SIGN_CODE_RE.match(label_text):
                    ai.sign_code = label_text
                    ai.alt_text = f"Panneau {label_text}"
                    ai.save(update_fields=["sign_code", "alt_text"])
                    updated += 1

        self.stdout.write(f"🏷  Updated {updated} ArticleImage sign_codes")
