#!/usr/bin/env python3
"""Test extraction of road signs from signaux.pdf — pages 3-6 only.

Uses pymupdf table detection to get exact cell boundaries.
Layout: 3 columns — [NL description] | [sign image + code] | [FR description]
"""
import re
import json
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

PDF_PATH = Path(__file__).parent.parent / "signaux.pdf"
OUT_DIR = Path(__file__).parent.parent / "data" / "signs_test"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CODE_RE = re.compile(r'\b([A-Z]{1,2}\d+[a-z]?)\b')

doc = pymupdf.open(str(PDF_PATH))
signs = []
mat = pymupdf.Matrix(3, 3)  # 3x zoom ≈ 216 DPI

# Test on pages 3-6 (index 2-5)
for page_num in range(2, 6):
    page = doc[page_num]
    tabs = page.find_tables()
    if not tabs.tables:
        print(f"Page {page_num + 1}: no table found, skipping")
        continue

    table = tabs.tables[0]
    print(f"=== Page {page_num + 1}: {table.row_count} rows ===")

    rows = list(table.rows)
    i = 0
    while i < len(rows):
        cells = rows[i].cells
        if len(cells) < 3 or cells[1] is None:
            i += 1
            continue

        nl_cell, center_cell, fr_cell = cells[0], cells[1], cells[2]

        # Extract code from center cell text (the header sub-row)
        center_text = page.get_textbox(pymupdf.Rect(center_cell)).strip()
        match = CODE_RE.search(center_text)
        if not match:
            i += 1
            continue
        code = match.group(1)

        # Extract text from NL and FR cells (they span the full sign height)
        nl_rect = pymupdf.Rect(nl_cell) if nl_cell else None
        fr_rect = pymupdf.Rect(fr_cell) if fr_cell else None
        desc_nl = page.get_textbox(nl_rect).strip().replace("\n", " ") if nl_rect else ""
        desc_fr = page.get_textbox(fr_rect).strip().replace("\n", " ") if fr_rect else ""

        # The NEXT row holds the image (center only, NL/FR are None/merged)
        if i + 1 < len(rows):
            img_cells = rows[i + 1].cells
            img_center = img_cells[1] if len(img_cells) > 1 else None
        else:
            img_center = None

        # Clip = image sub-row if available, else full combined extent
        if img_center:
            clip_rect = pymupdf.Rect(img_center)
        else:
            clip_rect = pymupdf.Rect(center_cell)

        clip = page.get_pixmap(matrix=mat, clip=clip_rect)
        i += 2  # advance past both sub-rows
        img_path = OUT_DIR / f"{code}.png"
        clip.save(str(img_path))

        # Replace gray background (216,217,216) with white using flood-fill from all 4 corners
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        bg_color = (216, 217, 216)
        white = (255, 255, 255)
        for corner in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
            ImageDraw.floodfill(img, corner, white, thresh=10)
        img.save(str(img_path))

        entry = {"code": code, "page": page_num + 1, "name_nl": desc_nl, "name_fr": desc_fr}
        signs.append(entry)
        print(f"  {code}: NL={desc_nl!r}  FR={desc_fr!r}")

index_path = OUT_DIR / "test_index.json"
index_path.write_text(json.dumps(signs, indent=2, ensure_ascii=False))
print(f"\nExtracted {len(signs)} signs → {OUT_DIR}")
print(f"JSON index → {index_path}")
