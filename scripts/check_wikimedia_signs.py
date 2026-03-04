#!/usr/bin/env python3
"""Check which Wikimedia filenames return valid images for problematic signs."""
import ssl, urllib.request, urllib.parse, time, hashlib
from pathlib import Path

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Known bad MD5s (these are images that were mistakenly downloaded as duplicates)
BAD_MD5S = {
    'a73a0da299335e04bb9949c6967ca3eb',  # F4a = F43 = F50 (Zone 30 sign)
    '5b055bde23f0e52135c955b1fd01e2bd',  # F4b = F51 (Zone end sign)
}

def fetch(filename):
    url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(filename)}?width=150'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'prava-sign-bot/1.0'})
        with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
            data = r.read()
            md5 = hashlib.md5(data).hexdigest()
            is_bad = md5 in BAD_MD5S
            return len(data), md5, is_bad
    except Exception as e:
        return 0, '', False

# Signs to investigate
candidates = {
    'A7':  ['Belgian_traffic_sign_A7.svg', 'Belgian_traffic_sign_A7a.svg'],
    'A25': ['Belgian_traffic_sign_A25.svg'],
    'A25a': ['Belgian_traffic_sign_A25a.svg'],
    'A25b': ['Belgian_traffic_sign_A25b.svg'],
    'A41': ['Belgian_traffic_sign_A41.svg'],
    'A43': ['Belgian_traffic_sign_A43.svg'],
    'F43': ['Belgian_traffic_sign_F43.svg', 'Belgian_road_sign_F43.svg'],
    'F47': ['Belgian_traffic_sign_F47.svg', 'Belgian_road_sign_F47.svg'],
    'F49': ['Belgian_traffic_sign_F49.svg'],
    'F50': ['Belgian_traffic_sign_F50.svg', 'Belgian_road_sign_F50.svg'],
    'F51': ['Belgian_traffic_sign_F51.svg', 'Belgian_road_sign_F51.svg'],
}

for code, fnames in candidates.items():
    for fname in fnames:
        size, md5, is_bad = fetch(fname)
        status = ' *** BAD (duplicate) ***' if is_bad else (' ✓ OK' if size > 500 else ' ✗ empty')
        print(f'{code:6s} {fname} → {size} bytes {md5[:8]} {status}')
        time.sleep(0.4)
