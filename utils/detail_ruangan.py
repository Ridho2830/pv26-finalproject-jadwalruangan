"""
DetailRuanganPopup — Dialog popup untuk menampilkan detail ruangan.
Ditampilkan saat pengguna mengklik kartu ruangan di halaman utama.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QWidget, QGridLayout)
from PySide6.QtCore import Qt
from utils.components import CubeWidget
from utils.mode import theme_manager


class DetailRuanganPopup(QDialog):
    """Popup dialog yang menampilkan informasi lengkap sebuah ruangan."""
    
    def __init__(self, room_data: dict, parent=None):
        super().__init__(parent)
        self.room_data = room_data
        self.setWindowTitle(f"Detail — {room_data.get('nama', 'Ruangan')}")
        self.setMinimumSize(380, 500)
        self.setMaximumSize(500, 650)
        self.setModal(True)
        
        # Terapkan tema
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
        
        self._build_ui()
    
    def _build_ui(self):
        """Membangun seluruh elemen UI popup."""
        r = self.room_data
        name = r.get('nama', 'Unknown')
        gedung = r.get('gedung', '-')
        lantai = r.get('lantai', '-')
        kapasitas = r.get('kapasitas', '-')
        status = r.get('status', 'Tersedia')
        fasilitas = r.get('fasilitas', '-')
        keterangan = r.get('keterangan', '')
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # ── Header: Nama + Badge ──
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 22px; font-weight: 800; background-color: transparent;")
        
        display_status = status
        if status == "Digunakan" or status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
            display_status = "Terpakai"
        elif status == "Dosen":
            display_status = "Terbooking"
            
        badge_lbl = QLabel(display_status.upper())
        badge_class = self._get_badge_class(status)
        badge_lbl.setProperty("class", f"badge {badge_class}")
        badge_lbl.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(name_lbl)
        header_layout.addStretch()
        header_layout.addWidget(badge_lbl)
        layout.addLayout(header_layout)
        
        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: rgba(147, 90, 255, 0.15); max-height: 1px;")
        layout.addWidget(sep)
        
        # ── Kubus 3D ──
        cube_color = self._get_cube_color(status)
        should_animate = status in ("Terpakai", "Digunakan", "Terbooking", "Dosen")
        cube = CubeWidget(cube_color, should_animate=should_animate)
        
        cube_container = QWidget()
        cube_layout = QHBoxLayout(cube_container)
        cube_layout.addStretch()
        cube_layout.addWidget(cube)
        cube_layout.addStretch()
        cube_layout.setContentsMargins(0, 8, 0, 8)
        cube_container.setStyleSheet("background-color: transparent;")
        layout.addWidget(cube_container)
        
        # ── Info Grid ──
        info_frame = QFrame()
        # Fix CSS leak: Don't use the generic room_card class that overrides everything
        info_frame.setObjectName("InfoCardFrame")
        info_frame.setStyleSheet("""
            QFrame#InfoCardFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
            }
        """)
        info_grid = QGridLayout(info_frame)
        info_grid.setContentsMargins(16, 16, 16, 16)
        info_grid.setSpacing(12)
        info_grid.setColumnStretch(1, 1)
        
        details = [
            ("🏢", "Gedung", str(gedung)),
            ("🏗", "Lantai", str(lantai)),
            ("👥", "Kapasitas", f"{kapasitas} orang"),
            ("📦", "Fasilitas", str(fasilitas)),
        ]
        
        for row, (icon, label, value) in enumerate(details):
            icon_lbl = QLabel(icon)
            icon_lbl.setFixedWidth(24)
            icon_lbl.setStyleSheet("font-size: 16px; background-color: transparent;")
            
            label_lbl = QLabel(label)
            label_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #6b5e8a; background-color: transparent;")
            
            value_lbl = QLabel(value)
            value_lbl.setWordWrap(True)
            value_lbl.setStyleSheet("font-size: 13px; font-weight: 700; background-color: transparent;")
            
            info_grid.addWidget(icon_lbl, row, 0, Qt.AlignTop)
            info_grid.addWidget(label_lbl, row, 1, Qt.AlignTop)
            info_grid.addWidget(value_lbl, row, 2, Qt.AlignTop)
        
        layout.addWidget(info_frame)
        
        # ── Keterangan (jika ada) ──
        if keterangan:
            ket_frame = QFrame()
            ket_frame.setProperty("class", "stat_chip")
            ket_layout = QHBoxLayout(ket_frame)
            ket_layout.setContentsMargins(12, 8, 12, 8)
            
            ket_icon = QLabel("📋")
            ket_icon.setStyleSheet("font-size: 14px; background-color: transparent;")
            ket_text = QLabel(keterangan)
            ket_text.setWordWrap(True)
            ket_text.setStyleSheet("font-size: 12px; font-weight: 600; background-color: transparent;")
            
            ket_layout.addWidget(ket_icon)
            ket_layout.addWidget(ket_text)
            ket_layout.addStretch()
            layout.addWidget(ket_frame)
        
        layout.addStretch()
        
        
        login_btn = QPushButton("Login untuk Memesan")
        login_btn.setObjectName("login_btn")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self._on_login_clicked)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(login_btn, 1)
        layout.addLayout(btn_layout)
    
    def _get_badge_class(self, status: str) -> str:
        """Mengembalikan class badge berdasarkan status."""
        if status == "Terpakai" or status == "Digunakan" or status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
            return "badge_in_use"
        elif status == "Terbooking" or status == "Dosen":
            return "badge_booked"
        return "badge_available"
    
    def _get_cube_color(self, status: str) -> str:
        """Mengembalikan warna kubus berdasarkan status."""
        if status == "Terpakai" or status == "Digunakan" or status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
            return "#EF4444"
        elif status == "Terbooking" or status == "Dosen":
            return "#F59E0B"
        return "#22C55E"
        
    def _on_login_clicked(self):
        """Handler saat tombol login diklik — tutup popup lalu navigasi ke login."""
        self.close()
        # Cari MainWindow secara rekursif dari parent popup
        parent_widget = self.parent()
        while parent_widget is not None:
            if hasattr(parent_widget, 'switch_to_login'):
                parent_widget.switch_to_login()
                return
            parent_widget = parent_widget.parent()