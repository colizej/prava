"""Extract sign code → name mappings from French law text."""
import json, re
from pathlib import Path

d = json.loads(Path('data/laws/1975/fr_reglementation.json').read_text())
arts = d.get('articles', [])

# Find all articles and search for sign image references with labels
# Format in law text: ![CODE](sign:CODE) description
all_sign_refs = {}

for a in arts:
    artnum = a.get('article_number', '')
    title = a.get('title','')
    c = a.get('content_md', '') or ''

    # Find patterns like: ![A1a](sign:A1a) Virage dangereux à droite
    # or: A1a - Virage dangereux
    matches = re.findall(r'!\[([A-Z][A-Za-z0-9_]+)\]\(sign:[A-Z][A-Za-z0-9_]+\)\s+([^\n!]+)', c)
    for code, desc in matches:
        desc = desc.strip().rstrip('.')
        if code not in all_sign_refs:
            all_sign_refs[code] = []
        all_sign_refs[code].append((artnum, desc[:80]))

# Print all found sign code→name pairs
print("=== Signs found in law text ===")
for code in sorted(all_sign_refs.keys()):
    entries = all_sign_refs[code]
    # Take first mention
    artnum, desc = entries[0]
    print(f"  {code:15} | art {artnum:10} | {desc}")

print(f"\nTotal unique codes: {len(all_sign_refs)}")
