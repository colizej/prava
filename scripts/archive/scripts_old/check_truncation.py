#!/usr/bin/env python3
"""Quick check of current scraped JSON content for truncation issues."""
import json

with open('data/sites/codedelaroute.be/output/code_de_la_route_complet.json', encoding='utf-8') as f:
    data = json.load(f)

# Check Art. 82 html to see truncation
for art in data['articles']:
    if art['number'] == '82':
        html = art['html']
        print('Art. 82 HTML length:', len(html))
        print()
        print('LAST 300 chars:')
        print(html[-300:])
        print()
        if '<ul' in html:
            print('Contains <ul>: YES')
        else:
            print('Contains <ul>: NO')
        break

print()
print('=== Articles likely truncated (missing ul/div content) ===')
for art in data['articles']:
    html = art['html']
    # Check if article ends mid-sentence (with : at the end)
    text_end = html.rstrip().rstrip('</p>').rstrip()
    if text_end.endswith(':'):
        print(art['number'] + ': ends with ":" -> likely truncated. Last 100: ...' + html[-100:].replace('\n', ' '))
