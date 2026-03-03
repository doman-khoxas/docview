"""DocView Configuration Constants - Professional Dark Theme."""

# --- Application Identity ---
WINDOW_TITLE = "DocView"
WINDOW_SIZE = "1200x800"
APPEARANCE_MODE = "dark"
COLOR_THEME = "dark-blue"

# --- Professional Dark Color Palette ---
# Backgrounds (layered grays for depth)
BG_DEEP = "#1A1B1E"          # Deepest background (main canvas area)
BG_PANEL = "#222327"          # Panel/sidebar background
BG_SURFACE = "#2B2D31"        # Elevated surface (cards, toolbars)
BG_HOVER = "#35373C"          # Hover state
BG_ACTIVE = "#3E4046"         # Active/selected state

# Legacy aliases
BG_ABYSS = BG_DEEP
CANVAS_BG = BG_DEEP

# Accent (blue)
ACCENT = "#4A9EFF"
ACCENT_HOVER = "#5AADFF"
ACCENT_MUTED = "#2D5A8E"
ACCENT_DIM = "#1E3A5C"

# Text
TEXT_PRIMARY = "#E1E2E4"
TEXT_SECONDARY = "#A0A1A4"
TEXT_MUTED = "#6B6D72"
TEXT_ACCENT = "#4A9EFF"

# Borders (brightened for more contrast between panels)
BORDER_DEFAULT = "#44464B"
BORDER_ACCENT = "#4A9EFF"
BORDER_SUBTLE = "#35373B"

# Status colors
COLOR_SUCCESS = "#3BA55C"
COLOR_WARNING = "#FAA61A"
COLOR_DANGER = "#ED4245"

# Legacy aliases (referenced throughout UI files)
BORDER_RED = BORDER_DEFAULT
TEXT_RED = TEXT_PRIMARY
HOVER_RED = BG_HOVER
ACTIVE_RED = BG_ACTIVE

# --- UI Geometry ---
CORNER_RADIUS = 6
BORDER_WIDTH = 1

# --- Viewport & Zoom ---
ZOOM_DEFAULT = 1.0
ZOOM_MIN = 0.25
ZOOM_MAX = 4.0
ZOOM_STEP = 0.1
RENDER_DPI = 150

# --- Continuous Viewport Layout ---
PAGE_GAP = 20
PAGE_SHADOW_OFFSET = 4
PAGE_SHADOW_COLOR = "#0D0E10"
OVERSCAN_PX = 200
PAGE_CACHE_SIZE = 20

# --- Annotation Defaults ---
DEFAULT_ANNOT_COLOR = "#4A9EFF"
DEFAULT_HIGHLIGHT_COLOR = "#FAA61A"
DEFAULT_TEXT_COLOR = "#E1E2E4"
DEFAULT_OPACITY = 0.5
DEFAULT_FONT_SIZE = 14
DEFAULT_BORDER_WIDTH = 2

# --- Sizing ---
SIDEBAR_WIDTH = 220
THUMBNAIL_WIDTH = 150
THUMBNAIL_SIDEBAR_WIDTH = 180
PROPERTIES_PANEL_WIDTH = 200
TAB_HEIGHT = 32
TAB_MAX_TITLE_LEN = 25

# --- Thumbnails ---
ACTIVE_THUMBNAIL_BORDER = ACCENT
THUMBNAIL_BORDER = BORDER_DEFAULT

# --- Limits ---
LAZY_THUMBNAIL_THRESHOLD = 20
RECENT_FILES_MAX = 10

# --- Search ---
SEARCH_HIGHLIGHT_COLOR = "#FAA61A"
SEARCH_ACTIVE_COLOR = "#ED4245"
