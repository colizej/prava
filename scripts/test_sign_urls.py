"""Find actual Wikimedia Commons file names for Belgian road signs."""
import ssl
import json
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-finder/1.0'})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return r.read()


# Check API response for A1a
api = 'https://commons.wikimedia.org/w/api.php?action=query&titles=File:Belgium_road_sign_A1a.svg&prop=imageinfo&iiprop=url&format=json'
data = json.loads(fetch(api))
print('API result for Belgium_road_sign_A1a.svg:')
print(json.dumps(data, indent=2)[:600])

# Try category search
api2 = 'https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Road_signs_in_Belgium&cmlimit=20&cmtype=file&format=json'
data2 = json.loads(fetch(api2))
print('\nCategory members (first 20 files):')
# Search Wikimedia Commons for Belgian road sign files
api3 = 'https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=Belgian+road+sign+A1a&srnamespace=6&srlimit=10&format=json'
data3 = json.loads(fetch(api3))
print('\nSearch results for "Belgian road sign A1a":')
for r in data3.get('query', {}).get('search', []):
    print(' ', r.get('title'))

# Try the Belgian traffic signs category specifically
api4 = 'https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Traffic_signs_in_Belgium&cmlimit=30&cmtype=file&format=json'
data4 = json.loads(fetch(api4))
print('\nCategory Traffic_signs_in_Belgium (first 30 files):')
for m in data4.get('query', {}).get('categorymembers', []):
    print(' ', m.get('title'))
