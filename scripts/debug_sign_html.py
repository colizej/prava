"""
Look at the raw HTML structure around sign images in codedelaroute.be source.
"""
import json, re
from pathlib import Path

src = Path('data/sources/codedelaroute.be/code_de_la_route_complet.json')
data = json.loads(src.read_text())

# Find articles that contain sign images with alt codes
for article in data.get('articles', []):
    art_id = article.get('id', '') or article.get('url', '')
    html = article.get('content_html', article.get('html', '')) or ''
    if not html:
        continue

    # Look for img tags with alt text matching sign codes
    imgs = re.findall(r'<img[^>]*>', html)
    for img_tag in imgs[:3]:
        alt_m = re.search(r'alt=["\']([^"\']+)["\']', img_tag)
        if alt_m:
            alt = alt_m.group(1)
            if re.match(r'^[A-Z]\d', alt):
                # Found a sign code - show context around it
                idx = html.find(img_tag)
                context = html[max(0,idx-100):idx+200]
                print(f"Article: {art_id}")
                print(f"Alt: {alt}")
                print(f"Context: {context[:300]}")
                print("---")
                break
    else:
        continue
    break

print("\n=== Article keys ===")
if data.get('articles'):
    print(list(data['articles'][0].keys()))
