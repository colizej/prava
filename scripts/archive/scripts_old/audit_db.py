#!/usr/bin/env python3
"""Audit all articles in DB for empty, short, or cut-off content."""
import django, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.reglementation.models import CodeArticle

PUNCT = set('.;:!?)\'"')

for a in CodeArticle.objects.all().order_by('category__order', 'order'):
    clen = len(a.content or '')
    text = (a.content_text or '').strip()
    flags = []
    if clen < 50:
        flags.append('EMPTY')
    elif clen < 200:
        flags.append('SHORT')
    if text and text[-1] not in PUNCT and clen > 50:
        flags.append('CUT-OFF')
    if flags:
        ending = text[-60:] if text else '(no text)'
        print(f"{a.article_number} | {clen} chars | {' '.join(flags)} | ...{ending}")

print(f"\n--- TOTAL: {CodeArticle.objects.count()} articles")
