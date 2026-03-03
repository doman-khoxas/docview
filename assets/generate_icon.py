"""Generate DocView icon as .ico file using Pillow."""
from PIL import Image, ImageDraw, ImageFont
import os

SIZES = [16, 32, 48, 64, 128, 256]
OUTPUT = os.path.join(os.path.dirname(__file__), "docview.ico")


def draw_icon(size: int) -> Image.Image:
    """Draw a simple PDF-document icon at the given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(1, size // 16)
    # Document body (rounded rect approximation)
    doc_left = pad
    doc_top = pad
    doc_right = size - pad
    doc_bottom = size - pad
    corner_fold = max(3, size // 4)

    # Shadow
    shadow_off = max(1, size // 32)
    draw.rounded_rectangle(
        [doc_left + shadow_off, doc_top + shadow_off, doc_right + shadow_off, doc_bottom + shadow_off],
        radius=max(1, size // 16),
        fill=(17, 18, 20, 120)
    )

    # Main document body — dark surface
    draw.rounded_rectangle(
        [doc_left, doc_top, doc_right, doc_bottom],
        radius=max(1, size // 16),
        fill=(43, 45, 49, 255)  # BG_SURFACE #2B2D31
    )

    # Corner fold triangle
    fold_pts = [
        (doc_right - corner_fold, doc_top),
        (doc_right, doc_top + corner_fold),
        (doc_right, doc_top),
    ]
    draw.polygon(fold_pts, fill=(34, 35, 39, 255))  # BG_PANEL #222327

    fold_line = [
        (doc_right - corner_fold, doc_top),
        (doc_right - corner_fold, doc_top + corner_fold),
        (doc_right, doc_top + corner_fold),
    ]
    draw.line(fold_line, fill=(74, 158, 255, 200), width=max(1, size // 64))

    # "PDF" text or "D" letter in accent blue
    text = "D" if size < 48 else "DV"
    try:
        font_size = max(8, size // 3)
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2 + max(1, size // 12)
    draw.text((tx, ty), text, fill=(74, 158, 255, 255), font=font)  # ACCENT #4A9EFF

    # Subtle lines representing text
    line_y_start = doc_top + corner_fold + max(2, size // 10)
    line_left = doc_left + max(2, size // 8)
    line_right = doc_right - max(2, size // 8)
    line_gap = max(2, size // 12)

    if size >= 64:
        for i in range(3):
            ly = line_y_start + i * line_gap
            if ly + 1 < ty - 2:  # Don't overlap with text
                w = line_right - line_left if i < 2 else (line_right - line_left) * 2 // 3
                draw.line(
                    [(line_left, ly), (line_left + w, ly)],
                    fill=(107, 109, 114, 100),  # TEXT_MUTED
                    width=max(1, size // 64)
                )

    return img


def main():
    images = []
    for s in SIZES:
        images.append(draw_icon(s))

    # Save as .ico with all sizes
    images[0].save(
        OUTPUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=images[1:]
    )
    print(f"Icon saved to {OUTPUT}")

    # Also save a PNG for tkinter window icon
    png_path = OUTPUT.replace(".ico", ".png")
    draw_icon(256).save(png_path)
    print(f"PNG saved to {png_path}")


if __name__ == "__main__":
    main()
