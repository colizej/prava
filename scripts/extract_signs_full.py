#!/usr/bin/env python3
"""Extract all road signs from signaux.pdf — clean version.

PDF structure: 3-column table per page — [NL desc] | [sign + code] | [FR desc]
Two layout variants:
  TYPE A (pages 3-5, 7 etc.): code in small row (h<25pt), image in next row (h≈75pt)
  TYPE B (pages 6, 8 etc.): code+image in one tall cell (h>25pt)

Key techniques:
- Inset clip rect by 2pt to avoid table border lines
- Gray background removed via numpy threshold (equal-channel pixels with r>100)
- Auto-trim dark horizontal border lines at top/bottom of rendered images
"""
import re
import json
from pathlib import Path

import pymupdf
from PIL import Image
import numpy as np

PDF_PATH = Path(__file__).parent.parent / "signaux.pdf"
OUT_DIR  = Path(__file__).parent.parent / "data" / "signs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CODE_RE = re.compile(r'^([A-Z]{1,2}\d+[a-z]?(?:-[A-Z]\.\d+)?)\.?\s*$')
INSET   = 2    # points to shrink clip rect (avoids table borders)
ZOOM    = 3    # 3× = 216 DPI
MAT     = pymupdf.Matrix(ZOOM, ZOOM)


def inset_rect(r):
    """Shrink a Rect by INSET points on each side to avoid table borders."""
    return pymupdf.Rect(r.x0 + INSET, r.y0 + INSET, r.x1 - INSET, r.y1 - INSET)


def clean_background(img_path):
    """Replace gray PDF background (216,217,216) with white using numpy.

    Any pixel where all RGB channels are close together (diff < 15)
    and brightness > 100 is turned white. This catches:
    - Page background (216,217,216)
    - Table borders (127,128,127) and (178,179,178)
    Sign content (red, blue, black, yellow) has divergent channels so is safe.
    """
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    mask = (
        (np.abs(r.astype(int) - g.astype(int)) < 15) &
        (np.abs(g.astype(int) - b.astype(int)) < 15) &
        (np.abs(r.astype(int) - b.astype(int)) < 15) &
        (r > 100)
    )
    arr[mask] = [255, 255, 255]

    # Auto-trim dark border rows at top and bottom.
    # Table borders render as solid dark horizontal lines (>30% dark pixels).
    h, w = arr.shape[:2]
    top = 0
    while top < h - 1:
        row = arr[top, :, :]
        dark = np.sum(np.all(row < 80, axis=1))
        if dark > w * 0.3:
            top += 1
        else:
            break
    bot = h - 1
    while bot > top:
        row = arr[bot, :, :]
        dark = np.sum(np.all(row < 80, axis=1))
        if dark > w * 0.3:
            bot -= 1
        else:
            break
    if top > 0 or bot < h - 1:
        arr = arr[top:bot + 1, :, :]

    Image.fromarray(arr).save(str(img_path))


doc   = pymupdf.open(str(PDF_PATH))
signs = []
seen  = set()

for page_num in range(len(doc)):
    page = doc[page_num]
    tabs = page.find_tables()
    if not tabs.tables:
        continue

    rows = list(tabs.tables[0].rows)
    page_count = 0

    i = 0
    while i < len(rows):
        cells = rows[i].cells
        if len(cells) < 3 or cells[1] is None:
            i += 1
            continue

        center_cell = cells[1]
        center_text = page.get_textbox(pymupdf.Rect(center_cell)).strip()
        match = CODE_RE.match(center_text)
        if not match:
            i += 1
            continue

        code = match.group(1)
        if code in seen:
            i += 1
            continue

        nl_cell, fr_cell = cells[0], cells[2]
        r_center = pymupdf.Rect(center_cell)

        # --- Determine layout type and find image clip rect ---
        # TYPE A: small code row (h<25pt) followed by adjacent image row with empty text
        #         (or text matching the same code — some signs render their own code).
        # TYPE B: tall cell (h>25pt) containing both code and image.
        img_rect = None
        is_two_row = False
        if r_center.height < 25:
            scan_end = min(i + 5, len(rows))
            for j in range(i + 1, scan_end):
                jcells = rows[j].cells
                if len(jcells) < 2 or jcells[1] is None:
                    continue
                jr = pymupdf.Rect(jcells[1])
                if abs(jr.y0 - r_center.y1) > 5:
                    break  # too far away — not adjacent
                jtext = page.get_textbox(jr).strip()
                if not jtext or CODE_RE.match(jtext) and jtext.strip().rstrip('.') == code:
                    img_rect = jr
                    is_two_row = True
                    break

        if img_rect is None:
            # TYPE B: code + image in single tall cell — strip code text area
            # Need extra gap (4pt) to skip the internal horizontal grid line
            words = page.get_text("words", clip=r_center)
            if words:
                label_bottom = max(w[3] for w in words)
                candidate = pymupdf.Rect(
                    r_center.x0, label_bottom + 4,
                    r_center.x1, r_center.y1,
                )
                if candidate.height > 20:
                    img_rect = candidate
                else:
                    img_rect = r_center
            else:
                img_rect = r_center

        # --- NL / FR descriptions (from code row cells, which span full height) ---
        desc_nl = page.get_textbox(pymupdf.Rect(nl_cell)).strip().replace("\n", " ") if nl_cell else ""
        desc_fr = page.get_textbox(pymupdf.Rect(fr_cell)).strip().replace("\n", " ") if fr_cell else ""

        # --- Render with inset to avoid table borders ---
        clip = inset_rect(img_rect)
        pix = page.get_pixmap(matrix=MAT, clip=clip)

        img_path = OUT_DIR / f"{code}.png"
        pix.save(str(img_path))
        clean_background(img_path)

        seen.add(code)
        signs.append({"code": code, "page": page_num + 1, "name_nl": desc_nl, "name_fr": desc_fr})
        page_count += 1
        print(f"  {code}: {desc_fr[:60]!r}")

        i += 2 if is_two_row else 1  # TYPE A: skip code+image rows; TYPE B: just code row

    if page_count:
        print(f"Page {page_num + 1}: {page_count} signs")

index_path = OUT_DIR / "signs_index.json"
index_path.write_text(json.dumps(signs, indent=2, ensure_ascii=False))
print(f"\nTotal: {len(signs)} signs -> {OUT_DIR}")
print(f"Index -> {index_path}")
