#!/usr/bin/env python3
"""Generate file-type icons for PDF and MD association in Windows Explorer."""
from PIL import Image, ImageDraw, ImageFont
import os

WHITE = (255, 255, 255)
ACCENT_BLUE = (0, 122, 204)
ACCENT_TEAL = (78, 201, 176)
FOLD_BLUE = (0, 90, 158)
FOLD_TEAL = (50, 150, 130)
DARK = (40, 40, 40)

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def draw_filetype_icon(size: int, label: str, color: tuple, fold_color: tuple) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(1, size // 10)
    fold = max(3, size // 5)

    doc_l, doc_t = pad, pad
    doc_r, doc_b = size - pad, size - pad

    # Document body
    points = [
        (doc_l, doc_t),
        (doc_r - fold, doc_t),
        (doc_r, doc_t + fold),
        (doc_r, doc_b),
        (doc_l, doc_b),
    ]
    draw.polygon(points, fill=WHITE)

    # Fold
    fold_pts = [
        (doc_r - fold, doc_t),
        (doc_r, doc_t + fold),
        (doc_r - fold, doc_t + fold),
    ]
    draw.polygon(fold_pts, fill=(220, 220, 220))

    # Color banner at bottom
    banner_h = max(4, size // 4)
    draw.rectangle([doc_l, doc_b - banner_h, doc_r, doc_b], fill=color)

    # Label text on the banner
    if size >= 32:
        try:
            font_size = max(6, banner_h - 4)
            font = ImageFont.truetype("segoeui.ttf", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (doc_l + doc_r - tw) // 2
        ty = doc_b - banner_h + (banner_h - th) // 2 - 1
        draw.text((tx, ty), label, fill=WHITE, font=font)

    # Content lines
    if size >= 32:
        line_color = (200, 200, 200)
        line_y = doc_t + fold + max(2, size // 12)
        line_left = doc_l + max(2, size // 8)
        line_right = doc_r - max(3, size // 6)
        line_h = max(1, size // 28)
        gap = max(2, size // 14)

        for i in range(min(3, (doc_b - banner_h - line_y) // (line_h + gap))):
            y = line_y + i * (line_h + gap)
            r = line_right - (size // 4 if i == 2 else 0)
            if y + line_h < doc_b - banner_h - 2:
                draw.rectangle([line_left, y, r, y + line_h], fill=line_color)

    return img


def save_ico(images: dict, path: str):
    base = images[256]
    extras = [images[s] for s in ICO_SIZES if s != 256]
    base.save(path, format="ICO", append_images=extras)
    print(f"Saved: {path} ({os.path.getsize(path):,} bytes)")


def main():
    d = os.path.dirname(os.path.abspath(__file__))

    # PDF icon — blue banner
    pdf_imgs = {s: draw_filetype_icon(s, "PDF", ACCENT_BLUE, FOLD_BLUE) for s in ICO_SIZES}
    save_ico(pdf_imgs, os.path.join(d, "filetype_pdf.ico"))
    pdf_imgs[256].save(os.path.join(d, "filetype_pdf_256.png"), format="PNG")

    # MD icon — teal banner
    md_imgs = {s: draw_filetype_icon(s, "MD", ACCENT_TEAL, FOLD_TEAL) for s in ICO_SIZES}
    save_ico(md_imgs, os.path.join(d, "filetype_md.ico"))
    md_imgs[256].save(os.path.join(d, "filetype_md_256.png"), format="PNG")

    print("Done.")


if __name__ == "__main__":
    main()
