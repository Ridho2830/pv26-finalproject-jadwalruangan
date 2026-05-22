# ui/mahasiswa.py
from functools import partial

from PySide6.QtCore import (
    Qt,
    QEasingCurve,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
    QPauseAnimation,
)

from PySide6.QtGui import QColor

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QPushButton,
    QScrollArea
)

from utils.components import CubeWidget
from utils.mode import theme_manager


class MahasiswaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.rooms_raw = []
        self.current_filter = "Semua"
        self.setup_ui()
        self.load_styles()
        self.refresh_data()

    def setup_ui(self):
        self.setObjectName("mahasiswa_page")

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # =====================================================
        # SIDEBAR
        # =====================================================
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 24, 20, 24)
        sidebar_layout.setSpacing(16)

        logo = QLabel("ReservasiKampus")
        logo.setObjectName("sidebar_logo")
        
        user_name = QLabel("Satria")
        sidebar_layout.addWidget(user_name)
        dashboard_btn = QPushButton("Dashboard")
        booking_btn = QPushButton("Jadwal Ruangan")
        history_btn = QPushButton("Peminjaman Saya")
        profile_btn = QPushButton("Riwayat")
        setting_btn = QPushButton("Pengaturan")

        buttons = [dashboard_btn, booking_btn, history_btn, profile_btn, setting_btn]

        for btn in buttons:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(42)
            btn.setObjectName("sidebar_btn")

        booking_btn.setObjectName("sidebar_btn_active")

        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(20)

        for btn in buttons:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setMinimumHeight(42)
        logout_btn.setObjectName("logout_btn")

        sidebar_layout.addWidget(logout_btn)

        # =====================================================
        # CONTENT
        # =====================================================
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(24)

        # HEADER
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel("Dashboard Mahasiswa")
        title.setObjectName("page_title")

        subtitle = QLabel(
            "Lihat status ruangan dan lakukan reservasi dengan cepat."
        )
        subtitle.setObjectName("page_subtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        right_header = QHBoxLayout()

        theme_btn = QPushButton("🌙")
        theme_btn.setFixedSize(42, 42)
        theme_btn.clicked.connect(self.toggle_theme)

        right_header.addWidget(theme_btn)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addLayout(right_header)

        content_layout.addLayout(header_layout)

        # =====================================================
		# STATS
		# =====================================================
        self.stats_label = QLabel("Loading...")
        self.stats_label.setObjectName("stats_label")

        content_layout.addWidget(self.stats_label)

        # =====================================================
        # ROOM GRID
        # =====================================================

        section_title = QLabel("Daftar Ruangan")
        section_title.setObjectName("section_title")

        content_layout.addWidget(section_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.canvas_widget = QWidget()

        self.canvas_layout = QGridLayout(self.canvas_widget)
        self.canvas_layout.setSpacing(16)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.canvas_widget)

        content_layout.addWidget(scroll)

        # =====================================================
        # ROOT
        # =====================================================

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content)
    
    def refresh_data(self):
        """Memperbarui data ruangan dari database Supabase dan merender kartu ruangan."""
        if hasattr(self, 'anim_group') and self.anim_group.state() == QParallelAnimationGroup.Running:
            self.anim_group.stop()
            
        self.clear_layout(self.canvas_layout)
        self.cards = []
        self.rooms_raw = []
        
        # Ambil filter status aktif
        filter_text = getattr(self, 'current_filter', 'Semua')

        # Fetch data dari Supabase
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        try:
            rooms_data = (
				supabase
				.table("ruangan")
				.select("*")
			)
            
            if not rooms_data:
                rooms_data = []
        except Exception as e:
            print("Supabase Error:", e)
            ooms_data = []
        
        if not rooms_data:
            rooms_data = []
        
        counts = {"Tersedia": 0, "Terbooking": 0, "Terpakai": 0}
        
        filtered_rooms = []
        
        for r in rooms_data:
            name = r.get('nama', 'Unknown')
            gedung = r.get('gedung', 'Unknown')
            lantai = r.get('lantai', 0)
            kapasitas = r.get('kapasitas', 0)
            status = r.get('status', 'Tersedia')
            
            # Fallback mapping if database has legacy values
            if status == "Digunakan":
                status = "Terpakai"
            elif status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
                status = "Terpakai"
            elif status == "Dosen":
                status = "Terbooking"
            
            # Hitung statistik dari database (sebelum difilter untuk visualisasi statistik)
            if status in counts:
                counts[status] += 1
            
            # Filter check
            match = False
            if filter_text == "Semua":
                match = True
            elif filter_text == status:
                match = True
                
            if not match:
                continue
            
            badge_class = "badge_available"
            if status == "Terpakai":
                badge_class = "badge_in_use"
            elif status == "Terbooking":
                badge_class = "badge_booked"
                
            filtered_rooms.append((name, status, badge_class))
            self.rooms_raw.append(r)
        
        # Update label statistik
        if hasattr(self, 'stats_label'):
            self.stats_label.setText(f"{counts.get('Tersedia', 0)} TERSEDIA · {counts.get('Terbooking', 0)} TERBOOKING · {counts.get('Terpakai', 0)} TERPAKAI")
        
        # Render kartu ruangan
        if not filtered_rooms:
            empty_icon = QLabel("📭")
            empty_icon.setAlignment(Qt.AlignCenter)
            empty_icon.setStyleSheet("font-size: 48px; background-color: transparent; padding-top: 40px;")
            
            empty_title = QLabel("Tidak Ada Ruangan")
            empty_title.setAlignment(Qt.AlignCenter)
            empty_title.setStyleSheet("font-size: 18px; font-weight: 700; background-color: transparent; padding: 8px;")
            
            empty_desc = QLabel("Jadwal ruangan kosong atau tidak ada ruangan yang sesuai filter.")
            empty_desc.setAlignment(Qt.AlignCenter)
            empty_desc.setWordWrap(True)
            empty_desc.setStyleSheet("font-size: 13px; color: #6b5e8a; background-color: transparent;")
            
            self.canvas_layout.addWidget(empty_icon, 0, 0)
            self.canvas_layout.addWidget(empty_title, 1, 0)
            self.canvas_layout.addWidget(empty_desc, 2, 0)
            return
        
        import json
        for i, (name, status, badge_class) in enumerate(filtered_rooms):
            r = self.rooms_raw[i]
            kapasitas = r.get('kapasitas', 0)
            gedung = r.get('gedung', '-')
            lantai = r.get('lantai', '-')
            
            fasilitas_raw = r.get('fasilitas') or r.get('fasilitas_list')
            fasilitas_list = []
            
            if fasilitas_raw:
                if isinstance(fasilitas_raw, str):
                    try:
                        fasilitas_list = json.loads(fasilitas_raw)
                        if not isinstance(fasilitas_list, list):
                            fasilitas_list = [str(fasilitas_list)]
                    except:
                        fasilitas_list = [f.strip() for f in fasilitas_raw.split(',') if f.strip()]
                elif isinstance(fasilitas_raw, list):
                    fasilitas_list = fasilitas_raw
                else:
                    fasilitas_list = [str(fasilitas_raw)]
            
            if not fasilitas_list:
                fasilitas_list = ["-"]
            
            card = QFrame()
            card.setProperty("class", "room_card")
            card.setCursor(Qt.PointingHandCursor)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(12)
            
            # 1. Baris Atas: Nama + Badge
            top_row = QHBoxLayout()
            title_lbl = QLabel(name)
            title_lbl.setProperty("class", "room_title")
            title_lbl.setStyleSheet("background-color: transparent;")
            is_dark = theme_manager.is_dark
            
            badge_lbl = QLabel(status.upper())
            badge_lbl.setAlignment(Qt.AlignCenter)
            badge_lbl.setProperty("class", f"badge {badge_class}")
                
            top_row.addWidget(title_lbl)
            top_row.addStretch()
            top_row.addWidget(badge_lbl)
            card_layout.addLayout(top_row)
            
            # 2. Subtitle
            subtitle_lbl = QLabel(f"Gedung {gedung} • Lantai {lantai} • Kapasitas {kapasitas}")
            subtitle_lbl.setProperty("class", "room_details")
            subtitle_lbl.setStyleSheet("background-color: transparent;")
            card_layout.addWidget(subtitle_lbl)
            
            # 3. Kubus 3D
            cube_color = "#22C55E"
            if status == "Terpakai" or status == "Digunakan" or status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
                cube_color = "#EF4444"
            elif status == "Terbooking" or status == "Dosen":
                cube_color = "#F59E0B"
                
            should_animate = status in ("Terpakai", "Digunakan", "Terbooking", "Dosen")
            cube_widget = CubeWidget(cube_color, should_animate=should_animate)
            cube_container = QWidget()
            cube_container_layout = QHBoxLayout(cube_container)
            cube_container_layout.addStretch()
            cube_container_layout.addWidget(cube_widget)
            cube_container_layout.addStretch()
            cube_container_layout.setContentsMargins(0, 8, 0, 8)
            cube_container.setStyleSheet("background-color: transparent;")
            card_layout.addWidget(cube_container)
            
            # 4. Chips Fasilitas
            chips_row = QHBoxLayout()
            chips_row.setSpacing(6)
            for fas in fasilitas_list:
                fas_lbl = QLabel(fas)
                fas_lbl.setProperty("class", "facility_chip")
                chips_row.addWidget(fas_lbl)
            chips_row.addStretch()
            card_layout.addLayout(chips_row)
            
            card.mousePressEvent = partial(self._on_card_clicked, index=i)
            
            # Container dengan Opacity Effect
            container = QWidget()
            container.setStyleSheet("background-color: transparent;")
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(8, 8, 8, 8)
            container_layout.addWidget(card)
            
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(16)
            shadow.setColor(QColor(155, 93, 229, 40) if is_dark else QColor(107, 114, 128, 40))
            shadow.setOffset(0, 4)
            card.setGraphicsEffect(shadow)
            
            opacity_effect = QGraphicsOpacityEffect(container)
            container.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0.0)
            
            self.cards.append(container)
        
        self.adjust_grid_columns()
        
        # Animasi staggered fade-in
        self.anim_group = QParallelAnimationGroup(self)
        for idx, container in enumerate(self.cards):
            effect = container.graphicsEffect()
            if isinstance(effect, QGraphicsOpacityEffect):
                anim = QPropertyAnimation(effect, b"opacity")
                anim.setDuration(450)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                
                seq_group = QSequentialAnimationGroup(self)
                pause = QPauseAnimation(idx * 75, self)
                seq_group.addAnimation(pause)
                seq_group.addAnimation(anim)
                
                def safe_remove_effect(c=container):
                    try:
                        c.setGraphicsEffect(None)
                    except RuntimeError:
                        pass
                
                seq_group.finished.connect(safe_remove_effect)
                self.anim_group.addAnimation(seq_group)
        self.anim_group.start()
    
    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())
                
    def adjust_grid_columns(self):
        columns = 3
        
        for i, card in enumerate(self.cards):
            row = i // columns
            col = i % columns
            self.canvas_layout.addWidget(card, row, col)
            
    def _on_card_clicked(self, event=None, index=0):
        room = self.rooms_raw[index]

    def toggle_theme(self):
        theme_manager.toggle_theme()

    def load_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #fdf7ff;
                color: #1d1b20;
                font-family: 'DM Sans';
            }

            #sidebar {
                background: #1e1b4b;
            }

            #sidebar_logo {
                color: white;
                font-size: 24px;
                font-weight: 700;
            }

            #sidebar_btn,
            #logout_btn {
                background: transparent;
                border: none;
                border-radius: 8px;
                color: #d1d5db;
                text-align: left;
                padding-left: 14px;
                font-size: 14px;
                font-weight: 500;
            }

            #sidebar_btn:hover,
            #logout_btn:hover {
                background: rgba(255,255,255,0.08);
            }

            #sidebar_btn_active {
                background: #4f378a;
                border-radius: 8px;
                color: white;
                text-align: left;
                padding-left: 14px;
                font-size: 14px;
                font-weight: 600;
            }

            #page_title {
                font-size: 32px;
                font-weight: 700;
            }

            #page_subtitle {
                color: #6b7280;
                font-size: 15px;
            }

            #section_title {
                font-size: 22px;
                font-weight: 700;
            }

            #stat_card,
            #room_card {
                background: white;
                border-radius: 12px;
                border: 1px solid #ece6ee;
            }

            #stat_title {
                color: #6b7280;
                font-size: 14px;
            }

            #stat_value {
                font-size: 32px;
                font-weight: 700;
            }

            #room_name {
                font-size: 18px;
                font-weight: 700;
            }

            #room_building {
                color: #6b7280;
                font-size: 14px;
            }

            #capacity_text {
                color: #4b5563;
                font-size: 14px;
            }

            #status_badge {
                background: #dcfce7;
                color: #166534;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                max-width: 120px;
            }

            #reserve_btn {
                background: #4f378a;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }

            #reserve_btn:hover {
                background: #6750a4;
            }
        """
        )