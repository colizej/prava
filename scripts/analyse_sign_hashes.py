"""Analyse media/signs/ directory — map hash filenames to sign codes via article HTML."""
import re
import json
from pathlib import Path

# ── Load original scraped data ─────────────────────────────────────────────
jf = Path('data/sources/codedelaroute.be/code_de_la_route_complet.json')
data = json.loads(jf.read_text())
arts = data.get('articles', [])

hash_to_code = {}    # hash filename → sign code (alt text)
hash_no_alt  = {}    # hash filename → article number (no useful alt)

for art in arts:
    art_num = art.get('article_number') or art.get('number', '?')
    for field in ('content', 'content_html', 'html', 'body'):
        html = art.get(field, '') or ''
        if not isinstance(html, str):
            continue
        for m in re.finditer(r'<img[^>]{0,600}>', html, re.I):
            tag = m.group(0)
            src_m = re.search(r"src=[\"'](/media/image/orig/([\w.\-]+))", tag, re.I)
            alt_m = re.search(r"alt=[\"'](.*?)[\"']", tag, re.I)
            if not src_m:
                continue
            hash_name = src_m.group(2)
            alt = alt_m.group(1).strip() if alt_m else ''
            alt = re.sub(r'\.png$', '', alt, flags=re.I).replace(' ', '_').strip()

            if alt:
                if hash_name not in hash_to_code:
                    hash_to_code[hash_name] = {'code': alt, 'article': art_num}
            else:
                if hash_name not in hash_to_code:
                    hash_no_alt[hash_name] = art_num

# ── Compare with actual files in media/signs/ ─────────────────────────────
signs_dir = Path('media/signs')
all_files = set(f.name for f in signs_dir.iterdir())

print(f'media/signs/ files total:     {len(all_files)}')
print(f'Hashes mapped to sign codes:  {len(hash_to_code)}')
print(f'Hashes with empty alt text:   {len(hash_no_alt)}')
files_in_json = {k for k in hash_to_code} | {k for k in hash_no_alt}
print(f'Files referenced in articles: {len(all_files & files_in_json)}')
print(f'Files NOT referenced at all:  {len(all_files - files_in_json)}')
print()

# ── Show all unique sign codes found ──────────────────────────────────────
unique_codes = sorted(set(v['code'] for v in hash_to_code.values()))
print(f'Unique sign codes with mapping: {len(unique_codes)}')
print(unique_codes)

# ── Save the mapping to JSON for use in import script ─────────────────────
out = {h: v['code'] for h, v in hash_to_code.items()}
Path('data/sources/codedelaroute.be/hash_to_code.json').write_text(
    json.dumps(out, ensure_ascii=False, indent=2)
)
print(f'\nMapping saved to data/sources/codedelaroute.be/hash_to_code.json')
