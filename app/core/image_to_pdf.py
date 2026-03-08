"""Convert image files to searchable PDFs via OCR.

Handles alpha channel flattening (RGBA → RGB) and runs OCR via ocrmypdf
to produce a searchable PDF from any supported image format.
"""
import os
import tempfile
from pathlib import Path
from PIL import Image
import ocrmypdf
from app.logger import get_logger

logger = get_logger(__name__)

# Image extensions DocView can open and convert
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".gif"}


def flatten_alpha(img: Image.Image) -> Image.Image:
    """Strip alpha channel by compositing onto a white background."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        logger.debug("Flattening alpha channel (%s → RGB)", img.mode)
        background = Image.new("RGB", img.size, (255, 255, 255))
        # Handle palette mode with transparency
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1])
        return background
    elif img.mode not in ("RGB", "L"):
        return img.convert("RGB")
    return img


def image_to_pdf(image_path: str, output_pdf_path: str | None = None,
                 language: str = "eng", deskew: bool = True,
                 clean: bool = True, dpi: int = 300) -> str:
    """Convert an image file to a searchable PDF using OCR.

    Args:
        image_path: Path to the source image.
        output_pdf_path: Path for the output PDF. If None, uses the same
            directory/name as the image with a .pdf extension.
        language: OCR language code (default "eng").
        deskew: Straighten skewed text.
        clean: Remove visual noise before OCR.
        dpi: DPI to assign to the image (for proper scaling).

    Returns:
        Path to the generated PDF.
    """
    image_path = os.path.abspath(image_path)
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if output_pdf_path is None:
        output_pdf_path = str(Path(image_path).with_suffix(".pdf"))

    logger.info("Converting image to PDF: %s → %s", image_path, output_pdf_path)

    # Load and flatten alpha channel
    img = Image.open(image_path)
    img = flatten_alpha(img)

    # Save to a lossless temp PNG for ocrmypdf (preserves OCR accuracy)
    fd, tmp_img_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)

    try:
        img.save(tmp_img_path, "PNG")
        logger.debug("Flattened image saved to temp: %s", tmp_img_path)

        # Run OCR to produce searchable PDF
        ocrmypdf.ocr(
            tmp_img_path,
            output_pdf_path,
            image_dpi=dpi,
            deskew=deskew,
            clean=clean,
            language=language,
        )

        logger.info("Image → PDF conversion complete: %s", output_pdf_path)
        return output_pdf_path

    finally:
        # Clean up temp image
        if os.path.exists(tmp_img_path):
            try:
                os.unlink(tmp_img_path)
            except OSError:
                pass
