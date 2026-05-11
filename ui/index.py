from PySide6.QtCore import QTimer
from PySide6.QtCore import QDateTime
import os
from functools import partial
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QLineEdit, QComboBox, 
                               QFrame, QGridLayout, QScrollArea)
from PySide6.QtCore import Qt

# Impor komponen kustom dari utils
from utils.components import CubeWidget
from utils.mode import theme_manager
from ui.detail_ruangan import DetailRuanganPopup

class StatusRuanganView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReservasiKampus - Status Ruangan Real-Time")
        
        # Main Widget & Layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
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
        # Memberikan margin vertikal sedikit lebih lega agar tidak terlalu sesak
        header_layout.setContentsMargins(24, 12, 24, 12)
        header_layout.setSpacing(16)
        
        # ─── Sisi Kiri: Logo & Judul ───
        left_layout = QHBoxLayout()
        left_layout.setSpacing(12)
        
        # Tambahkan ikon logo menggunakan emoji (bisa diganti icon SVG nantinya)
        logo_label = QLabel("🏢") 
        logo_label.setStyleSheet("font-size: 20px; background-color: transparent;")
        
        title_label = QLabel("ReservasiKampus")
        title_label.setObjectName("header_title")
        
        # Penambahan alignment vertikal agar semua text sejajar rapi di tengah
        left_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)
        left_layout.addWidget(title_label, alignment=Qt.AlignVCenter)
        # ─── Sisi Kanan: Theme Toggle, Jam Real-Time & Login ───
        right_layout = QHBoxLayout()
        right_layout.setSpacing(14)
        
        # Theme Toggle Button
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("theme_toggle")
        self.theme_btn.setToolTip("Toggle Dark/Light Mode")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        
        # Label Waktu (Sekarang berjalan real-time)
        self.time_label = QLabel()
        self.time_label.setObjectName("header_time")
        self.update_time() # Set waktu inisial agar tidak kosong saat baru dirender
        
        # Setup QTimer agar jam berjalan (update setiap 1000ms / 1 detik)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        # Tombol Login
        login_btn = QPushButton("Login")
        login_btn.setObjectName("login_btn")
        login_btn.setCursor(Qt.PointingHandCursor)
        
        # Alignment vertikal untuk elemen interaktif
        right_layout.addWidget(self.theme_btn, alignment=Qt.AlignVCenter)
        right_layout.addWidget(self.time_label, alignment=Qt.AlignVCenter)
        right_layout.addWidget(login_btn, alignment=Qt.AlignVCenter)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch() # Pendorong agar layout menempel ke ujung kiri dan kanan
        header_layout.addLayout(right_layout)
        
        self.main_layout.addWidget(header)

    def update_time(self):
        """Fungsi untuk mengupdate label waktu secara real-time ke format Bahasa Indonesia."""
        current_time = QDateTime.currentDateTime()
        
        # Format nama hari
        hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        nama_hari = hari[current_time.date().dayOfWeek() - 1]
        
        # Format nama bulan
        bulan = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        nama_bulan = bulan[current_time.date().month()]
        
        tanggal = current_time.date().day()
        tahun = current_time.date().year()
        waktu = current_time.toString("HH:mm:ss")
        
        # Format akhir: "Senin, 12 Mei 2025 | 09:34:22"
        self.time_label.setText(f"{nama_hari}, {tanggal:02d} {nama_bulan} {tahun} | {waktu}")

    def create_filter_section(self):
        filter_widget = QWidget()
        filter_widget.setObjectName("filter_section")
        filter_widget.setStyleSheet("#filter_section { background-color: transparent; }")
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(24, 16, 24, 16)
        filter_layout.setSpacing(12)
        
        # Stats Container
        self.stats_widget = QWidget()
        self.stats_widget.setObjectName("stats_container")
        self.stats_widget.setStyleSheet("#stats_container { background-color: transparent; }")
        stats_layout = QHBoxLayout(self.stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)
        
        self.stat_labels = {}
        
        def create_stat_chip(color, key):
            chip = QFrame()
            chip.setProperty("class", "stat_chip")
            chip.setFixedSize(44, 44) # Make it square
            
            l = QVBoxLayout(chip)
            l.setContentsMargins(2, 4, 2, 4)
            l.setSpacing(2)
            
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            
            count_lbl = QLabel("0")
            count_lbl.setStyleSheet("font-size: 14px; font-weight: bold; background-color: transparent;")
            count_lbl.setAlignment(Qt.AlignCenter)
            
            self.stat_labels[key] = count_lbl
            
            l.addWidget(dot, alignment=Qt.AlignHCenter)
            l.addWidget(count_lbl, alignment=Qt.AlignHCenter)
            return chip
            
        stats_layout.addWidget(create_stat_chip("#22C55E", "Tersedia"))
        stats_layout.addWidget(create_stat_chip("#EF4444", "Digunakan"))
        stats_layout.addWidget(create_stat_chip("#F59E0B", "Terbooking"))
        stats_layout.addWidget(create_stat_chip("#6B7280", "Nonaktif"))
        
        filter_layout.addWidget(self.stats_widget)
        filter_layout.addStretch()
        
        # Controls
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Status: Semua", "Tersedia", "Digunakan", "Terbooking", "Nonaktif"])
        self.status_combo.setFixedWidth(150)
        
        filter_layout.addWidget(self.status_combo)
        
        self.main_layout.addWidget(filter_widget)

    def create_main_canvas(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("main_canvas")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        canvas_widget = QWidget()
        canvas_main_layout = QVBoxLayout(canvas_widget)
        canvas_main_layout.setContentsMargins(24, 16, 24, 24)
        canvas_main_layout.setSpacing(16)
        
        # Label "SEMUA RUANGAN"
        section_lbl = QLabel("SEMUA RUANGAN")
        section_lbl.setObjectName("section_label")
        canvas_main_layout.addWidget(section_lbl)
        
        # Grid untuk kartu
        grid_container = QWidget()
        self.canvas_layout = QGridLayout(grid_container)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_layout.setSpacing(16)

        # Fetch data from Supabase
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        rooms_data = supabase.table('ruangan').select()
        
        if not rooms_data:
            rooms_data = []
        
        # Hitung statistik & kumpulkan gedung/lantai unik
        counts = {"Tersedia": 0, "Digunakan": 0, "Terbooking": 0, "Nonaktif": 0}
        gedung_set = set()
        lantai_set = set()
        
        self.rooms_raw = []  # Simpan data mentah untuk popup
        rooms = []
        for r in rooms_data:
            name = r.get('nama', 'Unknown')
            gedung = r.get('gedung', 'Unknown')
            lantai = r.get('lantai', 0)
            kapasitas = r.get('kapasitas', 0)
            status = r.get('status', 'Tersedia')
            
            gedung_set.add(gedung)
            lantai_set.add(lantai)
            
            # Update hitungan status
            if status in counts:
                counts[status] += 1
            elif status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
                counts["Nonaktif"] += 1
            elif status in ("Dosen",):
                counts["Terbooking"] += 1
            
            # Tentukan badge
            badge_class = "badge_available"
            if status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
                badge_class = "badge_unavailable"
            elif status == "Digunakan":
                badge_class = "badge_in_use"
            elif status in ("Terbooking", "Dosen"):
                badge_class = "badge_booked"
                
            rooms.append((name, status, badge_class))
            self.rooms_raw.append(r)  # Simpan data lengkap untuk popup
        
        # Update label statistik
        if hasattr(self, 'stat_labels'):
            for text, count in counts.items():
                if text in self.stat_labels:
                    self.stat_labels[text].setText(str(count))
        
        # Update combo filter dari database
        if hasattr(self, 'status_combo'):
            self.status_combo.clear()
            self.status_combo.addItems(["Status: Semua", "Tersedia", "Digunakan", "Terbooking", "Nonaktif"])
        
        # Jika tidak ada data — tampilkan empty state yang informatif
        if not rooms:
            empty_icon = QLabel("📭")
            empty_icon.setAlignment(Qt.AlignCenter)
            empty_icon.setStyleSheet("font-size: 48px; background-color: transparent; padding-top: 40px;")
            
            empty_title = QLabel("Tidak Ada Ruangan Ditemukan")
            empty_title.setAlignment(Qt.AlignCenter)
            empty_title.setStyleSheet("font-size: 18px; font-weight: 700; background-color: transparent; padding: 8px;")
            
            empty_desc = QLabel("Data ruangan belum tersedia atau tidak ada yang cocok dengan filter.\nCoba ubah kriteria pencarian Anda.")
            empty_desc.setAlignment(Qt.AlignCenter)
            empty_desc.setWordWrap(True)
            empty_desc.setStyleSheet("font-size: 13px; color: #6b5e8a; background-color: transparent;")
            
            self.canvas_layout.addWidget(empty_icon, 0, 0)
            self.canvas_layout.addWidget(empty_title, 1, 0)
            self.canvas_layout.addWidget(empty_desc, 2, 0)
        
        # Buat kartu: Sesuai referensi gambar
        self.cards = []
        import json
        for i, (name, status, badge_class) in enumerate(rooms):
            r = self.rooms_raw[i]
            kapasitas = r.get('kapasitas', 0)
            gedung = r.get('gedung', '-')
            lantai = r.get('lantai', '-')
            # Data dummy jika di database masih kosong (NULL)

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
            is_dark = theme_manager.is_dark
            title_color = "#F9FAFB" if is_dark else "#1F2937"
            title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {title_color}; background-color: transparent;")
            
            badge_lbl = QLabel(status.upper())
            badge_lbl.setAlignment(Qt.AlignCenter)
            # Style badge sesuai gambar
            if status == "Tersedia":
                badge_lbl.setStyleSheet("background-color: #F0FDF4; color: #15803D; border-radius: 6px; padding: 4px 8px; font-size: 10px; font-weight: 700;")
            elif status == "Digunakan":
                badge_lbl.setStyleSheet("background-color: #FEF2F2; color: #DC2626; border-radius: 6px; padding: 4px 8px; font-size: 10px; font-weight: 700;")
            else:
                badge_lbl.setStyleSheet("background-color: #F3F4F6; color: #4B5563; border-radius: 6px; padding: 4px 8px; font-size: 10px; font-weight: 700;")
                
            top_row.addWidget(title_lbl)
            top_row.addStretch()
            top_row.addWidget(badge_lbl)
            card_layout.addLayout(top_row)
            
            # 2. Subtitle
            subtitle_lbl = QLabel(f"Gedung {gedung} • Lantai {lantai} • Kapasitas {kapasitas}")
            subtitle_color = "#9CA3AF" if is_dark else "#6B7280"
            subtitle_lbl.setStyleSheet(f"font-size: 12px; color: {subtitle_color}; background-color: transparent;")
            card_layout.addWidget(subtitle_lbl)
            
            # 3. Kubus 3D (Tengah)
            cube_color = "#22C55E"
            if status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
                cube_color = "#9CA3AF"
            elif status == "Digunakan":
                cube_color = "#EF4444"
            elif status in ("Terbooking", "Dosen"):
                cube_color = "#F59E0B"
                
            cube_widget = CubeWidget(cube_color)
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
                fas_lbl.setStyleSheet("background-color: #F3E8FF; color: #6B21A8; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 600;")
                chips_row.addWidget(fas_lbl)
            chips_row.addStretch()
            card_layout.addLayout(chips_row)
            

            

            
            # Buat kartu bisa diklik → buka popup detail
            card.mousePressEvent = partial(self._on_card_clicked, index=i)
            
            self.cards.append(card)

            
        # Susun grid
        self.adjust_grid_columns()
        
        canvas_main_layout.addWidget(grid_container)
        canvas_main_layout.addStretch()
            
        self.scroll_area.setWidget(canvas_widget)
        self.main_layout.addWidget(self.scroll_area)



    def _on_card_clicked(self, event, index):
        """Membuka popup detail ruangan saat kartu diklik."""
        if index < len(self.rooms_raw):
            room_data = self.rooms_raw[index]
            popup = DetailRuanganPopup(room_data, parent=self)
            popup.exec()

    def adjust_grid_columns(self):
        """Menyusun ulang kartu ruangan dalam grid berdasarkan lebar window."""
        if not hasattr(self, 'cards') or not self.cards:
            return
            
        width = self.scroll_area.width()
        # Jika lebar belum terhitung (misal saat awal), gunakan lebar window
        if width <= 0:
            width = self.width()
            
        # Tentukan jumlah kolom (Gunakan 2 kolom di ukuran kecil agar jadi 2x2)
        if width < 500:
            cols = 2
        else:
            cols = max(2, (width - 48) // 320)

        
        # Bersihkan layout lama (tanpa menghapus widget)
        for i in reversed(range(self.canvas_layout.count())):
            self.canvas_layout.takeAt(i)
            
        # Susun ulang
        for i, card in enumerate(self.cards):
            row = i // cols
            col = i % cols
            self.canvas_layout.addWidget(card, row, col)

    def resizeEvent(self, event):
        """Event bawaan yang dipanggil saat window di-resize."""
        super().resizeEvent(event)
        self.adjust_grid_columns()



    def create_footer(self):
        footer_container = QVBoxLayout()
        footer_container.setSpacing(0)
        
        # ── Notification Banner (dismissable) ──
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
        
        # ── Footer utama ──
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
        
        # Tambahkan ke main layout
        self.main_layout.addWidget(self.notif_banner)
        self.main_layout.addWidget(footer)

    def load_stylesheet(self):
        """Memuat stylesheet dari ThemeManager sesuai tema aktif."""
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

    
    def toggle_theme(self):
        """Toggle antara dark dan light mode."""
        theme_manager.toggle()
        self.apply_theme()
    
    def apply_theme(self):
        """Terapkan tema dari ThemeManager dan update ikon toggle."""
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
        
        # Update ikon tombol toggle
        if theme_manager.is_dark:
            self.theme_btn.setText("🌙")
            self.theme_btn.setToolTip("Beralih ke Light Mode")
        else:
            self.theme_btn.setText("☀️")
            self.theme_btn.setToolTip("Beralih ke Dark Mode")
