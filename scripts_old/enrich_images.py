#!/usr/bin/env python3
"""
Enrich regulation JSON files with image references from scraped data.
Also re-scrape empty/short articles from codedelaroute.be.
"""
import json
import os
import re
import glob

IMAGES_DIR = "data/sites/codedelaroute.be/output/images"
REGL_DIR = "data/reglementation"
MAPPING_FILE = os.path.join(IMAGES_DIR, "image_mapping.json")
ANALYSIS_FILE = "data/sites/codedelaroute.be/output/images_analysis.json"


def normalize_art_num(number_str):
    """Normalize article number: 'Art. 22bis' -> '22bis', '3.' -> '3'"""
    s = str(number_str).strip()
    s = re.sub(r'^Art\.?\s*', '', s)
    s = s.rstrip('.')
    return s


def build_article_images_map():
    """Build mapping: article_number -> list of image filenames."""
    art_images = {}

    # From image filenames (artXX_*.png)
    for png in sorted(glob.glob(os.path.join(IMAGES_DIR, "art*.png"))):
        fname = os.path.basename(png)
        m = re.match(r'art(\w+?)_(.+)\.png', fname)
        if m:
            art_num = m.group(1)
            art_images.setdefault(art_num, []).append(fname)

    # Also use analysis JSON for sign codes
    sign_info = {}
    if os.path.exists(ANALYSIS_FILE):
        with open(ANALYSIS_FILE, encoding="utf-8") as f:
            analysis = json.load(f)
        for img in analysis.get("images", []):
            fname_match = None
            # Find corresponding local file
            src_hash = os.path.basename(img["src"])
            if os.path.exists(MAPPING_FILE):
                with open(MAPPING_FILE, encoding="utf-8") as f:
                    mapping = json.load(f)
                if src_hash in mapping:
                    fname_match = mapping[src_hash]["new_filename"]
            if fname_match:
                sign_info[fname_match] = {
                    "alt": img.get("alt", ""),
                    "sign_code": img.get("alt", ""),
                }

    return art_images, sign_info


def enrich_json_file(json_path, art_images, sign_info):
    """Add images field to each article in a JSON file."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for article in data["articles"]:
        art_num = normalize_art_num(article["article_number"])

        # Find matching images
        images = []
        if art_num in art_images:
            for fname in art_images[art_num]:
                img_entry = {
                    "filename": fname,
                    "path": f"/media/reglementation/{fname}",
                }
                if fname in sign_info:
                    img_entry["alt"] = sign_info[fname].get("alt", "")
                    img_entry["sign_code"] = sign_info[fname].get("sign_code", "")
                else:
                    img_entry["alt"] = fname.replace(".png", "").replace("_", " ")
                    img_entry["sign_code"] = ""
                images.append(img_entry)

        article["images"] = images
        if images:
            updated += 1

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


def main():
    art_images, sign_info = build_article_images_map()
    print(f"Found images for {len(art_images)} articles")
    print(f"Sign info for {len(sign_info)} images")

    json_files = sorted(glob.glob(os.path.join(REGL_DIR, "*.json")))
    for jf in json_files:
        count = enrich_json_file(jf, art_images, sign_info)
        print(f"  ✅ {os.path.basename(jf)}: {count} articles enriched with images")


if __name__ == "__main__":
    main()
