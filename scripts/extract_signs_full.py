#!/usr/bin/env python3
"""Extract all road signs from signaux.pdf.

Uses pymupdf table detection to get exact cell boundaries.
Layout: 3 columns — [NL description] | [sign image + code] | [FR description]
Each sign = 2 PDF rows: row 0 has code text, row 1 has image (empty text).
A25-style: image row may be at i+2 if NL/FR text spills into i+1 center=None.
Output: PNG per sign in data/signs/, signs_index.json
"""
import re
import json
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

PDF_PATH = Path(__file__).parent.parent / "signaux.pdf"
OUT_DIR  = Path(__file__).parent.parent / "data" / "signs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Code must be the entire content of the center cell (no surrounding text)
CODE_RE = re.compile(r'\b([A-Z]{1,2}\d+[a-z]?(?:-[A-Z]\.\d+)?)\b')

doc  = pymupdf.open(str(PDF_PATH))
signs = []
seen  = set()
mat   = pymupdf.Matrix(3, 3)  # 3× zoom ≈ 216 DPI

for page_num in range(len(doc)):
    page = doc[page_num]
    tabs = page.find_tables()
    if not tabs.tables:
        continue

    table = tabs.tables[0]
    rows  = list(table.rows)
    page_count = 0

    i = 0
    while i < len(rows):
        cells = rows[i].cells
        if len(cells) < 3 or cells[1] is None:
            i += 1
            continue

        nl_cell, center_cell, fr_cell = cells[0], cells[1], cells[2]

        # A valid code row has ONLY a code in the center cell
        center_text = page.get_textbox(pymupdf.Rect(center_cell)).strip()
        match = CODE_RE.fullmatch(center_text.rstrip("."))
        if not match:
            i += 1
            continue
        code = match.group(1)

        if code in seen:
            i += 1
            continue

        # NL / FR span the full sign height from this row onwards
        desc_nl = page.get_textbox(pymupdf.Rect(nl_cell)).strip().replace("\n", " ") if nl_cell else ""
        desc_fr = page.get_textbox(pymupdf.Rect(fr_cell)).strip().replace("\n", " ") if fr_cell else ""

        # Scan forward for the image row: first center cell with empty text
        img_center = None
        for j in range(i + 1, min(i + 5, len(rows))):
            jcells = rows[j].cells
            if len(jcells) < 2 or jcells[1] is None:
                continue
            jtext = page.get_textbox(pymupdf.Rect(jcells[1])).strip()
            if not jtext:
                img_center = jcells[1]
                break

        clip_rect = pymupdf.Rect(img_center) if img_center else pymupdf.Rect(center_cell)
        pix = page.get_pixmap(matrix=mat, clip=clip_rect)
        i += 2  # advance past code row + image row

        img_path = OUT_DIR / f"{code}.png"
        pix.save(str(img_path))

        # Replace near-gray background (216,217,216) with white via flood-fill
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        for corner in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
            ImageDraw.floodfill(img, corner, (255, 255, 255), thresh=12)
        img.save(str(img_path))

        seen.add(code)
        signs.append({"code": code, "page": page_num + 1, "name_nl": desc_nl, "name_fr": desc_fr})
        page_count += 1
        print(f"  {code}: NL={desc_nl[:50]!r}")

    if page_count:
        print(f"Page {page_num + 1}: {page_count} signs")

index_path = OUT_DIR / "signs_index.json"
index_path.write_text(json.dumps(signs, indent=2, ensure_ascii=False))
print(f"\nTotal: {len(signs)} signs → {OUT_DIR}")
print(f"Index → {index_path}")
import re
import json
from pathlib import Path

import pymupdf
from PIL import Image

PDF_PATH = Path(__file__).parent.parent / "signaux.pdf"
OUT_DIR  = Path(__file__).parent.parent / "data" / "signs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Strict match: A7a, B1, C22, M33-P.2, M41a-P.1, F34b. — entire cell text
CODE_RE = re.compile(r'^([A-Z]{1,2}\d+[a-z]?(?:-[A-Z]\.\d+)?)\.?\s*$')

# Column x-ranges (stable across every page)
NL_X0, NL_X1 = 58, 191
FR_X0, FR_X1 = 405, 538

MAT = pymupdf.Matrix(3, 3)   # 3× zoom ≈ 216 DPI
TARGET = 400                  # output square size (px)


def remove_gray_bg(img: Image.Image) -> Image.Image:
    """Replace near-gray (page background) pixels with white.

    The PDF background is (216, 217, 216).  Sign content colours are
    saturated (red, blue, black) so the near-equal-channels test is safe.
    """
    img = img.convert("RGB")
    data = img.getdata()
    new = [
        (255, 255, 255)
        if abs(r - g) < 20 and abs(g - b) < 20 and abs(r - b) < 20 and r > 200
        else (r, g, b)
        for r, g, b in data
    ]
    img.putdata(new)
    return img


def auto_crop_square(img: Image.Image, padding: float = 0.07) -> Image.Image:
    """Tight-crop to sign content, add padding, center on white square."""
    gray = img.convert("L")
    # Any pixel < 240 counts as content
    inv  = gray.point(lambda x: 255 if x < 240 else 0)
    bbox = inv.getbbox()
    if bbox:
        x0, y0, x1, y1 = bbox
        pw = max(6, int((x1 - x0) * padding))
        ph = max(6, int((y1 - y0) * padding))
        img = img.crop((
            max(0, x0 - pw), max(0, y0 - ph),
            min(img.width, x1 + pw), min(img.height, y1 + ph),
        ))
    img.thumbnail((TARGET, TARGET), Image.LANCZOS)
    square = Image.new("RGB", (TARGET, TARGET), (255, 255, 255))
    square.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
    return square


doc  = pymupdf.open(str(PDF_PATH))
signs = []
seen  = set()

for page_num in range(len(doc)):
    page = doc[page_num]
    tabs = page.find_tables()
    if not tabs.tables:
        continue
    rows = list(tabs.tables[0].rows)

    # ── 1. Locate every code-label row on this page ───────────────────────
    sign_positions: list[tuple[int, str, tuple]] = []
    for i, row in enumerate(rows):
        cells = row.cells
        if len(cells) < 2 or cells[1] is None:
            continue
        text = page.get_textbox(pymupdf.Rect(cells[1])).strip()
        m = CODE_RE.match(text)
        if m:
            sign_positions.append((i, m.group(1), cells[1]))

    if not sign_positions:
        continue

    page_count = 0

    for k, (i, code, center_cell) in enumerate(sign_positions):
        if code in seen:
            continue

        # ── 2. Full NL / FR text for this sign (whole y-range) ───────────
        sign_y0 = center_cell[1]
        sign_y1 = (sign_positions[k + 1][2][1]
                   if k + 1 < len(sign_positions)
                   else page.rect.height)

        desc_nl = (page
                   .get_textbox(pymupdf.Rect(NL_X0, sign_y0, NL_X1, sign_y1))
                   .strip().replace("\n", " "))
        desc_fr = (page
                   .get_textbox(pymupdf.Rect(FR_X0, sign_y0, FR_X1, sign_y1))
                   .strip().replace("\n", " "))

        # ── 3. Find the image clip rect ───────────────────────────────────
        next_i      = (sign_positions[k + 1][0]
                       if k + 1 < len(sign_positions) else len(rows))
        image_rect  = None

        # Look forward for an empty-text center cell = image row (new format)
        for j in range(i + 1, next_i):
            cells_j = rows[j].cells
            if len(cells_j) < 2 or cells_j[1] is None:
                continue
            if not page.get_textbox(pymupdf.Rect(cells_j[1])).strip():
                image_rect = pymupdf.Rect(cells_j[1])
                break

        if image_rect is None:
            # Old format: code label sits at the top of a tall center cell.
            # Strip label area using its exact text bounding box.
            words = page.get_text("words", clip=pymupdf.Rect(center_cell))
            if words:
                label_bottom = max(w[3] for w in words)
                gap = (center_cell[3] - center_cell[1]) * 0.04
                candidate = pymupdf.Rect(
                    center_cell[0], label_bottom + gap,
                    center_cell[2], center_cell[3],
                )
                # Only use if there's enough room for an actual image (> 20pt)
                if candidate.height > 20:
                    image_rect = candidate
                else:
                    image_rect = pymupdf.Rect(center_cell)
            else:
                image_rect = pymupdf.Rect(center_cell)

        # ── 4. Render, clean, uniform-size, save ─────────────────────────
        pix      = page.get_pixmap(matrix=MAT, clip=image_rect)
        img_path = OUT_DIR / f"{code}.png"
        pix.save(str(img_path))

        img = Image.open(img_path)
        img = remove_gray_bg(img)
        img = auto_crop_square(img)
        img.save(str(img_path))

        seen.add(code)
        signs.append({
            "code":    code,
            "page":    page_num + 1,
            "name_nl": desc_nl,
            "name_fr": desc_fr,
        })
        page_count += 1
        print(f"  {code}: {desc_nl[:50]!r}")

    if page_count:
        print(f"Page {page_num + 1}: {page_count} signs")

index_path = OUT_DIR / "signs_index.json"
index_path.write_text(json.dumps(signs, indent=2, ensure_ascii=False))
print(f"\nTotal: {len(signs)} signs → {OUT_DIR}")
print(f"Index → {index_path}")
