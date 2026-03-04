#!/usr/bin/env python3
"""
Download traffic sign images from codedelaroute.be.
Builds a map of sign_code → image_url by scanning:
  1. data/sources/codedelaroute.be/images_analysis.json
  2. Article HTML content in the DB (img alt attributes)
Then downloads missing images to media/signs/<code>.png
and updates TrafficSign.image in the DB.
"""
import os
import re
import sys
import ssl
import json
import time
import urllib.request
from pathlib import Path

# Add project root to path so Django can find 'config'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# SSL context that skips certificate verification (safe for downloading public images)
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

from apps.reglementation.models import TrafficSign, CodeArticle

BASE_URL = 'https://www.codedelaroute.be'
SIGNS_DIR = Path('media/signs')
SIGNS_DIR.mkdir(parents=True, exist_ok=True)

# Wikimedia Commons thumbnail URL for Belgian road signs
# Two naming conventions exist on Wikimedia
WIKI_PATTERNS = [
    'https://commons.wikimedia.org/wiki/Special:FilePath/Belgian_road_sign_{code}.svg?width=150',
    'https://commons.wikimedia.org/wiki/Special:FilePath/Belgian_traffic_sign_{code}.svg?width=150',
]

# Signs to skip for Wikimedia (already have from codedelaroute or not sign-like codes)
WIKI_SKIP = {'p_begin', 'p_einde', 'rue_scolaire', 'F101A', 'E9j_FR',
             '7_19_blauw', '7_19_wit', 'Lading', 'Wegmarkering_75.3',
             'ZE1+M22', 'elec', 'elec_auto', 'laden_en_lossen'}

# ── Step 1: build code → URL map ─────────────────────────────────────────────

code_to_url = {}

# Source A: images_analysis.json
analysis = Path('data/sources/codedelaroute.be/images_analysis.json')
if analysis.exists():
    data = json.loads(analysis.read_text())
    for img in data.get('images', []):
        alt = (img.get('alt') or '').strip()
        code = re.sub(r'\.png$', '', alt).replace(' ', '_')
        full_url = img.get('full_url', '')
        if code and full_url:
            code_to_url[code] = full_url

print(f'[analysis.json] {len(code_to_url)} code→URL entries')

# Source B: scraped article HTML in DB (both alt-before-src and src-before-alt)
IMG_PATTERNS = [
    re.compile(r'<img[^>]*\balt="([^"]+)"[^>]*\bsrc="(https?://[^"]+codedelaroute\.be[^"]+)"', re.I),
    re.compile(r'<img[^>]*\bsrc="(https?://[^"]+codedelaroute\.be[^"]+)"[^>]*\balt="([^"]+)"', re.I),
]

for art in CodeArticle.objects.all():
    for html in [art.content, art.content_nl, art.content_ru]:
        if not html or not isinstance(html, str):
            continue
        # alt before src
        for m in IMG_PATTERNS[0].finditer(html):
            alt, src = m.group(1).strip(), m.group(2)
            code = re.sub(r'\.png$', '', alt).replace(' ', '_')
            if code and code not in code_to_url:
                code_to_url[code] = src
        # src before alt
        for m in IMG_PATTERNS[1].finditer(html):
            src, alt = m.group(1), m.group(2).strip()
            code = re.sub(r'\.png$', '', alt).replace(' ', '_')
            if code and code not in code_to_url:
                code_to_url[code] = src

# Source C: scraped law JSON files (original data before DB import)
for law_dir in Path('data/laws').iterdir():
    for jf in law_dir.glob('*.json'):
        try:
            raw = json.loads(jf.read_text())
        except Exception:
            continue
        articles = raw if isinstance(raw, list) else raw.get('articles', [])
        for art in articles:
            if not isinstance(art, dict):
                continue
            for field in ('content', 'content_html', 'html', 'body', 'content_md'):
                html = art.get(field, '') or ''
                if not isinstance(html, str):
                    continue
                for m in IMG_PATTERNS[0].finditer(html):
                    alt, src = m.group(1).strip(), m.group(2)
                    code = re.sub(r'\.png$', '', alt).replace(' ', '_')
                    if code and code not in code_to_url:
                        code_to_url[code] = src
                for m in IMG_PATTERNS[1].finditer(html):
                    src, alt = m.group(1), m.group(2).strip()
                    code = re.sub(r'\.png$', '', alt).replace(' ', '_')
                    if code and code not in code_to_url:
                        code_to_url[code] = src

print(f'[all sources]  {len(code_to_url)} code→URL entries total')
print('Codes found:', sorted(code_to_url.keys()))

def download_url(url, dest_path):
    """Download URL to dest_path, return True on success."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; sign-downloader/1.0)'
    })
    with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
        # Check for redirect to SVG thumbnail (may return PNG/SVG bytes)
        data = resp.read()
        if len(data) < 200:
            return False   # probably an error page
        dest_path.write_bytes(data)
    return True


def try_wikimedia(code):
    """Try to download sign image from Wikimedia Commons. Returns dest path or None."""
    if code in WIKI_SKIP:
        return None
    dest = SIGNS_DIR / f'{code}.png'
    if dest.exists():
        return dest
    for pattern in WIKI_PATTERNS:
        url = pattern.format(code=code.replace(' ', '_'))
        try:
            if download_url(url, dest):
                return dest
            # download_url wrote the file but returned False (too small) — remove it
            if dest.exists() and dest.stat().st_size < 200:
                dest.unlink()
        except Exception:
            pass
    return None


# ── Step 2: download missing images ──────────────────────────────────────────

signs_needing_image = TrafficSign.objects.filter(image='')
print(f'\nSigns without image in DB: {signs_needing_image.count()}')

downloaded = 0
no_url = []
errors = []

for sign in signs_needing_image:
    url = code_to_url.get(sign.code)
    dest = SIGNS_DIR / f'{sign.code}.png'

    if not url:
        # Try Wikimedia Commons as fallback
        wiki_dest = try_wikimedia(sign.code)
        if wiki_dest:
            print(f'  ✓ {sign.code:12}  →  wikimedia')
            sign.image = f'signs/{sign.code}.png'
            sign.save(update_fields=['image'])
            downloaded += 1
            time.sleep(0.2)
        else:
            no_url.append(sign.code)
        continue

    if not dest.exists():
        try:
            if download_url(url, dest):
                print(f'  ✓ {sign.code:12}  →  {url.split("/")[-1]}')
                downloaded += 1
                time.sleep(0.3)   # polite delay
            else:
                print(f'  ✗ {sign.code:12}  empty response')
                errors.append(sign.code)
                continue
        except Exception as e:
            print(f'  ✗ {sign.code:12}  ERROR: {e}')
            errors.append(sign.code)
            continue
    else:
        print(f'  ~ {sign.code:12}  already exists locally')

    # Update DB record
    sign.image = f'signs/{sign.code}.png'
    sign.save(update_fields=['image'])

# ── Step 3: also update signs that already have hash-named images ─────────────
# Rename hash files to code-named files for clarity (optional, skip if risky)

print(f'\n─────────────────────────────────')
print(f'Downloaded: {downloaded}')
print(f'No URL found for: {len(no_url)} signs')
if no_url:
    print('  No URL:', sorted(no_url))
if errors:
    print(f'Download errors: {len(errors)}')
    print('  Errors:', sorted(errors))
print(f'Total signs with image: {TrafficSign.objects.exclude(image="").count()}')
