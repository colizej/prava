#!/usr/bin/env python3
"""Download images for signs that have no image in the DB."""
import os, sys, ssl, time, urllib.request, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from apps.reglementation.models import TrafficSign

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
SIGNS_DIR = Path('media/signs')
SIGNS_DIR.mkdir(parents=True, exist_ok=True)

def try_download(filename, dest):
    url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(filename)}?width=150'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'prava-sign-bot/1.0'})
        with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
            data = r.read()
            if len(data) > 500:
                dest.write_bytes(data)
                return True
    except Exception as e:
        print(f"    err: {e}")
    return False

# Explicit fallback filenames for hard-to-find signs
MANUAL = {
    'F59': ['Belgian_traffic_sign_F59.svg', 'Belgian_road_sign_F59.svg'],
    'F61': ['Belgian_traffic_sign_F61.svg', 'Belgian_road_sign_F61.svg'],
    'F79': ['Belgian_traffic_sign_F79.svg', 'Belgian_road_sign_F79.svg',
            'Belgian_traffic_sign_F79_KB-AR_03-06-2024.svg'],
    'F89': ['Belgian_traffic_sign_F89.svg', 'Belgian_road_sign_F89.svg'],
    'F91': ['Belgian_traffic_sign_F91.svg', 'Belgian_road_sign_F91.svg'],
}

missing = list(TrafficSign.objects.filter(image='').order_by('code'))
print(f"Signs without image: {len(missing)}")

for sign in missing:
    code = sign.code
    dest = SIGNS_DIR / f'{code}.png'
    filenames = MANUAL.get(code, [
        f'Belgian_traffic_sign_{code}.svg',
        f'Belgian_road_sign_{code}.svg',
    ])
    found = False
    for fname in filenames:
        print(f"  {code}: trying {fname}")
        if try_download(fname, dest):
            sign.image = f'signs/{code}.png'
            sign.save(update_fields=['image'])
            print(f"  ✓ {code} → signs/{code}.png ({dest.stat().st_size} bytes)")
            found = True
            break
        time.sleep(0.5)
    if not found:
        print(f"  ✗ {code} — not found on Wikimedia")
    time.sleep(0.3)

remaining = TrafficSign.objects.filter(image='').count()
print(f"\nDone. Still missing: {remaining}")
