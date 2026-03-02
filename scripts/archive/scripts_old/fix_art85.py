#!/usr/bin/env python3
"""
Fix Art. 85.2 - add F1 and F3 sign images that are missing.
The old F1/F3 sign images are already in the DB (used in Art. 2.12).
"""
import django
import os
import re
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle

# Step 1: Find F1 and F3 image local paths from Art. 2
art2 = CodeArticle.objects.get(article_number='Art. 2')
content2 = art2.content

imgs = re.findall(r'<img[^>]+>', content2)
f1_src = None
f3_src = None

for img in imgs:
    alt_m = re.search(r'alt="([^"]+)"', img)
    src_m = re.search(r'src="([^"]+)"', img)
    if alt_m and src_m:
        alt = alt_m.group(1)
        src = src_m.group(1)
        if alt == 'F1' and f1_src is None:
            f1_src = src
            print(f"Found F1: src={src!r}")
        elif alt == 'F3' and f3_src is None:
            f3_src = src
            print(f"Found F3: src={src!r}")

if not f1_src or not f3_src:
    print("ERROR: Could not find F1 or F3 images in Art. 2!")
    print("All alts found:", [re.search(r'alt="([^"]+)"', i).group(1) for i in imgs if re.search(r'alt="([^"]+)"', i)])
    sys.exit(1)

# Step 2: Look at current Art. 85 content around section 85.2
art85 = CodeArticle.objects.get(article_number='Art. 85')
content85 = art85.content

# Find the 85.2 section
idx_852 = content85.find('85.2.')
if idx_852 == -1:
    print("ERROR: Could not find 85.2 in Art. 85!")
    sys.exit(1)

print("\nCurrent Art. 85.2 section (200 chars):")
print(repr(content85[idx_852:idx_852+400]))

# Step 3: Fix - add F1 image before "Commencement" caption, and F3 before "Fin" caption
# Pattern: <p style="padding-left: 30px;"><em>Commencement d'une agglomération.</em></p>
# Replace with: <p style="..."><img src="{f1_src}" alt="F1"> <em>Commencement...</em></p>

new_content = content85

# Add F1 before "Commencement d'une agglomération"
old_comm = '<p style="padding-left: 30px;"><em>Commencement d\'une agglomération.</em></p>'
new_comm = '<p style="padding-left: 30px;"><img src="{src}" alt="F1" class="sign-img"> <em>Commencement d\'une agglomération.</em></p>'.format(src=f1_src)

if old_comm in new_content:
    new_content = new_content.replace(old_comm, new_comm, 1)
    print("\nReplaced Commencement caption with image")
else:
    # Try to find it with different spacing/quotes
    m = re.search(r'<p[^>]*padding-left[^>]*>\s*<em>Commencement d.une agglom', new_content)
    if m:
        print(f"Found but different format at pos {m.start()}: {new_content[m.start():m.start()+120]!r}")
    else:
        print("ERROR: Could not find Commencement caption pattern!")

# Add F3 before "Fin d'agglomération"
old_fin = '<p style="padding-left: 30px;"><em>Fin d\'agglomération.<br/></em></p>'
new_fin = '<p style="padding-left: 30px;"><img src="{src}" alt="F3" class="sign-img"> <em>Fin d\'agglomération.</em></p>'.format(src=f3_src)

if old_fin in new_content:
    new_content = new_content.replace(old_fin, new_fin, 1)
    print("Replaced Fin caption with image")
else:
    # Try without <br/>
    old_fin2 = '<p style="padding-left: 30px;"><em>Fin d\'agglomération.</em></p>'
    if old_fin2 in new_content:
        new_fin2 = '<p style="padding-left: 30px;"><img src="{src}" alt="F3" class="sign-img"> <em>Fin d\'agglomération.</em></p>'.format(src=f3_src)
        new_content = new_content.replace(old_fin2, new_fin2, 1)
        print("Replaced Fin caption (no <br/>) with image")
    else:
        m = re.search(r'<p[^>]*padding-left[^>]*>\s*<em>Fin d.agglom', new_content)
        if m:
            print(f"Found but different format at pos {m.start()}: {new_content[m.start():m.start()+120]!r}")
        else:
            print("ERROR: Could not find Fin caption pattern!")

if new_content != content85:
    art85.content = new_content
    art85.save()
    print("\nArt. 85 saved successfully!")

    # Verify
    art85_reloaded = CodeArticle.objects.get(article_number='Art. 85')
    idx = art85_reloaded.content.find('85.2.')
    print("New 85.2 section:")
    print(repr(art85_reloaded.content[idx:idx+500]))
else:
    print("\nNo changes made - patterns may not have matched")
    # Debug: show actual patterns
    m1 = re.search(r'<p[^>]*>.*?Commencement.*?</p>', new_content, re.DOTALL)
    m2 = re.search(r'<p[^>]*>.*?Fin d.agglom.*?</p>', new_content, re.DOTALL)
    if m1:
        print("Actual Commencement tag:", repr(m1.group()))
    if m2:
        print("Actual Fin tag:", repr(m2.group()))
