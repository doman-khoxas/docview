"""Dataclasses for each annotation type and commit logic."""
from dataclasses import dataclass, field
import fitz
from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnnotationBase:
    page_num: int
    color: str = "#4A9EFF"
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
class UnderlineAnnotation(AnnotationBase):
    color: str = "#ED4245"
    opacity: float = 0.8
    quads: list = field(default_factory=list)


@dataclass
class StrikeoutAnnotation(AnnotationBase):
    color: str = "#ED4245"
    opacity: float = 0.8
    quads: list = field(default_factory=list)


@dataclass
class ArrowAnnotation(AnnotationBase):
    x0: float = 0
    y0: float = 0
    x1: float = 0
    y1: float = 0
    border_width: float = 2


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
    """Embedded image placed on a page."""
    x0: float = 0
    y0: float = 0
    x1: float = 0
    y1: float = 0
    image_path: str = ""  # filesystem path to image file


@dataclass
class StickyNoteAnnotation(AnnotationBase):
    """Small icon annotation that shows popup text."""
    x: float = 0
    y: float = 0
    text: str = ""
    icon: str = "Note"  # Note, Comment, Help, Insert, Key, Paragraph
    color: str = "#FAA61A"


@dataclass
class StampAnnotation(AnnotationBase):
    """Stamp annotation (Approved, Confidential, Draft, etc.)."""
    x0: float = 0
    y0: float = 0
    x1: float = 0
    y1: float = 0
    stamp_text: str = "APPROVED"
    color: str = "#ED4245"


@dataclass
class RedactAnnotation(AnnotationBase):
    """Pending redaction rectangle — applied permanently via page.apply_redactions()."""
    x0: float = 0
    y0: float = 0
    x1: float = 0
    y1: float = 0
    color: str = "#000000"  # redact fill color (black)


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def commit_to_pdf(page: fitz.Page, annotation):
    logger.debug("Committing %s to page %d", type(annotation).__name__, annotation.page_num + 1)
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

    elif isinstance(annotation, UnderlineAnnotation):
        if annotation.quads:
            annot = page.add_underline_annot(quads=annotation.quads)
            annot.set_colors(stroke=_hex_to_rgb(annotation.color))
            annot.set_opacity(annotation.opacity)
            annot.update()

    elif isinstance(annotation, StrikeoutAnnotation):
        if annotation.quads:
            annot = page.add_strikeout_annot(quads=annotation.quads)
            annot.set_colors(stroke=_hex_to_rgb(annotation.color))
            annot.set_opacity(annotation.opacity)
            annot.update()

    elif isinstance(annotation, ArrowAnnotation):
        p1 = fitz.Point(annotation.x0, annotation.y0)
        p2 = fitz.Point(annotation.x1, annotation.y1)
        annot = page.add_line_annot(p1, p2)
        annot.set_border(width=annotation.border_width)
        annot.set_colors(stroke=_hex_to_rgb(annotation.color))
        annot.set_opacity(annotation.opacity)
        annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_CLOSED_ARROW)
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
        if annotation.image_path:
            rect = fitz.Rect(annotation.x0, annotation.y0, annotation.x1, annotation.y1)
            page.insert_image(rect, filename=annotation.image_path)

    elif isinstance(annotation, StickyNoteAnnotation):
        point = fitz.Point(annotation.x, annotation.y)
        annot = page.add_text_annot(point, annotation.text, icon=annotation.icon)
        annot.set_colors(stroke=_hex_to_rgb(annotation.color))
        annot.set_opacity(annotation.opacity)
        annot.update()

    elif isinstance(annotation, StampAnnotation):
        rect = fitz.Rect(annotation.x0, annotation.y0, annotation.x1, annotation.y1)
        annot = page.add_stamp_annot(rect, stamp=0)
        annot.set_info(content=annotation.stamp_text)
        annot.set_colors(stroke=_hex_to_rgb(annotation.color))
        annot.set_opacity(annotation.opacity)
        annot.update()

    elif isinstance(annotation, RedactAnnotation):
        # Redactions are handled separately via page.apply_redactions().
        # If commit_to_pdf is called on a RedactAnnotation, it means
        # the user saved without applying — add as a visual redact annot
        # so it persists in the PDF and can be applied later.
        rect = fitz.Rect(annotation.x0, annotation.y0, annotation.x1, annotation.y1)
        page.add_redact_annot(rect, fill=_hex_to_rgb(annotation.color))
