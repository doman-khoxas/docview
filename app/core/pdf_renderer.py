"""Render PDF pages to PIL images and handle coordinate conversion."""
import fitz
from PIL import Image
from app.config import RENDER_DPI


def render_page(page: fitz.Page, zoom: float = 1.0) -> Image.Image:
    mat = fitz.Matrix(zoom * RENDER_DPI / 72, zoom * RENDER_DPI / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def render_thumbnail(page: fitz.Page, width: int = 150) -> Image.Image:
    rect = page.rect
    zoom = width / rect.width
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def canvas_to_pdf_coords(x: float, y: float, zoom: float) -> tuple[float, float]:
    scale = zoom * RENDER_DPI / 72
    return x / scale, y / scale


def pdf_to_canvas_coords(x: float, y: float, zoom: float) -> tuple[float, float]:
    scale = zoom * RENDER_DPI / 72
    return x * scale, y * scale


def get_render_scale(zoom: float) -> float:
    return zoom * RENDER_DPI / 72
