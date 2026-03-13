#!/usr/bin/env python3
"""Verify sign image quality: check for border lines, gray residue, empty images."""
from pathlib import Path
from PIL import Image
import numpy as np

SIGNS_DIR = Path(__file__).parent.parent / 'data' / 'signs'

issues = []
for png in sorted(SIGNS_DIR.glob('*.png')):
    img = Image.open(png).convert('RGB')
    arr = np.array(img)
    w, h = img.size

    # Check if image is essentially blank (all white)
    non_white = np.sum(np.any(arr < 240, axis=2))
    total = w * h
    pct = non_white / total * 100
    if pct < 2:
        issues.append(f'EMPTY: {png.name} ({pct:.1f}% content)')
        continue

    # Check for table border artifact at top/bottom (edge-to-edge dark lines).
    # Sign-content borders are centered with white margins on both sides.
    edge = 10
    for label, y in [('top', 0), ('bottom', h-1)]:
        row = arr[y, :, :]  # shape (w, 3)
        dark = np.sum(np.all(row < 100, axis=1))
        left_dark = np.any(np.all(row[:edge] < 80, axis=1))
        right_dark = np.any(np.all(row[w-edge:] < 80, axis=1))
        if dark > w * 0.3 and left_dark and right_dark:
            issues.append(f'BORDER: {png.name} {label} row has {dark}/{w} dark pixels (edge-to-edge)')

    # Check for gray residue (pixels in 120-230 range with equal channels)
    r, g, b = arr[:,:,0].astype(int), arr[:,:,1].astype(int), arr[:,:,2].astype(int)
    gray_mask = (
        (np.abs(r - g) < 10) & (np.abs(g - b) < 10) &
        (r > 120) & (r < 230)
    )
    gray_pct = np.sum(gray_mask) / total * 100
    if gray_pct > 5:
        issues.append(f'GRAY: {png.name} has {gray_pct:.1f}% gray pixels')

total_files = len(list(SIGNS_DIR.glob('*.png')))
print(f'Checked {total_files} images')
if issues:
    print(f'\n{len(issues)} issues found:')
    for i in issues:
        print(f'  {i}')
else:
    print('All images clean!')
