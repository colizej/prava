#!/usr/bin/env python3
"""Deep analysis: container nesting, sibling chains, content patterns."""
from bs4 import BeautifulSoup, Tag
from collections import Counter

with open('/tmp/page_raw.html', 'rb') as f:
    soup = BeautifulSoup(f, 'lxml')

main = soup.find('main', class_='site-main') or soup.find('main') or soup.body

# 1. Find the stickytoc-content container
print("### 1. Content container structure:")
stc = main.find('div', class_='stickytoc-content')
if stc:
    # Trace path from main to stickytoc-content
    node = stc
    path = []
    while node and node != main:
        cls = '.'.join(node.get('class', [])) if isinstance(node, Tag) else ''
        path.append(f"<{node.name}.{cls}>" if isinstance(node, Tag) else str(type(node)))
        node = node.parent
    print(f"  Path: main > {' > '.join(reversed(path))}")

    # Direct children of stickytoc-content
    print(f"\n### 2. Direct children of stickytoc-content:")
    child_tags = Counter()
    for ch in stc.children:
        if isinstance(ch, Tag):
            cls = ' '.join(ch.get('class', []))
            key = f"<{ch.name}>" + (f".{cls}" if cls else "")
            child_tags[key] += 1
    for tag, count in child_tags.most_common(20):
        print(f"  {count:4d}x {tag}")

    # Are h5 elements direct children?
    h5s = stc.find_all('h5', recursive=False)
    h5s_deep = stc.find_all('h5')
    print(f"\n### 3. h5 elements: {len(h5s)} direct children, {len(h5s_deep)} total (nested)")

    h2s = stc.find_all('h2', recursive=False)
    h2s_deep = stc.find_all('h2')
    print(f"  h2 elements: {len(h2s)} direct, {len(h2s_deep)} total")

    h3s = stc.find_all('h3', recursive=False)
    h3s_deep = stc.find_all('h3')
    print(f"  h3 elements: {len(h3s)} direct, {len(h3s_deep)} total")

    # Check: are ALL content elements direct children of stickytoc-content?
    print(f"\n### 4. ALL direct children sequence (first 60):")
    count = 0
    for ch in stc.children:
        if isinstance(ch, Tag):
            cls = ' '.join(ch.get('class', []))
            text = ch.get_text(strip=True)[:60]
            imgs = len(ch.find_all('img'))
            img_mark = f" [🖼{imgs}]" if imgs else ""
            print(f"  {count:3d}. <{ch.name}.{cls}>{img_mark} {text}")
            count += 1
            if count >= 60:
                break

    # 5. Check Art. 72 siblings more carefully
    print(f"\n### 5. Art. 72 full sibling chain:")
    for h5 in stc.find_all('h5', recursive=False):
        if 'Article 72' in h5.get_text():
            idx = 0
            sib = h5.find_next_sibling()
            while sib and isinstance(sib, Tag):
                if sib.name in ('h2', 'h3', 'h5'):
                    print(f"  {idx:3d}. STOP: <{sib.name}> {sib.get_text(strip=True)[:60]}")
                    break
                cls = ' '.join(sib.get('class', []))
                text = sib.get_text(strip=True)
                imgs = len(sib.find_all('img'))
                inner_html = str(sib)[:200]

                if imgs and not text:
                    print(f"  {idx:3d}. <{sib.name}.{cls}> 🖼 IMAGE-ONLY: {inner_html[:150]}")
                elif imgs:
                    print(f"  {idx:3d}. <{sib.name}.{cls}> 🖼+TEXT: {text[:80]}")
                else:
                    print(f"  {idx:3d}. <{sib.name}.{cls}> {text[:80]}")
                idx += 1
                sib = sib.find_next_sibling()
            break

    # 6. Count image-only vs text-containing elements
    print(f"\n### 6. Image-only elements analysis:")
    img_only = 0
    img_with_text = 0
    text_only = 0
    for ch in stc.children:
        if isinstance(ch, Tag) and ch.name not in ('h2', 'h3', 'h5'):
            has_img = bool(ch.find_all('img'))
            has_text = bool(ch.get_text(strip=True))
            if has_img and not has_text:
                img_only += 1
            elif has_img and has_text:
                img_with_text += 1
            elif has_text:
                text_only += 1
    print(f"  Image-only elements (DROPPED by old scraper): {img_only}")
    print(f"  Image + text elements: {img_with_text}")
    print(f"  Text-only elements: {text_only}")

    # Count how many images are in the image-only elements
    lost_imgs = 0
    for ch in stc.children:
        if isinstance(ch, Tag) and ch.name not in ('h2', 'h3', 'h5'):
            has_text = bool(ch.get_text(strip=True))
            if not has_text:
                lost_imgs += len(ch.find_all('img'))
    print(f"  Images LOST in image-only elements: {lost_imgs}")

    # 7. Check table structure for sign images
    print(f"\n### 7. Table analysis:")
    for i, table in enumerate(stc.find_all('table')):
        cls = ' '.join(table.get('class', []))
        rows = table.find_all('tr')
        imgs = len(table.find_all('img'))
        # Find nearest heading before this table
        prev = table
        heading = None
        while prev:
            prev = prev.find_previous_sibling()
            if prev and isinstance(prev, Tag) and prev.name in ('h5', 'h2', 'h3'):
                heading = prev.get_text(strip=True)[:60]
                break
        print(f"  Table {i}: .{cls}, {len(rows)} rows, {imgs} imgs, after '{heading}'")
        # Show first row structure
        if rows:
            first_row = rows[0] if len(rows) == 1 else rows[1]  # skip header
            cells = first_row.find_all(['td', 'th'])
            cell_desc = []
            for cell in cells[:6]:
                c_text = cell.get_text(strip=True)[:30]
                c_imgs = len(cell.find_all('img'))
                cell_desc.append(f"[{c_text}{'🖼' if c_imgs else ''}]")
            print(f"    Row sample: {' | '.join(cell_desc)}")

else:
    print("  stickytoc-content NOT FOUND!")
    # Try other containers
    container = main.find('div', class_='container')
    if container:
        print(f"  Found div.container with {len(list(container.children))} children")
#!/usr/bin/env python3
"""Deep analysis: container nesting, sibling chains, content patterns."""

import os
import json
from bs4 import BeautifulSoup, Tag
from collections import Counter
from copy import deepcopy


TEMPLATE_PATH = 'data/reglementation/_TEMPLATE.json'
OUTPUT_DIR = 'data/reglementation_db/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open('/tmp/page_raw.html', 'rb') as f:
    soup = BeautifulSoup(f, 'lxml')

with open(TEMPLATE_PATH, 'r', encoding='utf-8') as tf:
    BASE_TEMPLATE = json.load(tf)


main = soup.find('main', class_='site-main') or soup.find('main') or soup.body


# --- UNIVERSAL ARTICLE EXTRACTION ---
stc = main.find('div', class_='stickytoc-content')
if not stc:
    raise RuntimeError('stickytoc-content not found!')

articles = []
current = None
for elem in stc.children:
    if isinstance(elem, Tag) and elem.name == 'h5' and 'Article' in elem.get_text():
        # Start new article
        if current:
            articles.append(current)
        current = {
            'header': elem,
            'content_blocks': []
        }
    elif current and isinstance(elem, Tag):
        current['content_blocks'].append(elem)
if current:
    articles.append(current)

print(f"Found {len(articles)} articles.")

def extract_article_data(article, idx):
    # --- Extract article number and title ---
    h = article['header']
    header_text = h.get_text(strip=True)
    # e.g. 'Article 2. Définitions'
    import re
    m = re.match(r'Article\s*(\d+[\w\.]*)\s*[\.:-]?\s*(.*)', header_text)
    article_number = m.group(1) if m else f"{idx+1}"
    title = m.group(2).strip() if m and m.group(2) else header_text
    slug = f"art{article_number.replace('.', '_').replace(' ', '_').lower()}"

    # --- Extract content HTML and text ---
    html_blocks = [str(b) for b in article['content_blocks']]
    content_html = '\n'.join(html_blocks)
    content_text = ' '.join(b.get_text(strip=True) for b in article['content_blocks'])

    # --- Build JSON dict from template ---
    data = deepcopy(BASE_TEMPLATE)
    data['article_number'] = f"Art. {article_number}"
    data['title'] = title
    data['content_html'] = content_html
    data['content_text'] = content_text
    data['slug'] = slug
    data['parsed_at'] = __import__('datetime').datetime.now().isoformat()
    # Optionally: extract images, definitions, etc. here
    # ...
    return data

# --- Output each article as JSON ---
for idx, art in enumerate(articles):
    data = extract_article_data(art, idx)
    fname = f"{data['article_number'].replace(' ', '_').replace('.', '')}_{data['slug']}.json"
    out_path = os.path.join(OUTPUT_DIR, fname)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved: {out_path}")
