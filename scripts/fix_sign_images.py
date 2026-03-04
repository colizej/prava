"""
Build a reliable mapping between Belgian sign codes and Wikimedia filenames.
Downloads all Belgian_road_sign_*.svg and Belgian_traffic_sign_*.svg file lists,
then matches to our DB sign codes, downloads correct images.
"""
import json, re, ssl, time, ssl, urllib.request, shutil
from pathlib import Path
import os, sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from apps.reglementation.models import TrafficSign

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

SIGNS_DIR = Path('media/signs')
WIKI_BASE = 'https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=250'

def fetch_wiki_filelist(prefix):
    """Get all files starting with prefix from Wikimedia allimages API."""
    url = (
        f'https://commons.wikimedia.org/w/api.php'
        f'?action=query&list=allimages&aifrom={prefix}&ailimit=500&format=json'
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-finder/1.0'})
    with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
        data = json.loads(r.read())
    return [img['name'] for img in data.get('query', {}).get('allimages', [])]

def download_file(wiki_filename, dest_path):
    url = WIKI_BASE.format(filename=wiki_filename.replace(' ', '_'))
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-finder/1.0'})
    with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
        data = r.read()
    if len(data) < 500:
        return False
    dest_path.write_bytes(data)
    return True

# --- Fetch all available Belgian road sign files ---
print("Fetching Wikimedia file list...")
all_wiki = set()
for prefix in ['Belgian_road_sign_', 'Belgian_traffic_sign_']:
    files = fetch_wiki_filelist(prefix)
    all_wiki.update(f for f in files if f.lower().endswith('.svg') and
                    (f.startswith('Belgian_road_sign_') or f.startswith('Belgian_traffic_sign_')))
    print(f"  {prefix}: {len(files)} files")

print(f"Total unique SVG files: {len(all_wiki)}")

# Build code→best_filename mapping
# Extract sign code from filename, e.g. Belgian_road_sign_F87.svg → F87
def filename_to_code(fname):
    for prefix in ['Belgian_road_sign_', 'Belgian_traffic_sign_']:
        if fname.startswith(prefix):
            code = fname[len(prefix):].replace('.svg', '')
            return code
    return None

# Index wiki files by their extracted code
wiki_by_code = {}
for fname in sorted(all_wiki):
    code = filename_to_code(fname)
    if code:
        if code not in wiki_by_code:
            wiki_by_code[code] = []
        wiki_by_code[code].append(fname)

print(f"Unique codes in Wikimedia: {len(wiki_by_code)}")

# --- Match our DB signs to Wikimedia codes ---
# Also use reliable hash_to_code signs (skip those - they're already correct from source)
h2c_path = Path('data/sources/codedelaroute.be/hash_to_code.json')
reliable_codes = set(json.loads(h2c_path.read_text()).values()) if h2c_path.exists() else set()
# Also signs from reglementation/ path
reliable_from_regl = set(TrafficSign.objects.filter(image__startswith='reglementation/').values_list('code', flat=True))
reliable_codes.update(reliable_from_regl)

print(f"\nReliable codes (skip): {len(reliable_codes)}")

# Find signs that need re-matching
to_fix = TrafficSign.objects.filter(image__startswith='signs/').exclude(code__in=reliable_codes)
print(f"Signs to re-match: {to_fix.count()}")

# Normalize code for matching (try exact, then case-insensitive, then without suffix)
def find_wiki_match(sign_code):
    code = sign_code.strip()
    # 1. Exact match
    if code in wiki_by_code:
        return wiki_by_code[code][0]
    # 2. Case-insensitive
    for wc, fnames in wiki_by_code.items():
        if wc.lower() == code.lower():
            return fnames[0]
    # 3. Code with zero-padding variants: A2→A02, etc.
    m = re.match(r'^([A-Za-z]+)(\d+)([a-z]?)$', code)
    if m:
        prefix, num, suffix = m.groups()
        padded = f"{prefix}{int(num):02d}{suffix}"
        if padded in wiki_by_code:
            return wiki_by_code[padded][0]
        padded3 = f"{prefix}{int(num):03d}{suffix}"
        if padded3 in wiki_by_code:
            return wiki_by_code[padded3][0]
    return None

# Apply fixes
fixed = 0
no_match = []

for sign in to_fix.order_by('sign_type', 'code'):
    wiki_file = find_wiki_match(sign.code)
    current_file = SIGNS_DIR / f"{sign.code}.png"

    if wiki_file:
        # Download correct image
        try:
            if download_file(wiki_file, current_file):
                sign.image = f'signs/{sign.code}.png'
                sign.save(update_fields=['image'])
                print(f"  ✓ {sign.code:10}  {wiki_file}")
                fixed += 1
                time.sleep(0.5)
            else:
                print(f"  ✗ {sign.code:10}  too small: {wiki_file}")
                no_match.append(sign.code)
        except Exception as e:
            if '429' in str(e):
                print(f"  ⏳ rate limited, waiting 15s...")
                time.sleep(15)
            else:
                print(f"  ! {sign.code:10}  {e}")
            no_match.append(sign.code)
    else:
        print(f"  ? {sign.code:10}  no Wikimedia match [name: {sign.name[:50]}]")
        no_match.append(sign.code)

print(f"\n=== Done: {fixed} fixed, {len(no_match)} no match ===")
if no_match:
    print("No match:", no_match)
