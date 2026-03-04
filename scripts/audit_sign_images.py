"""
Check which Belgian_traffic_sign_*.svg files exist on Wikimedia Commons.
Compare to our sign codes and determine which images to re-download.
"""
import json, ssl, time, urllib.request, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from apps.reglementation.models import TrafficSign

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def api(params):
    url = 'https://commons.wikimedia.org/w/api.php?' + '&'.join(f'{k}={urllib.request.quote(str(v))}' for k,v in params.items())
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-fix/1.0'})
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        return json.loads(r.read())

def download(fname, dest):
    url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{fname}?width=250'
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-fix/1.0'})
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        data = r.read()
    if len(data) < 500:
        return False
    dest.write_bytes(data)
    return True

# 1. Get all available Belgian_traffic_sign_*.svg files
print("Fetching Belgian_traffic_sign_* list...")
traffic_files = {}
data = api({'action': 'query', 'list': 'allimages', 'aifrom': 'Belgian_traffic_sign_', 'ailimit': '500', 'format': 'json'})
for img in data.get('query', {}).get('allimages', []):
    name = img['name']
    if name.startswith('Belgian_traffic_sign_') and name.endswith('.svg'):
        code = name.replace('Belgian_traffic_sign_','').replace('.svg','')
        traffic_files[code] = name

print(f"Found {len(traffic_files)} Belgian_traffic_sign_*.svg files")

# 2. Get reliable codes (from hash_to_code + reglementation/ path)
h2c_path = Path('data/sources/codedelaroute.be/hash_to_code.json')
reliable = set(json.loads(h2c_path.read_text()).values())
reliable.update(TrafficSign.objects.filter(image__startswith='reglementation/').values_list('code', flat=True))

# 3. Check each Wikimedia sign code against our DB
print("\n=== Signs to potentially update (traffic_sign variant available) ===")
signs_dir = Path('media/signs')
updated = 0

# Signs from Wikimedia that might be wrong
from_wiki = TrafficSign.objects.filter(image__startswith='signs/').exclude(code__in=reliable)
print(f"\nTotal potentially wrong: {from_wiki.count()}")

# Only re-download if traffic_sign variant exists (it tends to be newer)
to_update = []
for sign in from_wiki.order_by('code'):
    if sign.code in traffic_files:
        to_update.append((sign, traffic_files[sign.code]))
        print(f"  CAN UPDATE: {sign.code:10} → {traffic_files[sign.code]}")
    else:
        print(f"  NO ALT:     {sign.code:10} [{sign.sign_type}] {sign.name[:40]}")

print(f"\n{len(to_update)} signs can be updated from traffic_sign variant")
print("\nTo actually download, run with --download flag")

if '--download' in sys.argv:
    print("\nDownloading...")
    for sign, wiki_file in to_update:
        dest = signs_dir / f'{sign.code}.png'
        try:
            if download(wiki_file, dest):
                sign.image = f'signs/{sign.code}.png'
                sign.save(update_fields=['image'])
                print(f"  ✓ {sign.code:10} {wiki_file}")
                updated += 1
            else:
                print(f"  ✗ {sign.code:10} too small")
            time.sleep(1.0)
        except Exception as e:
            print(f"  ! {sign.code:10} {e}")
            if '429' in str(e):
                time.sleep(15)
    print(f"\nUpdated {updated}/{len(to_update)} signs")
