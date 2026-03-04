"""Check Wikimedia descriptions for Belgian sign files."""
import json, ssl, urllib.request, re

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

codes_to_check = ['F43','F59','F61','F79','F83','F85','F87','F89','F91',
                  'C21','C27','C33','B3','B17','A2','A7','M1','M2','E1','E3']

titles = '|'.join(f'File:Belgian_road_sign_{c}.svg' for c in codes_to_check)
url = (f'https://commons.wikimedia.org/w/api.php'
       f'?action=query&titles={titles}'
       f'&prop=revisions&rvprop=content&rvslots=main&format=json')
req = urllib.request.Request(url, headers={'User-Agent': 'sign-checker/1.0'})
with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
    d = json.loads(r.read())

results = {}
for pid, p in d['query']['pages'].items():
    title = p['title'].replace('File:Belgian_road_sign_', '').replace('.svg', '')
    content = p.get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('*', '')
    if not content:
        results[title] = 'NOT FOUND'
        continue
    # Try to extract description
    m = re.search(r'\|description\s*=\s*(.+?)(?:\n\||\Z)', content, re.IGNORECASE | re.DOTALL)
    if m:
        desc = re.sub(r'\s+', ' ', m.group(1)).strip()[:150]
    else:
        desc = content[:150].replace('\n', ' ').strip()
    results[title] = desc

for code in codes_to_check:
    print(f'{code:8}  {results.get(code, "??")}')
