#!/usr/bin/env python3
"""Audit content completeness of regulation JSON files."""
import json
import os
import sys

def audit_file(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    articles = data["articles"]
    print(f"\n{'='*60}")
    print(f"FILE: {path}")
    print(f"Theme: {data['theme']['name']}")
    print(f"Total articles: {data['articles_count']}")
    print(f"{'='*60}")

    empty = []
    short = []
    for art in articles:
        html = art.get("content_html", "")
        text = art.get("content_text", "")
        if not html and not text:
            empty.append(art["article_number"])
        elif len(text) < 50:
            short.append((art["article_number"], art["title"][:50], len(text), text[:80]))

    print(f"\nEmpty articles (no content): {len(empty)}")
    for a in empty:
        print(f"  X {a}")

    print(f"\nShort articles (<50 chars): {len(short)}")
    for num, title, length, preview in short:
        print(f"  ! {num} ({length} chars): {preview}")

    # Check for cut-off indicators
    print(f"\nSuspicious endings (possible cut-offs):")
    suspicious = 0
    for art in articles:
        text = art.get("content_text", "")
        if text and not text.rstrip().endswith((".", ":", ";", ")", "\u00bb", '"', "!")):
            last_line = text.rstrip().split("\n")[-1][-80:]
            print(f"  ! {art['article_number']}: ...{last_line}")
            suspicious += 1
    print(f"  Total suspicious: {suspicious}")

    # Content length stats
    lengths = [len(art.get("content_html", "")) for art in articles]
    print(f"\nHTML length stats:")
    print(f"  Min: {min(lengths)} chars")
    print(f"  Max: {max(lengths)} chars")
    print(f"  Avg: {sum(lengths)//len(lengths)} chars")
    print(f"  Articles > 500 chars: {sum(1 for l in lengths if l > 500)}")
    print(f"  Articles < 100 chars: {sum(1 for l in lengths if l < 100)}")

    # Show a few sample articles to inspect quality
    print(f"\n--- Sample articles (first 3) ---")
    for art in articles[:3]:
        print(f"\n  {art['article_number']} | {art['title']}")
        html = art.get("content_html", "")
        print(f"  HTML length: {len(html)}")
        print(f"  First 200 chars: {html[:200]}")


if __name__ == "__main__":
    files = sorted(f for f in os.listdir("data/reglementation") if f.endswith(".json"))
    for f in files:
        audit_file(os.path.join("data/reglementation", f))
