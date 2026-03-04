"""
Fetch all Belgian road sign files from Wikimedia Commons with descriptions.
Helps build a reliable code→filename mapping.
"""
import json, re, ssl, urllib.request
from pathlib import Path

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def api_get(params):
    base = "https://commons.wikimedia.org/w/api.php"
    p = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
    url = base + "?" + p
    req = urllib.request.Request(url, headers={"User-Agent": "sign-finder/1.0"})
    with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
        return json.loads(r.read())

all_files = {}
params = {
    "action": "query",
    "generator": "categorymembers",
    "gcmtitle": "Category:Belgian road signs",
    "gcmtype": "file",
    "gcmlimit": "500",
    "gcmnamespace": "6",
    "prop": "imageinfo",
    "iiprop": "url|extmetadata",
    "iiextmetadatafilter": "ImageDescription",
    "format": "json",
}

while True:
    data = api_get(params)
    pages = data.get("query", {}).get("pages", {})
    for p in pages.values():
        title = p.get("title", "").replace("File:", "")
        ii = p.get("imageinfo", [{}])[0]
        desc = ii.get("extmetadata", {}).get("ImageDescription", {}).get("value", "")
        desc = re.sub("<[^>]+>", "", desc).strip()
        url = ii.get("url", "")
        all_files[title] = {"desc": desc, "url": url}

    cont = data.get("continue", {})
    if not cont:
        break
    params.update(cont)
    print(f"  fetched {len(all_files)} so far...")

# Save
out = Path("data/sources/codedelaroute.be/wikimedia_catalog.json")
out.write_text(json.dumps(all_files, ensure_ascii=False, indent=2))
print(f"\nSaved {len(all_files)} files to {out}")

# Print sorted for inspection
print("\n=== Belgian road sign files ===")
for name in sorted(all_files):
    if "Belgian" in name or "Belgium" in name:
        desc = all_files[name]["desc"][:80]
        print(f"  {name:70} {desc}")
