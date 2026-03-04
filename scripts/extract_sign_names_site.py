"""
Extract sign code → French name mapping from code_de_la_route_complet.json.
Signs appear as: <img alt="A1a"> followed by their description text.
"""
import json, re
from pathlib import Path
from bs4 import BeautifulSoup

src = Path('data/sources/codedelaroute.be/code_de_la_route_complet.json')
data = json.loads(src.read_text())

sign_names = {}

for article in data.get('articles', []):
    html = article.get('content_html', '') or ''
    if not html:
        continue

    soup = BeautifulSoup(html, 'html.parser')

    # Find all images with sign codes as alt text
    for img in soup.find_all('img'):
        alt = (img.get('alt') or '').strip()
        if not alt or not re.match(r'^[A-Z][A-Za-z0-9]+$', alt):
            continue

        # Get the text that follows this image (within same parent or next sibling)
        # Try parent's full text context
        parent = img.parent
        if parent:
            # Get text after the img tag
            full_text = parent.get_text(separator=' ')
            # Look for the sign code followed by description
            # Pattern: "A1a Virage dangereux à droite"
            m = re.search(rf'\b{re.escape(alt)}\b\s+([^.!?\n]{{5,80}})', full_text)
            if m:
                desc = m.group(1).strip()
                if alt not in sign_names:
                    sign_names[alt] = desc
                continue

        # Also try: look at next text nodes
        for sib in img.next_siblings:
            text = sib.get_text().strip() if hasattr(sib, 'get_text') else str(sib).strip()
            if text and len(text) > 3:
                sign_names[alt] = text[:80]
                break

# Also search raw text patterns: "A1a – Virage dangereux" or "A1a : Virage"
for article in data.get('articles', []):
    html = article.get('content_html', '') or ''
    text = BeautifulSoup(html, 'html.parser').get_text(separator='\n') if html else ''

    # Pattern: code followed by dash/colon and description
    for m in re.finditer(r'\b([A-Z][A-Za-z0-9]{1,5})\s*[–\-:]\s*([A-ZÉÀÈÎÔÙÜ][^.\n]{5,80})', text):
        code, desc = m.group(1), m.group(2).strip()
        if code not in sign_names:
            sign_names[code] = desc

print(f"Found {len(sign_names)} sign names\n")

# Filter to only sign-like codes (A, B, C, D, E, F, M series)
sign_like = {k: v for k, v in sign_names.items()
             if re.match(r'^[ABCDEFM][A-Z0-9]', k)}

print("=== Sign code → French name (from codedelaroute.be) ===")
for code in sorted(sign_like.keys()):
    print(f"  {code:12} {sign_like[code]}")
