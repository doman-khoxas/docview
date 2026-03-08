"""Persistent user preferences stored as JSON."""
import json
from pathlib import Path
from app.logger import get_logger

logger = get_logger(__name__)

_PREFS_PATH = Path.home() / ".pdf_editor" / "preferences.json"

_DEFAULTS = {
    "theme": "dark",           # "dark", "light", "system"
    "zoom": 1.0,
    "sidebar_visible": True,
    "window_width": 1200,
    "window_height": 800,
    "window_x": None,
    "window_y": None,
    "last_directory": None,
}


class Preferences:
    def __init__(self):
        self._data: dict = dict(_DEFAULTS)
        self._load()

    def _load(self):
        try:
            if _PREFS_PATH.exists():
                with open(_PREFS_PATH, "r") as f:
                    saved = json.load(f)
                for k, v in saved.items():
                    if k in _DEFAULTS:
                        self._data[k] = v
                logger.debug("Preferences loaded from %s", _PREFS_PATH)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to load preferences: %s", e)

    def save(self):
        try:
            _PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_PREFS_PATH, "w") as f:
                json.dump(self._data, f, indent=2)
            logger.debug("Preferences saved to %s", _PREFS_PATH)
        except IOError as e:
            logger.error("Failed to save preferences: %s", e)

    def get(self, key: str, default=None):
        return self._data.get(key, default if default is not None else _DEFAULTS.get(key))

    def set(self, key: str, value):
        self._data[key] = value

    @property
    def theme(self) -> str:
        return self._data.get("theme", "dark")

    @theme.setter
    def theme(self, value: str):
        self._data["theme"] = value

    @property
    def zoom(self) -> float:
        return self._data.get("zoom", 1.0)

    @zoom.setter
    def zoom(self, value: float):
        self._data["zoom"] = value

    @property
    def sidebar_visible(self) -> bool:
        return self._data.get("sidebar_visible", True)

    @sidebar_visible.setter
    def sidebar_visible(self, value: bool):
        self._data["sidebar_visible"] = value

    @property
    def window_geometry(self) -> str:
        w = self._data.get("window_width", 1200)
        h = self._data.get("window_height", 800)
        x = self._data.get("window_x")
        y = self._data.get("window_y")
        if x is not None and y is not None:
            return f"{w}x{h}+{x}+{y}"
        return f"{w}x{h}"

    def save_window_geometry(self, geometry_str: str):
        """Parse '1200x800+100+50' format and save components."""
        try:
            parts = geometry_str.replace("+", "x").split("x")
            self._data["window_width"] = int(parts[0])
            self._data["window_height"] = int(parts[1])
            if len(parts) >= 4:
                self._data["window_x"] = int(parts[2])
                self._data["window_y"] = int(parts[3])
        except (ValueError, IndexError):
            pass
