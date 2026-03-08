"""OCR Service — flatten image alpha channels and run ocrmypdf.

Converts any image (PNG, JPG, BMP, TIFF, WebP) into a searchable PDF.
Handles RGBA/LA/P+transparency by compositing onto a solid white background
before handing off to Tesseract via ocrmypdf.
"""
import os
import tempfile
from PIL import Image
import ocrmypdf
from app.logger import get_logger

logger = get_logger(__name__)


def flatten_alpha_to_rgb(image_path: str) -> str:
    """Strip alpha/transparency from an image, save as temp JPEG.

    Args:
        image_path: Path to the source image file.

    Returns:
        Path to the flattened temporary JPEG file.
        Caller is responsible for deleting this file.
    """
    img = Image.open(image_path)

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        logger.info("Alpha channel detected in %s — flattening to white", image_path)
        if img.mode == "P":
            img = img.convert("RGBA")
        solid_white = Image.new("RGB", img.size, (255, 255, 255))
        solid_white.paste(img, mask=img.split()[-1])
        img = solid_white
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    img.save(tmp_path, "JPEG", quality=95)
    logger.debug("Flattened image saved: %s", tmp_path)
    return tmp_path


def ocr_image_to_pdf(image_path: str, output_pdf_path: str,
                     language: str = "eng", dpi: int = 300) -> str:
    """Convert an image to a searchable PDF via OCR.

    Flattens any alpha channel, then runs ocrmypdf with deskew + clean.

    Args:
        image_path: Path to the source image.
        output_pdf_path: Destination path for the searchable PDF.
        language: Tesseract language code (default "eng").
        dpi: DPI to assign to the image (default 300).

    Returns:
        Path to the generated PDF.

    Raises:
        Exception: If OCR or image processing fails.
    """
    logger.info("OCR service: %s -> %s (lang=%s, dpi=%d)",
                image_path, output_pdf_path, language, dpi)

    tmp_path = flatten_alpha_to_rgb(image_path)
    try:
        ocrmypdf.ocr(
            tmp_path,
            output_pdf_path,
            image_dpi=dpi,
            deskew=True,
            clean=True,
            language=language,
        )
        logger.info("OCR complete: %s", output_pdf_path)
        return output_pdf_path
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
