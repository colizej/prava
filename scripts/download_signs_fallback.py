"""
Try alternative Wikimedia filenames for signs that didn't match 'Belgian road sign X.svg'.
"""
import os
import re
import sys
import ssl
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.reglementation.models import TrafficSign

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

SIGNS_DIR = Path('media/signs')


def try_url(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-finder/1.0'})
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
        data = r.read()
        if len(data) < 200:
            return False
        dest.write_bytes(data)
        return True


# Alternative URL patterns to try (in order)
PATTERNS = [
    'https://commons.wikimedia.org/wiki/Special:FilePath/Belgian_road_sign_{code}.svg?width=150',
    'https://commons.wikimedia.org/wiki/Special:FilePath/Belgian_traffic_sign_{code}.svg?width=150',
    'https://commons.wikimedia.org/wiki/Special:FilePath/Belgian_road_sign_{code_lower}.svg?width=150',
    'https://commons.wikimedia.org/wiki/Special:FilePath/Belgium_road_sign_{code}.svg?width=150',
    'https://commons.wikimedia.org/wiki/Special:FilePath/Belgium_traffic_sign_{code}.svg?width=150',
]

signs_without_image = TrafficSign.objects.filter(image='')
print(f'Signs without image: {signs_without_image.count()}')

downloaded = 0
still_missing = []

for sign in signs_without_image:
    code = sign.code
    dest = SIGNS_DIR / f'{code}.png'
    found = False

    subs = {
        'code': code.replace(' ', '_'),
        'code_lower': code.lower().replace(' ', '_'),
    }

    for pattern in PATTERNS:
        url = pattern.format(**subs)
        try:
            if try_url(url, dest):
                sign.image = f'signs/{code}.png'
                sign.save(update_fields=['image'])
                print(f'  ✓ {code:15}  {url.rsplit("/", 1)[-1][:50]}')
                downloaded += 1
                found = True
                time.sleep(1.5)   # longer delay to avoid 429
                break
        except Exception as e:
            if '429' in str(e):
                print(f'  ⏳ {code:15}  rate limited, waiting 10s...')
                time.sleep(10)
            if dest.exists() and dest.stat().st_size < 200:
                dest.unlink()

    if not found:
        still_missing.append(code)

print(f'\nDownloaded: {downloaded}')
print(f'Still missing: {len(still_missing)}')
print('Missing:', sorted(still_missing))
print(f'Total with image: {TrafficSign.objects.exclude(image="").count()}/{TrafficSign.objects.count()}')
