#!/usr/bin/env python3
"""
Fix sign image/name mismatches:
1. Delete A7 (highway photo, old duplicate of A31)
2. Rename A25a → A25 "Traversée pour cyclistes", delete A25b
3. Re-download F43, F47, F49→F50 images via direct Wikimedia CDN
4. Try to fix F51
"""
import os, sys, ssl, time, hashlib, urllib.request, urllib.parse, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from apps.reglementation.models import TrafficSign

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
SIGNS_DIR = Path('media/signs')

def download_thumb(svg_path_on_wikimedia, filename, dest_path, width=320):
    """
    Download a thumbnail PNG from the Wikimedia CDN using the known SVG file path.
    svg_path_on_wikimedia: e.g. '4/4a/Belgian_traffic_sign_F43.svg'
    Uses 320px as Wikimedia requires standard thumbnail steps (not arbitrary sizes).
    """
    fname = filename  # e.g. 'Belgian_traffic_sign_F43.svg'
    url = f'https://upload.wikimedia.org/wikipedia/commons/thumb/{svg_path_on_wikimedia}/{width}px-{urllib.parse.quote(fname)}.png'
    print(f'  Downloading: {url}')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'prava-sign-bot/1.0'})
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
            data = r.read()
            if len(data) > 500:
                dest_path.write_bytes(data)
                md5 = hashlib.md5(data).hexdigest()
                print(f'  ✓ Saved {len(data)} bytes (md5: {md5[:8]})')
                return True
            else:
                print(f'  ✗ Too small ({len(data)} bytes)')
    except Exception as e:
        print(f'  ✗ Error: {e}')
    return False

# Known Wikimedia CDN paths (from API query: url field)
# Format: filename → (hash_path, svg_filename)
WIKIMEDIA_PATHS = {
    'F43': ('4/4a', 'Belgian_traffic_sign_F43.svg'),
    'F47': ('d/da', 'Belgian_traffic_sign_F47.svg'),
    'F49': ('a/a4', 'Belgian_traffic_sign_F49.svg'),  # Use F49 for F50 (cyclist crossing)
    'F50_new': ('6/6e', 'Belgian_traffic_sign_F50.svg'),  # New F50 (turning danger)
    'F51': None,  # Doesn't exist on Wikimedia
    'A25': ('2/22', 'Belgian_traffic_sign_A25.svg'),
    'A41': ('c/cf', 'Belgian_traffic_sign_A41.svg'),
    'A43': ('f/f9', 'Belgian_traffic_sign_A43.svg'),
    'A31': ('c/c2', 'Belgian_traffic_sign_A31.svg'),
}

print('=== Step 1: Fix A7 (delete - wrong image, duplicate of A31) ===')
a7 = TrafficSign.objects.filter(code='A7').first()
if a7:
    a7_img = Path('media') / str(a7.image) if a7.image else None
    a7.delete()
    print(f'  ✓ Deleted A7 from DB')
    # Remove the wrong JPEG file
    if a7_img and a7_img.exists():
        a7_img.unlink()
        print(f'  ✓ Deleted image file: {a7_img}')
else:
    print('  → A7 not found in DB (already removed)')

print()
print('=== Step 2: Fix A25a → A25 (cyclist crossing), delete A25b ===')
# Delete A25b first
a25b = TrafficSign.objects.filter(code='A25b').first()
if a25b:
    a25b.delete()
    # Remove image file if possible
    img_path = SIGNS_DIR / 'A25b.png'
    if img_path.exists():
        img_path.unlink()
        print(f'  ✓ Deleted A25b image')
    print(f'  ✓ Deleted A25b from DB')
else:
    print('  → A25b not found')

# Check if A25 already exists
a25_exists = TrafficSign.objects.filter(code='A25').exists()
if a25_exists:
    print('  → A25 already exists in DB; fixing A25a')
    a25a = TrafficSign.objects.filter(code='A25a').first()
    if a25a:
        a25a.delete()
        print('  ✓ Deleted A25a from DB (A25 already exists)')
else:
    # Rename A25a to A25
    a25a = TrafficSign.objects.filter(code='A25a').first()
    if a25a:
        # Download fresh A25 cyclist image
        dest = SIGNS_DIR / 'A25.png'
        path, fname = WIKIMEDIA_PATHS['A25']
        if download_thumb(f'{path}/{fname}', fname, dest):
            a25a.code = 'A25'
            a25a.name = 'Traversée pour cyclistes et cyclomoteurs'
            a25a.image = 'signs/A25.png'
            a25a.save()
            # Remove old A25a.png
            old_img = SIGNS_DIR / 'A25a.png'
            if old_img.exists():
                old_img.unlink()
            print(f'  ✓ Renamed A25a → A25 with fresh cyclist image')
        else:
            # Just update name and code without refreshing image
            a25a.code = 'A25'
            a25a.name = 'Traversée pour cyclistes et cyclomoteurs'
            a25a.image = 'signs/A25a.png'
            a25a.save()
            print(f'  ✓ Renamed A25a → A25 (kept old image file A25a.png)')
    else:
        print('  → A25a not found')

print()
print('=== Step 3: Re-download F43 (signal de localité / frontière de commune) ===')
print('  Waiting 5s to avoid rate limiting...')
time.sleep(5)
f43 = TrafficSign.objects.filter(code='F43').first()
if f43:
    dest = SIGNS_DIR / 'F43.png'
    path, fname = WIKIMEDIA_PATHS['F43']
    if download_thumb(f'{path}/{fname}', fname, dest):
        f43.image = 'signs/F43.png'
        f43.save(update_fields=['image'])
        print(f'  ✓ Updated F43 image')
    time.sleep(2)
else:
    print('  → F43 not found in DB')

print()
print('=== Step 4: Re-download F47 (fin de travaux) ===')
f47 = TrafficSign.objects.filter(code='F47').first()
if f47:
    dest = SIGNS_DIR / 'F47.png'
    path, fname = WIKIMEDIA_PATHS['F47']
    if download_thumb(f'{path}/{fname}', fname, dest):
        f47.image = 'signs/F47.png'
        f47.save(update_fields=['image'])
        print(f'  ✓ Updated F47 image')
    time.sleep(2)
else:
    print('  → F47 not found in DB')

print()
print('=== Step 5: Fix F50 (passage pour cyclistes) - download F49/cyclist image ===')
f50 = TrafficSign.objects.filter(code='F50').first()
if f50:
    dest = SIGNS_DIR / 'F50.png'
    # Download F49 (= cyclist crossing in new code) for the "passage pour cyclistes" sign
    path, fname = WIKIMEDIA_PATHS['F49']
    if download_thumb(f'{path}/{fname}', fname, dest):
        f50.image = 'signs/F50.png'
        f50.save(update_fields=['image'])
        print(f'  ✓ Updated F50 image (using F49 SVG = cyclist crossing)')
    time.sleep(2)
else:
    print('  → F50 not found in DB')

print()
print('=== Step 6: Fix F51 (passage souterrain) ===')
# F51 doesn't exist on Wikimedia as Belgian_traffic_sign_F51.svg
# Try alternative approaches
f51 = TrafficSign.objects.filter(code='F51').first()
if f51:
    print(f'  F51 current image: {f51.image}')
    dest = SIGNS_DIR / 'F51.png'
    # Try alternative filenames
    alternatives = [
        ('', 'Belgian_traffic_sign_F51.svg'),  # May have been added since last check
    ]
    # Use Wikimedia API to search
    try:
        api_url = 'https://commons.wikimedia.org/w/api.php?action=query&titles=File:Belgian_traffic_sign_F51.svg&prop=imageinfo&iiprop=url&format=json'
        req = urllib.request.Request(api_url, headers={'User-Agent': 'prava-sign-bot/1.0'})
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
            import json
            data = json.load(r)
            pages = data['query']['pages']
            for k, v in pages.items():
                info = v.get('imageinfo', [{}])
                if info and info[0].get('url'):
                    url = info[0]['url']
                    print(f'  Found F51 at: {url}')
                    # Extract path for thumb
                    # url like https://upload.wikimedia.org/wikipedia/commons/x/xx/filename
                    parts = url.split('commons/')[-1]  # x/xx/filename
                    svgname = parts.split('/')[-1]
                    hash_path = '/'.join(parts.split('/')[:2])
                    download_thumb(f'{hash_path}/{svgname}', svgname, dest)
                else:
                    print('  ✗ F51 still not found on Wikimedia')
    except Exception as e:
        print(f'  Error checking F51: {e}')
else:
    print('  → F51 not found in DB')

print()
print('=== Step 7: Verify A41/A43 have correct images ===')
for code, key in [('A41', 'A41'), ('A43', 'A43')]:
    sign = TrafficSign.objects.filter(code=code).first()
    if sign:
        dest = SIGNS_DIR / f'{code}.png'
        if not dest.exists() or dest.stat().st_size < 1000:
            path, fname = WIKIMEDIA_PATHS[key]
            download_thumb(f'{path}/{fname}', fname, dest)
            sign.image = f'signs/{code}.png'
            sign.save(update_fields=['image'])
            print(f'  ✓ Downloaded {code}')
        else:
            print(f'  {code}: image exists ({dest.stat().st_size} bytes) ✓')
        time.sleep(2)

print()
print('=== Final State ===')
problem_codes = ['A25', 'A31', 'A41', 'A43', 'F43', 'F47', 'F50', 'F51']
for s in TrafficSign.objects.filter(code__in=problem_codes).order_by('code'):
    img_path = Path('media') / str(s.image) if s.image else None
    img_size = img_path.stat().st_size if img_path and img_path.exists() else 0
    print(f'{s.code:6s} | {s.name[:45]:45s} | {s.image} ({img_size}B)')

print()
deleted = ['A7', 'A25a', 'A25b']
remaining = TrafficSign.objects.filter(code__in=deleted).exists()
print(f'Deleted signs still in DB: {remaining}')
