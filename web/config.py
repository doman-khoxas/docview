"""DocView Web — configuration."""

import os
import tempfile

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads"
)
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {".pdf"}
RENDER_DPI = 150
DEFAULT_JPEG_QUALITY = 85
