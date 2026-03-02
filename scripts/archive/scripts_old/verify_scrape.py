#!/usr/bin/env python3
"""Quick verify: count images per article in the new scraped JSON."""
import json, re

with open('data/sites/codedelaroute.be/output/code_de_la_route_complet.json') as f:
    data = json.load(f)

print(f"Total articles: {len(data['articles'])}")
total_imgs = 0
for art in data['articles']:
    html = art['html']
    img_count = html.count('<img')
    total_imgs += img_count
    has_table = '<table' in html
    has_list = '<ul>' in html or '<ol>' in html
    has_notif = 'notification' in html
    markers = []
    if img_count: markers.append(f"🖼{img_count}")
    if has_table: markers.append("📊tbl")
    if has_list: markers.append("📝list")
    if has_notif: markers.append("ℹ️notif")
    if markers:
        print(f"  Art. {art['number']}: {' '.join(markers)}  len={len(html)}")

print(f"\nTotal images across all articles: {total_imgs}")
