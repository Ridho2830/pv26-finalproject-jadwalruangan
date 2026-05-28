from PySide6.QtCore import QTimer, QDateTime, Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QPauseAnimation
from functools import partial
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QComboBox, 
                               QFrame, QGridLayout, QScrollArea,
                               QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PySide6.QtGui import QColor

# Impor komponen kustom dari utils
from utils.components import CubeWidget
from utils.mode import theme_manager
from utils.detail_ruangan import DetailRuanganPopup

class StatusRuanganView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Header
        self.create_header()
        
        # 2. Filter Section
        self.create_filter_section()
        
        # 3. Main Canvas (Scrollable)
        self.create_main_canvas()
        
        # 4. Footer
        self.create_footer()
        
        # Load Stylesheet
        self.load_stylesheet()

    def create_header(self):
        header = QWidget()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        header_layout.setSpacing(16)
        
        # ─── Sisi Kiri: Logo & Judul ───
        left_layout = QHBoxLayout()
        left_layout.setSpacing(12)
        
        logo_container = QFrame()
        logo_container.setObjectName("logo_container")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(8, 8, 8, 8)
        logo_label = QLabel("🏢") 
        logo_label.setStyleSheet("font-size: 18px; background-color: transparent;")
        logo_layout.addWidget(logo_label)
        
        title_label = QLabel('<span style="color: #00e5cc;">Reservasi</span><span style="color: #00e5cc;">Kampus</span>')
        title_label.setObjectName("header_title")
        
        left_layout.addWidget(logo_container, alignment=Qt.AlignVCenter)
        left_layout.addWidget(title_label, alignment=Qt.AlignVCenter)
        
        # ─── Sisi Kanan: Theme Toggle, Jam Real-Time & Login ───
        right_layout = QHBoxLayout()
        right_layout.setSpacing(14)
        
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("theme_toggle")
        self.theme_btn.setToolTip("Toggle Dark/Light Mode")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        
        self.time_label = QLabel()
        self.time_label.setObjectName("header_time")
        self.update_time()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        login_btn = QPushButton("Login")
        login_btn.setObjectName("login_btn")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self._on_login_clicked)
        
        right_layout.addWidget(self.theme_btn, alignment=Qt.AlignVCenter)
        right_layout.addWidget(self.time_label, alignment=Qt.AlignVCenter)
        right_layout.addWidget(login_btn, alignment=Qt.AlignVCenter)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        header_layout.addLayout(right_layout)
        
        self.main_layout.addWidget(header)

    def _on_login_clicked(self):
        """Navigasi ke Halaman Login."""
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'switch_to_login'):
            parent_widget.switch_to_login()

    def update_time(self):
        current_time = QDateTime.currentDateTime()
        hari = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
        nama_hari = hari[current_time.date().dayOfWeek() - 1]
        
        bulan = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        nama_bulan = bulan[current_time.date().month()]
        
        tanggal = current_time.date().day()
        waktu = current_time.toString("HH:mm")
        
        self.time_label.setText(f"🕒 {nama_hari}, {tanggal:02d} {nama_bulan} · {waktu}")

    def create_filter_section(self):
        filter_widget = QWidget()
        filter_widget.setObjectName("filter_section")
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(24, 12, 24, 12)
        filter_layout.setSpacing(24)
        
        # Sisi Kiri: Tab Filter
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(20)
        
        self.filter_buttons = {}
        filters = ["Semua Ruangan", "Tersedia", "Terbooking", "Terpakai"]
        
        for f in filters:
            btn = QPushButton(f)
            btn.setProperty("class", "filter_tab")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(partial(self._on_filter_tab_clicked, f))
            self.filter_buttons[f] = btn
            tab_layout.addWidget(btn)
        
        self.filter_buttons["Semua Ruangan"].setProperty("class", "filter_tab active")
        self.current_filter = "Semua"
            
        # Sisi Kanan: Teks Statistik
        self.stats_label = QLabel("0 TERSEDIA · 0 TERBOOKING · 0 TERPAKAI")
        self.stats_label.setObjectName("stats_text")
        self.stats_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        
        filter_layout.addLayout(tab_layout)
        filter_layout.addStretch()
        filter_layout.addWidget(self.stats_label)
        
        self.main_layout.addWidget(filter_widget)

    def _on_filter_tab_clicked(self, filter_name):
        for name, btn in self.filter_buttons.items():
            btn.setProperty("class", "filter_tab")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        clicked_btn = self.filter_buttons[filter_name]
        clicked_btn.setProperty("class", "filter_tab active")
        clicked_btn.style().unpolish(clicked_btn)
        clicked_btn.style().polish(clicked_btn)
        
        if filter_name == "Semua Ruangan":
            self.current_filter = "Semua"
        else:
            self.current_filter = filter_name
            
        self.refresh_data()

    def create_main_canvas(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("main_canvas")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.canvas_widget = QWidget()
        self.canvas_main_layout = QVBoxLayout(self.canvas_widget)
        self.canvas_main_layout.setContentsMargins(24, 16, 24, 24)
        self.canvas_main_layout.setSpacing(16)
        
        section_lbl = QLabel("SEMUA RUANGAN")
        section_lbl.setObjectName("section_label")
        self.canvas_main_layout.addWidget(section_lbl)
        
        self.grid_container = QWidget()
        self.canvas_layout = QGridLayout(self.grid_container)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_layout.setSpacing(16)
        
        self.canvas_main_layout.addWidget(self.grid_container)
        self.canvas_main_layout.addStretch()
        
        self.scroll_area.setWidget(self.canvas_widget)
        self.main_layout.addWidget(self.scroll_area)

    def clear_layout(self, layout):
        """Membersihkan semua widget dari layout secara rekursif."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

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
        rooms_data = supabase.table('ruangan').select()
        
        if not rooms_data:
            rooms_data = []
        
        counts = {"Tersedia": 0, "Terbooking": 0, "Terpakai": 0}
        
        filtered_rooms = []
        
        # Deduplikasi ruangan berdasarkan nama agar tidak ganda di layar
        seen_names = set()
        
        for r in rooms_data:
            name = r.get('nama', 'Unknown')
            
            # Lewati jika ruangan ini sudah ada
            if name in seen_names:
                continue
            seen_names.add(name)
            
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

    def _on_card_clicked(self, event, index):
        if index < len(self.rooms_raw):
            room_data = self.rooms_raw[index]
            popup = DetailRuanganPopup(room_data, parent=self)
            popup.exec()

    def adjust_grid_columns(self):
        if not hasattr(self, 'cards') or not self.cards:
            return
            
        width = self.scroll_area.width()
        if width <= 0:
            width = self.width()
            
        if width < 500:
            cols = 2
        else:
            cols = max(2, (width - 48) // 320)
        
        for i in reversed(range(self.canvas_layout.count())):
            self.canvas_layout.takeAt(i)
            
        for i, card in enumerate(self.cards):
            row = i // cols
            col = i % cols
            self.canvas_layout.addWidget(card, row, col)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_grid_columns()

    def create_footer(self):
        self.notif_banner = QFrame()
        self.notif_banner.setObjectName("notif_banner")
        notif_layout = QHBoxLayout(self.notif_banner)
        notif_layout.setContentsMargins(24, 8, 24, 8)
        
        notif_icon = QLabel("⚠️")
        notif_icon.setStyleSheet("font-size: 16px; background-color: transparent;")
        
        notif_text = QLabel("INFO: Lab Komputer B2 akan ditutup pada pukul 14:00 untuk maintenance harian.")
        notif_text.setObjectName("notif_text")
        notif_text.setWordWrap(True)
        
        dismiss_btn = QPushButton("✕")
        dismiss_btn.setObjectName("dismiss_btn")
        dismiss_btn.setCursor(Qt.PointingHandCursor)
        dismiss_btn.setFixedSize(24, 24)
        dismiss_btn.clicked.connect(lambda: self.notif_banner.hide())
        
        notif_layout.addWidget(notif_icon)
        notif_layout.addWidget(notif_text, 1)
        notif_layout.addWidget(dismiss_btn)
        
        footer = QWidget()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 0, 24, 0)
        
        contact_lbl = QLabel("📧 admin@kampus.ac.id  |  📞 (0370) 123-456  |  ❓ FAQ & Bantuan")
        contact_lbl.setObjectName("footer_contact")
        
        refresh_lbl = QLabel("AUTO-REFRESH ON")
        refresh_lbl.setStyleSheet("color: #cfbcff; font-weight: bold; background-color: transparent;")
        
        footer_layout.addWidget(contact_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(refresh_lbl)
        
        self.main_layout.addWidget(self.notif_banner)
        self.main_layout.addWidget(footer)

    def load_stylesheet(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

    def toggle_theme(self):
        theme_manager.toggle()
        self.apply_theme()
    
    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
        
        if theme_manager.is_dark:
            self.theme_btn.setText("🌙")
            self.theme_btn.setToolTip("Beralih ke Light Mode")
        else:
            self.theme_btn.setText("☀️")
            self.theme_btn.setToolTip("Beralih ke Dark Mode")
