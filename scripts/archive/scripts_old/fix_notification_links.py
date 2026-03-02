#!/usr/bin/env python3
"""
Smart notification link routing:
  - Links to articles we have → internal link to our article page
  - Links to external laws/decrees → original codedelaroute.be (or other sites)

Anchor patterns recognised:
    #art-21         → Art. 21
    #art-22bis      → Art. 22bis
    #art9.8         → Art. 9  (subsection .8)
    #11.3           → Art. 11 (subsection .3)

Internal links: no target="_blank", normal navigation.
External links: target="_blank" rel="noopener".
"""
import django
import os
import re
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, "/Users/colizej/Documents/webApp/prava")
django.setup()

from bs4 import BeautifulSoup
from apps.reglementation.models import CodeArticle

BASE = "https://www.codedelaroute.be"
PAGE_URL = "https://www.codedelaroute.be/fr/reglementation/1975120109~hra8v386pu"

DRY_RUN = "--dry-run" in sys.argv

# ── Build article lookup: "21" → slug, "22bis" → slug, etc. ──
article_map = {}  # key → (article_number, slug)
for a in CodeArticle.objects.all():
    # "Art. 22bis" → "22bis"
    num = a.article_number.replace("Art. ", "").strip()
    article_map[num.lower()] = (a.article_number, a.slug)

# Regex to extract article number from anchor:
#   #art-22bis  → "22bis"
#   #art9.8     → "9"  (dot = subsection)
#   #11.3       → "11" (just number.subsection)
RE_ANCHOR_ART = re.compile(
    r'^#art[-.]?(\d+(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|un)?)',
    re.IGNORECASE,
)
RE_ANCHOR_NUM = re.compile(r'^#(\d+)\.')  # e.g. #11.3


def resolve_anchor(href):
    """Try to resolve an anchor href to a local article slug.
    Returns (article_number, slug) or (None, None).
    """
    m = RE_ANCHOR_ART.match(href)
    if m:
        key = m.group(1).lower()
        if key in article_map:
            return article_map[key]
        # Try truncated suffixes: "22undecies" → "22un"
        # (some article_numbers are abbreviated in DB)
        for suffix_len in range(2, len(key)):
            short = key[:suffix_len]
            if short in article_map and not short.isdigit():
                return article_map[short]
    m = RE_ANCHOR_NUM.match(href)
    if m:
        key = m.group(1).lower()
        if key in article_map:
            return article_map[key]
    return None, None


updated = 0
internal_count = 0
external_count = 0

for article in CodeArticle.objects.all():
    soup = BeautifulSoup(article.content, "html.parser")
    notifs = soup.find_all("div", class_="notification")
    if not notifs:
        continue

    changed = False
    for notif in notifs:
        for a_tag in notif.find_all("a", href=True):
            href = a_tag["href"]

            # ── 1. Already-converted codedelaroute.be article anchor ──
            #    e.g. https://www.codedelaroute.be/fr/reglementation/1975120109~hra8v386pu#art-21
            if PAGE_URL in href and "#" in href:
                anchor = "#" + href.split("#", 1)[1]
                art_number, slug = resolve_anchor(anchor)
                if slug:
                    a_tag["href"] = f"/reglementation/{slug}/"
                    a_tag.attrs.pop("target", None)
                    a_tag.attrs.pop("rel", None)
                    changed = True
                    internal_count += 1
                    if DRY_RUN:
                        print(f"  INT {article.article_number}: {href[:60]} → /reglementation/{slug}/")
                    continue
                # Article not found — keep external
                a_tag["target"] = "_blank"
                a_tag["rel"] = "noopener"
                external_count += 1
                if DRY_RUN:
                    print(f"  EXT {article.article_number}: {href[:80]} (article not in DB)")
                continue

            # ── 2. Raw anchor (shouldn't exist after v1, but just in case) ──
            if href.startswith("#"):
                art_number, slug = resolve_anchor(href)
                if slug:
                    a_tag["href"] = f"/reglementation/{slug}/"
                    a_tag.attrs.pop("target", None)
                    a_tag.attrs.pop("rel", None)
                    changed = True
                    internal_count += 1
                    continue
                # Unknown anchor → send to original site
                a_tag["href"] = PAGE_URL + href
                a_tag["target"] = "_blank"
                a_tag["rel"] = "noopener"
                changed = True
                external_count += 1
                continue

            # ── 3. External links (other laws, decrees, etc.) ──
            # Already absolute → just ensure target="_blank"
            a_tag["target"] = "_blank"
            a_tag["rel"] = "noopener"
            external_count += 1

    if changed:
        new_content = str(soup)
        if not DRY_RUN:
            article.content = new_content
            article.save(update_fields=["content"])
        updated += 1

action = "[DRY RUN] Would update" if DRY_RUN else "Updated"
print(f"\n{action} {updated} articles")
print(f"  Internal links (→ our articles): {internal_count}")
print(f"  External links (→ original sites): {external_count}")
