"""Settings dialog for vault path, theme, and preferences."""
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox, QGroupBox, QFormLayout
)
from PyQt5.QtGui import QFont

CONFIG_PATH = Path.home() / ".docview" / "config.json"


def load_config() -> dict:
    """Load user configuration."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_config(config: dict):
    """Save user configuration."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding='utf-8')


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DocView Settings")
        self.setMinimumWidth(500)
        self._config = load_config()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Obsidian vault
        vault_group = QGroupBox("Obsidian Vault")
        vault_layout = QFormLayout(vault_group)

        vault_row = QHBoxLayout()
        self._vault_entry = QLineEdit(self._config.get('vault_path', ''))
        self._vault_entry.setPlaceholderText("Path to Obsidian vault...")
        vault_row.addWidget(self._vault_entry)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_vault)
        vault_row.addWidget(browse_btn)

        vault_layout.addRow("Vault Path:", vault_row)
        layout.addWidget(vault_group)

        # Editor settings
        editor_group = QGroupBox("Editor")
        editor_layout = QFormLayout(editor_group)

        self._font_size = QLineEdit(str(self._config.get('editor_font_size', 13)))
        self._font_size.setFixedWidth(60)
        editor_layout.addRow("Font Size:", self._font_size)

        self._tab_size = QLineEdit(str(self._config.get('tab_size', 4)))
        self._tab_size.setFixedWidth(60)
        editor_layout.addRow("Tab Size:", self._tab_size)

        layout.addWidget(editor_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_vault(self):
        path = QFileDialog.getExistingDirectory(self, "Select Obsidian Vault")
        if path:
            self._vault_entry.setText(path)

    def _save(self):
        self._config['vault_path'] = self._vault_entry.text().strip()
        try:
            self._config['editor_font_size'] = int(self._font_size.text())
        except ValueError:
            pass
        try:
            self._config['tab_size'] = int(self._tab_size.text())
        except ValueError:
            pass
        save_config(self._config)
        self.accept()

    @property
    def vault_path(self) -> str:
        return self._config.get('vault_path', '')
