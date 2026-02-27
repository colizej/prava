#!/usr/bin/env python3
"""Analyze image display issues in article HTML."""
import django, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from bs4 import BeautifulSoup
from apps.reglementation.models import CodeArticle

art = CodeArticle.objects.get(article_number='Art. 71')
soup = BeautifulSoup(art.content, 'html.parser')

print("=== TABLE structure in Art.71 (first table, first 3 rows) ===")
for table in soup.find_all('table')[:1]:
    for tr in table.find_all('tr')[:3]:
        tds = tr.find_all('td')
        print(f'  Row: {len(tds)} cells')
        for td in tds:
            imgs = td.find_all('img')
            text = td.get_text(strip=True)[:50]
            style = td.get('style', '')[:60]
            print(f'    TD style="{style}" imgs={len(imgs)} text="{text}"')
            if imgs:
                for img in imgs:
                    w = img.get('width', '?')
                    h = img.get('height', '?')
                    print(f'      img w={w} h={h} src={img["src"][:50]}')
        print()

print("\n=== Checking S.30 context ===")
for p in soup.find_all('p'):
    text = p.get_text(strip=True)
    if 'S.30' in text or 'S.31' in text or 'S.32' in text:
        print(f'P style="{p.get("style","")[:60]}" text={text[:80]}')
        for img in p.find_all('img'):
            print(f'  img w={img.get("width","?")} src={img["src"][:60]}')
        print()

print("\n=== TABLE cell detail (rows 34-42) ===")
art71 = CodeArticle.objects.get(article_number='Art. 71')
soup71 = BeautifulSoup(art71.content, 'html.parser')
tables = soup71.find_all('table')
for table in tables[:1]:
    rows = table.find_all('tr')
    for i, tr in enumerate(rows):
        if 34 <= i <= 42:
            tds = tr.find_all('td')
            print(f"\n--- Row {i} ({len(tds)} cells) ---")
            for j, td in enumerate(tds):
                colspan = td.get('colspan', '1')
                style = td.get('style', '')[:60]
                print(f"  TD{j} colspan={colspan} style=\"{style}\"")
                print(f"    HTML: {str(td)[:600]}")
                print()

print("\n=== Image-only paragraphs across ALL articles ===")
count = 0
for a in CodeArticle.objects.all():
    s = BeautifulSoup(a.content, 'html.parser')
    for p in s.find_all('p'):
        imgs = p.find_all('img')
        text = p.get_text(strip=True)
        if imgs and len(text) < 5:
            count += 1
            if count <= 10:
                print(f'{a.article_number}: imgs={len(imgs)} html={str(p)[:200]}')
print(f"\nTotal image-only paragraphs: {count}")

print("\n=== Figure elements (from fix_article_images) across ALL ===")
fig_count = 0
for a in CodeArticle.objects.all():
    s = BeautifulSoup(a.content, 'html.parser')
    figs = s.find_all('figure')
    fig_count += len(figs)
    for fig in figs[:2]:
        print(f'{a.article_number}: {str(fig)[:200]}')
print(f"\nTotal figure elements: {fig_count}")
