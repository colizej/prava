"""Manual Wikimedia search for the last 9 missing signs."""
import os, sys, ssl, json, time, urllib.request, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from apps.reglementation.models import TrafficSign

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
SIGNS_DIR = Path('media/signs')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-finder/1.0'})
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
        return r.read()

def download(url, dest):
    data = fetch(url)
    if len(data) < 200:
        return False
    dest.write_bytes(data)
    return True

# Direct Wikimedia file title overrides for hard-to-find signs
MANUAL_TITLES = {
    # D17 — newer sign with KB-AR date suffix
    'D17':  'Belgian_traffic_sign_D17_KB-AR_03-06-2024.svg',
    # F23 — no standalone parking SVG, use the generic F45 parking sign
    'F23':  'Belgian_road_sign_F45.svg',
}

missing_signs = TrafficSign.objects.filter(image='')
print(f'Missing: {missing_signs.count()}')

for sign in missing_signs:
    code = sign.code
    title = MANUAL_TITLES.get(code, f'Belgian_road_sign_{code}.svg')
    url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{title}?width=150'
    dest = SIGNS_DIR / f'{code}.png'
    try:
        if download(url, dest):
            sign.image = f'signs/{code}.png'
            sign.save(update_fields=['image'])
            print(f'  ✓ {code:15}  {title}')
        else:
            print(f'  ~ {code:15}  empty')
    except Exception as e:
        print(f'  ✗ {code:15}  {e}')
    time.sleep(2)

print(f'\nFinal: {TrafficSign.objects.exclude(image="").count()}/{TrafficSign.objects.count()} signs with image')
