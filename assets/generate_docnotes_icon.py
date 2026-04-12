#!/usr/bin/env python3
"""Generate DocNotes icon — sticky note with pen, distinct from DocView's document icon."""
from PIL import Image, ImageDraw
import os

TEAL = (78, 201, 176)        # #4ec9b0 — DocNotes accent
TEAL_DARK = (50, 150, 130)
YELLOW = (255, 249, 196)     # sticky note yellow
YELLOW_FOLD = (230, 220, 160)
DARK = (30, 30, 30)

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(1, size // 16)
    r = max(2, size // 8)

    # Background — teal rounded rect
    draw.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=r, fill=TEAL,
    )

    # Sticky note shape — yellow square with folded bottom-right corner
    m = max(3, size // 5)
    note_l, note_t = m, m
    note_r, note_b = size - m, size - m
    fold = max(2, size // 7)

    note_points = [
        (note_l, note_t),
        (note_r, note_t),
        (note_r, note_b - fold),
        (note_r - fold, note_b),
        (note_l, note_b),
    ]
    draw.polygon(note_points, fill=YELLOW)

    # Fold triangle
    fold_points = [
        (note_r, note_b - fold),
        (note_r - fold, note_b),
        (note_r - fold, note_b - fold),
    ]
    draw.polygon(fold_points, fill=YELLOW_FOLD)

    # Lines on the sticky note
    if size >= 32:
        line_color = (200, 190, 150)
        line_y = note_t + max(3, size // 8)
        line_left = note_l + max(2, size // 10)
        line_right = note_r - max(3, size // 7)
        line_h = max(1, size // 28)
        line_gap = max(2, size // 11)

        for i in range(min(3, (note_b - fold - line_y) // (line_h + line_gap))):
            y = line_y + i * (line_h + line_gap)
            right = line_right - (size // 5 if i == 2 else 0)
            if y + line_h < note_b - fold - 2:
                draw.rectangle([line_left, y, right, y + line_h], fill=line_color)

    # Small pen icon — bottom-right
    if size >= 48:
        pen_size = max(3, size // 10)
        px = note_r - pen_size
        py = note_t + max(2, size // 12)
        draw.rectangle([px, py, px + pen_size, py + pen_size * 3],
                        fill=TEAL_DARK)
        # Pen tip
        draw.polygon([
            (px, py + pen_size * 3),
            (px + pen_size, py + pen_size * 3),
            (px + pen_size // 2, py + pen_size * 3 + pen_size),
        ], fill=DARK)

    return img


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images = {s: draw_icon(s) for s in ICO_SIZES}

    ico_path = os.path.join(script_dir, "docnotes_icon.ico")
    base = images[256]
    extras = [images[s] for s in ICO_SIZES if s != 256]
    base.save(ico_path, format="ICO", append_images=extras)
    print(f"Saved: {ico_path} ({os.path.getsize(ico_path):,} bytes)")

    png_path = os.path.join(script_dir, "docnotes_icon_256.png")
    images[256].save(png_path, format="PNG")
    print(f"Saved: {png_path}")


if __name__ == "__main__":
    main()
