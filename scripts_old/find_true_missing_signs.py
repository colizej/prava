#!/usr/bin/env python3
"""
Find TRUE missing sign image captions — short <em> texts in padding-left paragraphs
that look like sign names/descriptions, not numbered list items.
"""
import django
import os
import sys
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle

# Pattern for list items (false positives):
# - Starts with digit(s) + °
# - Starts with letter(s) + )
# - Starts with - or *
# - Long text (> 80 chars)
LIST_ITEM_PATTERN = re.compile(
    r'^(\d+[°º]|[a-z]\)|[-*•]|\w+\s+\w+\s+\w+\s+\w+\s+\w+)',  # numbered or long
)

candidates = []

for art in CodeArticle.objects.all():
    content = art.content or ""

    # Find all padding-left paragraphs with <em> but no <img>
    paras = re.findall(r'<p[^>]*padding-left[^>]*>(.*?)</p>', content, re.DOTALL)

    for para in paras:
        if '<img' in para:
            continue  # has image, skip

        em_texts = re.findall(r'<em>(.*?)</em>', para, re.DOTALL)
        for em_text in em_texts:
            # Clean HTML tags
            text = re.sub(r'<[^>]+>', '', em_text).strip()
            if not text:
                continue

            # Skip if it's a list item (false positive)
            if LIST_ITEM_PATTERN.match(text):
                continue

            # Skip very long texts (not a sign name)
            if len(text) > 100:
                continue

            # Skip if starts with uppercase word followed by many words (legal text)
            words = text.split()
            if len(words) > 8:
                continue

            # Check: does it look like a sign caption?
            # Sign captions typically: "F1. Commencement...", "Début de...", "Fin de..."
            # Or literally sign type descriptions
            looks_like_sign = (
                re.match(r'^[A-Z]\d', text) or  # starts with sign code like F1, C3
                'agglomér' in text.lower() or
                'commencement' in text.lower() or
                'début' in text.lower() or
                'fin d' in text.lower() or
                'signal' in text.lower() or
                'zone' in text.lower() or
                len(text) < 60
            )

            if looks_like_sign:
                candidates.append({
                    'article': art.article_number,
                    'text': text,
                    'para_snippet': re.sub(r'<[^>]+>', '', para[:80]).strip()
                })

print("=== Candidate missing sign image captions ===")
print("Total:", len(candidates))
print()

for c in candidates:
    print("Art.", c['article'], ":", repr(c['text'][:80]))

print()
print("=== Summary by article ===")
from collections import defaultdict
by_art = defaultdict(list)
for c in candidates:
    by_art[c['article']].append(c['text'])

for art_num, texts in sorted(by_art.items()):
    print(art_num, ":", len(texts), "candidates")
    for t in texts[:5]:
        print("  -", repr(t[:70]))
