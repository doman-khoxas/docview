"""Dataclasses for each annotation type and commit logic."""
from dataclasses import dataclass, field
import fitz


@dataclass
class AnnotationBase:
    page_num: int
    color: str = "#FF0000"
    opacity: float = 1.0


@dataclass
class RectAnnotation(AnnotationBase):
    x0: float = 0
    y0: float = 0
    x1: float = 0
    y1: float = 0
    border_width: float = 2
    fill_color: str | None = None


@dataclass
class CircleAnnotation(AnnotationBase):
    x0: float = 0
    y0: float = 0
    x1: float = 0
    y1: float = 0
    border_width: float = 2
    fill_color: str | None = None


@dataclass
class LineAnnotation(AnnotationBase):
    x0: float = 0
    y0: float = 0
    x1: float = 0
    y1: float = 0
    border_width: float = 2


@dataclass
class HighlightAnnotation(AnnotationBase):
    color: str = "#FFFF00"
    opacity: float = 0.5
    quads: list = field(default_factory=list)  # list of fitz.Quad


@dataclass
class FreetextAnnotation(AnnotationBase):
    x: float = 0
    y: float = 0
    text: str = ""
    font_size: float = 12
    text_color: str = "#000000"
    color: str = "#FFFFFF"


@dataclass
class InkAnnotation(AnnotationBase):
    points: list = field(default_factory=list)  # list of (x, y) tuples
    border_width: float = 2


@dataclass
class ImageAnnotation(AnnotationBase):
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 100
    image_path: str = ""
    image_data: bytes = field(default_factory=bytes, repr=False)  # raw image bytes


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def commit_to_pdf(page: fitz.Page, annotation):
    if isinstance(annotation, RectAnnotation):
        rect = fitz.Rect(annotation.x0, annotation.y0, annotation.x1, annotation.y1)
        annot = page.add_rect_annot(rect)
        annot.set_border(width=annotation.border_width)
        annot.set_colors(stroke=_hex_to_rgb(annotation.color))
        if annotation.fill_color:
            annot.set_colors(fill=_hex_to_rgb(annotation.fill_color))
        annot.set_opacity(annotation.opacity)
        annot.update()

    elif isinstance(annotation, CircleAnnotation):
        rect = fitz.Rect(annotation.x0, annotation.y0, annotation.x1, annotation.y1)
        annot = page.add_circle_annot(rect)
        annot.set_border(width=annotation.border_width)
        annot.set_colors(stroke=_hex_to_rgb(annotation.color))
        if annotation.fill_color:
            annot.set_colors(fill=_hex_to_rgb(annotation.fill_color))
        annot.set_opacity(annotation.opacity)
        annot.update()

    elif isinstance(annotation, LineAnnotation):
        p1 = fitz.Point(annotation.x0, annotation.y0)
        p2 = fitz.Point(annotation.x1, annotation.y1)
        annot = page.add_line_annot(p1, p2)
        annot.set_border(width=annotation.border_width)
        annot.set_colors(stroke=_hex_to_rgb(annotation.color))
        annot.set_opacity(annotation.opacity)
        annot.update()

    elif isinstance(annotation, HighlightAnnotation):
        if annotation.quads:
            annot = page.add_highlight_annot(quads=annotation.quads)
            annot.set_colors(stroke=_hex_to_rgb(annotation.color))
            annot.set_opacity(annotation.opacity)
            annot.update()

    elif isinstance(annotation, FreetextAnnotation):
        rect = fitz.Rect(annotation.x, annotation.y,
                         annotation.x + 200, annotation.y + annotation.font_size + 10)
        annot = page.add_freetext_annot(
            rect,
            annotation.text,
            fontsize=annotation.font_size,
            text_color=_hex_to_rgb(annotation.text_color),
            fill_color=_hex_to_rgb(annotation.color),
        )
        annot.set_opacity(annotation.opacity)
        annot.update()

    elif isinstance(annotation, InkAnnotation):
        if annotation.points:
            annot = page.add_ink_annot([annotation.points])
            annot.set_border(width=annotation.border_width)
            annot.set_colors(stroke=_hex_to_rgb(annotation.color))
            annot.set_opacity(annotation.opacity)
            annot.update()

    elif isinstance(annotation, ImageAnnotation):
        rect = fitz.Rect(annotation.x, annotation.y,
                         annotation.x + annotation.width,
                         annotation.y + annotation.height)
        if annotation.image_data:
            page.insert_image(rect, stream=annotation.image_data)
        elif annotation.image_path:
            page.insert_image(rect, filename=annotation.image_path)
