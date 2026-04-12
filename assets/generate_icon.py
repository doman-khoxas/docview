#!/usr/bin/env python3
"""Generate DocView icon as .ico and .png at multiple sizes.

Run once: python assets/generate_icon.py
Outputs:  assets/icon.ico, assets/icon_256.png, assets/icon_48.png
"""
from PIL import Image, ImageDraw
import os

ACCENT = (0, 122, 204)       # #007acc
ACCENT_DARK = (0, 90, 158)   # #005a9e
WHITE = (255, 255, 255)

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def draw_icon(size: int) -> Image.Image:
    """Draw the DocView icon at a given pixel size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(1, size // 16)
    r = max(2, size // 8)

    # Outer rounded rect — accent blue
    draw.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=r,
        fill=ACCENT,
    )

    # Inner document shape — white rectangle with folded corner
    inner_pad = max(2, size // 5)
    doc_left = inner_pad
    doc_top = inner_pad
    doc_right = size - inner_pad
    doc_bottom = size - inner_pad
    fold = max(2, size // 6)

    # Document body (white)
    doc_points = [
        (doc_left, doc_top),
        (doc_right - fold, doc_top),
        (doc_right, doc_top + fold),
        (doc_right, doc_bottom),
        (doc_left, doc_bottom),
    ]
    draw.polygon(doc_points, fill=WHITE)

    # Fold triangle (darker shade)
    fold_points = [
        (doc_right - fold, doc_top),
        (doc_right, doc_top + fold),
        (doc_right - fold, doc_top + fold),
    ]
    draw.polygon(fold_points, fill=ACCENT_DARK)

    # Text lines on the document
    if size >= 32:
        line_color = (180, 180, 180)
        line_y_start = doc_top + fold + max(2, size // 10)
        line_left = doc_left + max(2, size // 10)
        line_right_long = doc_right - max(3, size // 7)
        line_right_short = doc_left + (doc_right - doc_left) * 2 // 3
        line_h = max(1, size // 24)
        line_gap = max(2, size // 12)

        for i in range(min(4, (doc_bottom - line_y_start) // (line_h + line_gap))):
            y = line_y_start + i * (line_h + line_gap)
            right = line_right_short if i % 3 == 2 else line_right_long
            if y + line_h < doc_bottom - 2:
                draw.rectangle([line_left, y, right, y + line_h], fill=line_color)

    # Small blue accent dot — bottom-right corner
    if size >= 48:
        dot_r = max(2, size // 16)
        dot_cx = doc_right - dot_r - max(2, size // 12)
        dot_cy = doc_bottom - dot_r - max(2, size // 12)
        draw.ellipse(
            [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
            fill=ACCENT,
        )

    return img


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate each size
    images = {}
    for s in ICO_SIZES:
        images[s] = draw_icon(s)

    # Save .ico — Pillow needs the largest image as the base,
    # with smaller sizes passed via append_images
    ico_path = os.path.join(script_dir, "icon.ico")
    base = images[256]
    extras = [images[s] for s in ICO_SIZES if s != 256]
    base.save(ico_path, format="ICO", append_images=extras)
    ico_size = os.path.getsize(ico_path)
    print(f"Saved: {ico_path} ({ico_size:,} bytes, {len(ICO_SIZES)} sizes)")

    # Save 256px PNG
    png_path = os.path.join(script_dir, "icon_256.png")
    images[256].save(png_path, format="PNG")
    print(f"Saved: {png_path}")

    # Save 48px PNG for tray
    png48_path = os.path.join(script_dir, "icon_48.png")
    images[48].save(png48_path, format="PNG")
    print(f"Saved: {png48_path}")


if __name__ == "__main__":
    main()
