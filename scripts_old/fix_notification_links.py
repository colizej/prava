#!/usr/bin/env python3
"""
Convert notification links to point to the original codedelaroute.be site.

Transforms:
    #art-21         → https://www.codedelaroute.be/fr/reglementation/...#art-21
    #art9.8         → same with anchor
    #11.3           → same with anchor
    /fr/perma/...   → https://www.codedelaroute.be/fr/perma/...

Adds target="_blank" and rel="noopener" to all notification links.
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
# The page URL where article anchors live
PAGE_URL = "https://www.codedelaroute.be/fr/reglementation/1975120109~hra8v386pu"

DRY_RUN = "--dry-run" in sys.argv

updated = 0
links_fixed = 0

for article in CodeArticle.objects.all():
    soup = BeautifulSoup(article.content, "html.parser")
    notifs = soup.find_all("div", class_="notification")
    if not notifs:
        continue

    changed = False
    for notif in notifs:
        for a_tag in notif.find_all("a", href=True):
            href = a_tag["href"]
            new_href = None

            if href.startswith("#"):
                # Anchor link → full page URL + anchor
                new_href = PAGE_URL + href
            elif href.startswith("/"):
                # Relative link → absolute on codedelaroute.be
                new_href = BASE + href
            # Already absolute links (http/https) — leave as is

            if new_href and new_href != href:
                a_tag["href"] = new_href
                changed = True
                links_fixed += 1

            # Add target="_blank" to all notification links
            a_tag["target"] = "_blank"
            a_tag["rel"] = "noopener"

    if changed:
        new_content = str(soup)
        if not DRY_RUN:
            article.content = new_content
            article.save(update_fields=["content"])
        updated += 1

action = "[DRY RUN] Would update" if DRY_RUN else "Updated"
print(f"{action} {updated} articles, {links_fixed} links converted")
