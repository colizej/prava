#!/usr/bin/env python3
"""
Analyze the HTML structure of the codedelaroute.be regulation page.
Goal: Understand ALL content patterns (text, images, lists, tables,
notifications, examples, etc.) to build a proper scraper.
"""
from bs4 import BeautifulSoup, NavigableString, Tag
from collections import Counter
import re

with open('/tmp/page_raw.html', 'rb') as f:
    soup = BeautifulSoup(f, 'lxml')

main = soup.find('main', class_='site-main')
if not main:
    main = soup.find('main')
    if not main:
        print("No <main> found, trying body")
        main = soup.body

print("=" * 70)
print("STRUCTURAL ANALYSIS OF codedelaroute.be REGULATION PAGE")
print("=" * 70)

# 1. What are the direct children of main?
print("\n### 1. Direct children of <main>:")
child_tags = Counter()
for child in main.children:
    if isinstance(child, Tag):
        cls = ' '.join(child.get('class', []))
        key = f"<{child.name}>" + (f".{cls}" if cls else "")
        child_tags[key] += 1
for tag, count in child_tags.most_common(20):
    print(f"  {count:4d}x {tag}")

# 2. Find the actual content container
print("\n### 2. Looking for content container...")
# Try various possible containers
for selector in ['div.content', 'article', 'div.regulation-content',
                 'div.article-content', 'section', 'div.entry-content',
                 'div.body-content']:
    found = main.select(selector)
    if found:
        print(f"  Found: {selector} ({len(found)} elements)")

# 3. ALL unique tag names in main content
print("\n### 3. ALL tag names used in content area:")
all_tags = Counter()
for tag in main.find_all(True):
    cls = ' '.join(tag.get('class', []))
    key = f"<{tag.name}>" + (f".{cls}" if cls else "")
    all_tags[key] += 1
for key, count in all_tags.most_common(50):
    print(f"  {count:4d}x {key}")

# 4. Heading hierarchy
print("\n### 4. Heading hierarchy (h1-h6):")
for level in range(1, 7):
    headings = main.find_all(f'h{level}')
    if headings:
        print(f"\n  <h{level}> ({len(headings)} total):")
        for h in headings[:5]:
            text = h.get_text(strip=True)[:80]
            cls = ' '.join(h.get('class', []))
            hid = h.get('id', '')
            print(f"    [{cls}] #{hid}: {text}")
        if len(headings) > 5:
            print(f"    ... and {len(headings)-5} more")

# 5. Images analysis
print("\n### 5. Images in content:")
images = main.find_all('img')
print(f"  Total: {len(images)}")
img_patterns = Counter()
for img in images:
    src = img.get('src', '')
    parent_tag = img.parent.name if img.parent else 'none'
    parent_cls = ' '.join(img.parent.get('class', [])) if img.parent and isinstance(img.parent, Tag) else ''
    grandparent = img.parent.parent if img.parent else None
    gp_tag = grandparent.name if grandparent and isinstance(grandparent, Tag) else 'none'
    gp_cls = ' '.join(grandparent.get('class', [])) if grandparent and isinstance(grandparent, Tag) else ''

    # Classify image source type
    if '/media/image/' in src:
        src_type = '/media/image/...'
    elif src.startswith('data:'):
        src_type = 'data:...'
    else:
        src_type = src[:60]

    pattern = f"{src_type} in <{parent_tag}.{parent_cls}> in <{gp_tag}.{gp_cls}>"
    img_patterns[pattern] += 1

for pattern, count in img_patterns.most_common(20):
    print(f"  {count:4d}x {pattern}")

# Show a few actual image srcs
print("\n  Sample image srcs:")
for img in images[:10]:
    print(f"    src={img.get('src', '')[:100]}")

# 6. Find content around Art. 72 (road markings) specifically
print("\n### 6. Art. 72 content analysis:")
art72_heading = None
for h in main.find_all(['h4', 'h5', 'h6']):
    if 'Article 72' in h.get_text():
        art72_heading = h
        break

if art72_heading:
    print(f"  Found: <{art72_heading.name}> {art72_heading.get_text(strip=True)[:80]}")

    # Walk siblings after this heading
    sibling = art72_heading.find_next_sibling()
    elem_count = 0
    while sibling and elem_count < 40:
        if isinstance(sibling, Tag):
            # Stop at next article heading
            if sibling.name in ('h4', 'h5') and 'Article' in sibling.get_text():
                print(f"  --> STOPPED at: <{sibling.name}> {sibling.get_text(strip=True)[:60]}")
                break

            cls = ' '.join(sibling.get('class', []))
            text = sibling.get_text(strip=True)[:100]
            has_img = len(sibling.find_all('img')) if sibling.find_all else 0

            marker = f" [🖼 {has_img} imgs]" if has_img else ""
            print(f"  <{sibling.name}.{cls}>{marker}: {text[:80]}")
            elem_count += 1
        sibling = sibling.find_next_sibling()
    print(f"  Total sibling elements until next article: {elem_count}")
else:
    print("  NOT FOUND")

# 7. Notification/info blocks
print("\n### 7. Notification/info blocks:")
notif_classes = set()
for div in main.find_all('div'):
    classes = div.get('class', [])
    for cls in classes:
        if 'notification' in cls or 'alert' in cls or 'info' in cls or 'note' in cls:
            notif_classes.add(' '.join(classes))
for cls in sorted(notif_classes):
    divs = main.find_all('div', class_=cls.split())
    print(f"  {len(divs):4d}x <div.{cls}>")
    if divs:
        print(f"         Sample: {divs[0].get_text(strip=True)[:100]}")

# 8. Lists (ul, ol)
print("\n### 8. Lists:")
for list_tag in ['ul', 'ol']:
    lists = main.find_all(list_tag)
    print(f"  <{list_tag}>: {len(lists)} total")
    # Show first few with context
    for lst in lists[:3]:
        prev = lst.find_previous_sibling()
        prev_text = prev.get_text(strip=True)[:60] if prev else "none"
        li_count = len(lst.find_all('li'))
        print(f"    after '{prev_text}': {li_count} items")

# 9. Tables
print("\n### 9. Tables:")
tables = main.find_all('table')
print(f"  Total: {len(tables)}")
for t in tables[:3]:
    rows = len(t.find_all('tr'))
    cols = len(t.find_all('th')) + len(t.find_all('td'))
    prev = t.find_previous_sibling()
    context = prev.get_text(strip=True)[:60] if prev else "none"
    print(f"    {rows} rows, after '{context}'")

# 10. Special patterns: p with specific classes
print("\n### 10. Paragraph classes:")
p_classes = Counter()
for p in main.find_all('p'):
    cls = ' '.join(p.get('class', []))
    if cls:
        p_classes[cls] += 1
for cls, count in p_classes.most_common(15):
    print(f"  {count:4d}x <p.{cls}>")

# 11. Check around 72.7 / "Ex." pattern
print("\n### 11. Looking for 'Ex.' / example patterns:")
for tag in main.find_all(True):
    text = tag.get_text(strip=True)
    if text.startswith('Ex.') or text.startswith('Ex :') or text.startswith('Exemp'):
        parent = tag.parent
        p_cls = ' '.join(parent.get('class', [])) if isinstance(parent, Tag) else ''
        print(f"  <{tag.name}> in <{parent.name if isinstance(parent, Tag) else 'none'}.{p_cls}>: {text[:100]}")
