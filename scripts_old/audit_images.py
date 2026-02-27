#!/usr/bin/env python3
"""
Find all articles where sign labels/descriptions exist without corresponding images.
These are places where the original had <img> tags that were either:
1. Not scraped (missing from scraped data)
2. Present in scraped data as codedelaroute.be remote URLs but not downloaded
"""
import os, sys, django, re, json
os.chdir('/Users/colizej/Documents/webApp/prava')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle

# Load scraped data to compare
with open('data/sites/codedelaroute.be/output/code_de_la_route_complet.json') as f:
    scraped = json.load(f)

scraped_map = {}
for art in scraped['articles']:
    num = art.get('number', '').rstrip('.')
    if num == '22no': num = '22novies'
    elif num == '22un': num = '22undecies'
    elif num == '22' and 'decies' in art.get('title', '').lower(): num = '22decies'
    scraped_map[f"Art. {num}"] = art

print("=" * 80)
print("SEARCHING FOR ARTICLES WITH MISSING IMAGES")
print("=" * 80)

# Pattern 1: remote img tags pointing to codedelaroute.be that were NOT downloaded
remote_img_pattern = re.compile(r'<img[^>]+src=["\']https?://www\.codedelaroute\.be[^"\']+["\'][^>]*>', re.IGNORECASE)

# Pattern 2: local img tags
local_img_pattern = re.compile(r'<img[^>]+src=["\']/(media|static)[^"\']+["\'][^>]*>', re.IGNORECASE)

# Pattern 3: Sign labels without nearby images (e.g. "Commencement d'une agglomération." in italics)
# after sign-code references or section text without image

issues = []

for db_art in CodeArticle.objects.all().order_by('category__order', 'order'):
    content = db_art.content or ''
    key = db_art.article_number

    # Check for any remote codedelaroute.be img URLs still in content
    remote_imgs = remote_img_pattern.findall(content)
    local_imgs = local_img_pattern.findall(content)

    # Get scraped version to compare img count
    scraped_art = scraped_map.get(key)
    scraped_html = scraped_art.get('html', '') if scraped_art else ''
    scraped_imgs = re.findall(r'<img[^>]+>', scraped_html, re.IGNORECASE) if scraped_html else []

    # Count local media/signs imgs in our content
    our_sign_imgs = re.findall(r'src=["\']/?media/signs/[^"\']+["\']', content)
    our_all_imgs = re.findall(r'<img[^>]+>', content)

    # Compare: scraped has images we don't have locally
    scraped_img_count = len(scraped_imgs)
    our_img_count = len(our_all_imgs)

    if remote_imgs:
        issues.append({
            'key': key,
            'type': 'REMOTE_IMG_STILL_PRESENT',
            'detail': f'{len(remote_imgs)} remote codedelaroute.be img tags still in content',
            'examples': [re.search(r'src=["\']([^"\']+)["\']', r).group(1) for r in remote_imgs[:3]]
        })

    if scraped_img_count > 0 and our_img_count < scraped_img_count:
        missing = scraped_img_count - our_img_count
        issues.append({
            'key': key,
            'type': 'FEWER_IMGS_THAN_SCRAPED',
            'detail': f'Scraped had {scraped_img_count} imgs, we have {our_img_count}',
            'missing': missing
        })

print(f"\nTotal issues found: {len(issues)}")
print()

# Group and display
remote_issues = [i for i in issues if i['type'] == 'REMOTE_IMG_STILL_PRESENT']
count_issues = [i for i in issues if i['type'] == 'FEWER_IMGS_THAN_SCRAPED']

print(f"=== REMOTE IMG TAGS STILL IN CONTENT ({len(remote_issues)}) ===")
for issue in remote_issues:
    print(f"\n  {issue['key']}: {issue['detail']}")
    for ex in issue['examples']:
        print(f"    {ex}")

print(f"\n=== FEWER IMGS THAN SCRAPED ({len(count_issues)}) ===")
for issue in count_issues:
    print(f"  {issue['key']}: {issue['detail']}")

# Now specifically look at articles where scraped has ZERO imgs but we know they had some
# (scraped html is empty but our DB has content with img references to specific signs)
print("\n\n=== ARTICLES WITH SCRAPED HTML = 0 (img analysis impossible) ===")
for key in ['Art. 11', 'Art. 35', 'Art. 45bis', 'Art. 57', 'Art. 78']:
    db_art = CodeArticle.objects.get(article_number=key)
    imgs = re.findall(r'<img[^>]+>', db_art.content or '')
    sign_texts = re.findall(r'(?:le signal|les signaux|signal|signaux)\s+([A-Z]\d+[a-z]?(?:\s+et\s+[A-Z]\d+[a-z]?)*)',
                             db_art.content or '')
    # Check for sign gallery
    galleries = db_art.content.count('sign-gallery') if db_art.content else 0
    print(f"\n  {key}: {len(imgs)} imgs, {galleries} galleries")
    if imgs:
        for img in imgs[:5]:
            src = re.search(r'src=["\']([^"\']+)["\']', img)
            print(f"    img: {src.group(1) if src else 'N/A'}")

# Check article 85 specifically - what does scraped have?
print("\n\n=== ART. 85 SCRAPED DATA ===")
s85 = scraped_map.get('Art. 85')
if s85:
    html = s85.get('html', '')
    imgs_in_scraped = re.findall(r'<img[^>]+>', html)
    print(f"Scraped HTML length: {len(html)}")
    print(f"Scraped img tags: {len(imgs_in_scraped)}")
    for img in imgs_in_scraped[:10]:
        src = re.search(r'src=["\']([^"\']+)["\']', img)
        alt = re.search(r'alt=["\']([^"\']*)["\']', img)
        print(f"  src: {src.group(1) if src else 'N/A'}, alt: {alt.group(1) if alt else 'N/A'}")

    # Find 85.2 section
    idx = html.find('85.2')
    if idx >= 0:
        print(f"\n85.2 section in scraped:")
        print(html[max(0,idx-50):idx+1000])
