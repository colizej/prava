"""Search Wikimedia Commons API for exact filenames of missing Belgian signs."""
import os, sys, ssl, json, time, re, urllib.request, urllib.parse
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


def search_wikimedia(code):
    """Return first matching Wikimedia file title that looks like a Belgian sign."""
    query = f'Belgian road sign {code}'
    api = ('https://commons.wikimedia.org/w/api.php?action=query&list=search'
           f'&srsearch={urllib.parse.quote(query)}&srnamespace=6&srlimit=5&format=json')
    data = json.loads(fetch(api))
    results = data.get('query', {}).get('search', [])
    for r in results:
        title = r.get('title', '')
        # Accept if code appears in the filename
        if re.search(re.escape(code), title, re.I):
            return title.replace('File:', '').replace(' ', '_')
    return None


def download_from_title(title, dest):
    url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{title}?width=150'
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-finder/1.0'})
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
        data = r.read()
        if len(data) < 200:
            return False
        dest.write_bytes(data)
        return True


missing = list(TrafficSign.objects.filter(image=''))
print(f'Searching Wikimedia for {len(missing)} missing signs...\n')

found = []
not_found = []

for sign in missing:
    code = sign.code
    dest = SIGNS_DIR / f'{code}.png'
    title = search_wikimedia(code)
    time.sleep(0.3)

    if not title:
        not_found.append(code)
        print(f'  ✗ {code:15}  not found')
        continue

    try:
        if download_from_title(title, dest):
            sign.image = f'signs/{code}.png'
            sign.save(update_fields=['image'])
            print(f'  ✓ {code:15}  {title[:60]}')
            found.append(code)
        else:
            not_found.append(code)
            print(f'  ~ {code:15}  found but empty: {title}')
    except Exception as e:
        not_found.append(code)
        print(f'  ✗ {code:15}  DL error: {e}')
    time.sleep(0.3)

print(f'\n─────────────────────────────────────')
print(f'Found via search: {len(found)}')
print(f'Still missing:    {len(not_found)}  → {sorted(not_found)}')
print(f'Total with image: {TrafficSign.objects.exclude(image="").count()}/{TrafficSign.objects.count()}')
