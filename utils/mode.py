"""
ThemeManager — Singleton untuk mengelola dark/light mode di seluruh aplikasi.
Menyimpan state tema saat ini dan menyediakan sinyal untuk memberitahu
semua window ketika tema berubah.
"""

import os
from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    """Singleton yang mengelola tema dark/light untuk seluruh aplikasi."""
    
    # Sinyal yang di-emit ketika tema berubah, membawa nama tema ("dark"/"light")
    theme_changed = Signal(str)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._current_theme = "dark"  # Default: dark mode
        self._styles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'styles')
    
    @property
    def current_theme(self) -> str:
        """Mengembalikan tema saat ini ('dark' atau 'light')."""
        return self._current_theme
    
    @property
    def is_dark(self) -> bool:
        """True jika tema saat ini adalah dark mode."""
        return self._current_theme == "dark"
    
    def toggle(self):
        """Toggle antara dark dan light mode."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.set_theme(new_theme)
    
    def set_theme(self, theme: str):
        """Set tema ke 'dark' atau 'light'."""
        if theme not in ("dark", "light"):
            return
        self._current_theme = theme
        self.theme_changed.emit(theme)
    
    def get_stylesheet(self) -> str:
        """Membaca dan mengembalikan isi file QSS untuk tema saat ini."""
        filename = f"{self._current_theme}.qss"
        filepath = os.path.join(self._styles_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"[ThemeManager] File tidak ditemukan: {filepath}")
            return ""


# Singleton global
theme_manager = ThemeManager()
