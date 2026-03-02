#!/usr/bin/env python3
"""
Fix Art. 85.2 - download F1 and F3 (old agglomeration signs) from codedelaroute.be
and add them as inline images in the article content.
"""
import django
import os
import sys
import re
import hashlib
import urllib.request

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle, ArticleImage
from django.conf import settings

MEDIA_ROOT = settings.MEDIA_ROOT
SIGNS_DIR = os.path.join(MEDIA_ROOT, 'signs')
os.makedirs(SIGNS_DIR, exist_ok=True)

# These URLs come from Art. 2.12 on codedelaroute.be (old F1/F3 sign models)
SIGN_URLS = {
    'F1': 'https://www.codedelaroute.be/media/image/orig/e758aef1c502442f82e3f8f64ee6896d1929fb7e.gif',
    'F3': 'https://www.codedelaroute.be/media/image/orig/a810e6756432cb60a8d3fe542093613019a9de3d.gif',
}

local_paths = {}

print("=== Downloading F1 and F3 sign images ===")
for code, url in SIGN_URLS.items():
    # Extract hash from URL for consistent naming
    url_hash = url.split('/')[-1].split('.')[0]
    ext = url.split('.')[-1]
    filename = url_hash + '.' + ext
    local_file = os.path.join(SIGNS_DIR, filename)
    web_path = '/media/signs/' + filename

    if os.path.exists(local_file):
        print(code + ": already exists at " + local_file)
        local_paths[code] = web_path
    else:
        print(code + ": downloading from " + url)
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Referer': 'https://www.codedelaroute.be/'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            with open(local_file, 'wb') as f:
                f.write(data)
            print(code + ": saved " + str(len(data)) + " bytes to " + local_file)
            local_paths[code] = web_path
        except Exception as e:
            print(code + ": DOWNLOAD FAILED: " + str(e))

print()
print("=== Local paths ===")
for code, path in local_paths.items():
    print(code + ": " + path)

if len(local_paths) < 2:
    print("ERROR: Not all images downloaded successfully!")
    sys.exit(1)

# Now update Art. 85.2 content
print()
print("=== Updating Art. 85 content ===")
art85 = CodeArticle.objects.get(article_number='Art. 85')
content = art85.content

# Show current 85.2
idx = content.find('85.2.')
print("Current 85.2 section:")
print(content[idx:idx+500])
print()

# Build the replacement HTML for the sign entries in 85.2
# Pattern 1: Commencement d'une agglomération (F1)
old_comm = '<p style="padding-left: 30px;"><em>Commencement d\'une agglomération.</em></p>'
new_comm = (
    '<p style="padding-left: 30px;">'
    '<img alt="F1" loading="lazy" src="' + local_paths['F1'] + '" class="sign-img d-inline-block" style="max-height:60px; margin-right:8px;"/>'
    ' <em>Commencement d\'une agglomération.</em>'
    '</p>'
)

# Pattern 2: Fin d'agglomération (F3) — has <br/> inside <em>
# Try both with and without <br/>
old_fin_br = '<p style="padding-left: 30px;"><em>Fin d\'agglomération.<br/></em></p>'
old_fin = '<p style="padding-left: 30px;"><em>Fin d\'agglomération.</em></p>'
new_fin = (
    '<p style="padding-left: 30px;">'
    '<img alt="F3" loading="lazy" src="' + local_paths['F3'] + '" class="sign-img d-inline-block" style="max-height:60px; margin-right:8px;"/>'
    ' <em>Fin d\'agglomération.</em>'
    '</p>'
)

new_content = content
changed = False

if old_comm in new_content:
    new_content = new_content.replace(old_comm, new_comm, 1)
    print("OK: Replaced Commencement caption with F1 image")
    changed = True
else:
    print("WARNING: Could not find Commencement pattern")
    print("Looking for:", repr(old_comm))

if old_fin_br in new_content:
    new_content = new_content.replace(old_fin_br, new_fin, 1)
    print("OK: Replaced Fin caption (with br) with F3 image")
    changed = True
elif old_fin in new_content:
    new_content = new_content.replace(old_fin, new_fin, 1)
    print("OK: Replaced Fin caption (no br) with F3 image")
    changed = True
else:
    print("WARNING: Could not find Fin pattern")
    print("Looking for:", repr(old_fin_br))

if changed:
    art85.content = new_content
    art85.save()
    print()
    print("Art. 85 saved!")
    # Verify
    art85_v = CodeArticle.objects.get(article_number='Art. 85')
    idx = art85_v.content.find('85.2.')
    print("New 85.2 section:")
    print(art85_v.content[idx:idx+700])
else:
    print()
    print("No changes made.")
