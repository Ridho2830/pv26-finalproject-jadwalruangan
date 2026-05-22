from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QTableWidget, QTableWidgetItem, 
                                QHeaderView, QMessageBox, QFrame, QStackedWidget,
                                QProgressBar, QGridLayout, QScrollArea)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from utils.mode import theme_manager
from api.supabase import get_supabase_client
from ui.admin.ruangan.kelola_ruangan import KelolaRuanganWidget
from ui.admin.aktivitas.aktivitas_terbaru import AktivitasTerbaruWidget

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta

class RoomStatusDonutChart(QWidget):
    """Widget kustom untuk menggambar diagram donat distribusi status ruangan."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {"Tersedia": 0, "Terbooking": 0, "Terpakai": 0}
        self.colors = {
            "Tersedia": QColor("#10B981"),     # Green
            "Terbooking": QColor("#F59E0B"),   # Amber
            "Terpakai": QColor("#EF4444")      # Red
        }
        self.setMinimumSize(140, 140)
        self.setMaximumSize(180, 180)

    def set_data(self, tersedia, terbooking, terpakai):
        self.data = {
            "Tersedia": tersedia,
            "Terbooking": terbooking,
            "Terpakai": terpakai
        }
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        total = sum(self.data.values())
        rect = self.rect().adjusted(10, 10, -10, -10)
        size = min(rect.width(), rect.height())
        
        # Hitung koordinat bounding box agar diagram donat berbentuk lingkaran sempurna
        draw_rect = QRect(
            rect.x() + (rect.width() - size) // 2 + 6,
            rect.y() + (rect.height() - size) // 2 + 6,
            size - 12,
            size - 12
        )
        
        pen_width = 12
        
        if total == 0:
            # Draw placeholder ring jika tidak ada data
            painter.setPen(QPen(QColor("#3d2f6e") if theme_manager.is_dark else QColor("#e2daf0"), pen_width, Qt.SolidLine, Qt.RoundCap))
            painter.drawEllipse(draw_rect)
            
            # Teks tengah
            painter.setPen(QColor("#a899c8") if theme_manager.is_dark else QColor("#6b5e8a"))
            font = painter.font()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(draw_rect, Qt.AlignCenter, "Tidak Ada Data")
            return
            
        start_angle = 90 * 16 # Mulai dari jam 12
        
        for label, val in self.data.items():
            if val == 0:
                continue
            span_angle = int((val / total) * 360 * 16)
            
            color = self.colors.get(label, Qt.gray)
            pen = QPen(color, pen_width, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            
            # Gambar busur/arc
            painter.drawArc(draw_rect, start_angle, -span_angle)
            start_angle -= span_angle
            
        center = draw_rect.center()
        
        # Gambar teks angka total di tengah lingkaran (sedikit di atas center)
        painter.setPen(QColor("#f0e8ff") if theme_manager.is_dark else QColor("#1c1433"))
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        total_rect = QRect(draw_rect.left(), center.y() - 18, draw_rect.width(), 20)
        painter.drawText(total_rect, Qt.AlignCenter, str(total))
        
        # Label kecil di bawah angka
        lbl_rect = QRect(draw_rect.left(), center.y() + 6, draw_rect.width(), 12)
        painter.setPen(QColor("#a899c8") if theme_manager.is_dark else QColor("#6b5e8a"))
        font.setPointSize(7)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(lbl_rect, Qt.AlignCenter, "TOTAL")


class ReservationTrendChart(QWidget):
    """Widget untuk merender diagram tren reservasi menggunakan Matplotlib."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.current_period = "harian"
        self.chart_data = {}
        
    def set_data(self, period_type, data):
        self.current_period = period_type
        self.chart_data = data
        self.draw_chart()
        
    def draw_chart(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        
        is_dark = theme_manager.is_dark
        
        if is_dark:
            bg_color = "#160f2a"
            fg_color = "#f0e8ff"
            grid_color = "#2d204d"
            spine_color = "#3d2f6e"
            accent_color = "#c084fc"
            bar_color = "#9b5de5"
            label_color = "#a899c8"
        else:
            bg_color = "#ffffff"
            fg_color = "#1d1b2f"
            grid_color = "#e0d8ed"
            spine_color = "#d4c8e8"
            accent_color = "#7c3aed"
            bar_color = "#9b5de5"
            label_color = "#6b5e8a"
            
        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        labels = list(self.chart_data.keys())
        values = list(self.chart_data.values())
        
        if not labels:
            self.ax.text(0.5, 0.5, "Tidak Ada Data Reservasi", 
                         color=label_color, ha='center', va='center', 
                         transform=self.ax.transAxes, fontsize=13, fontweight='bold')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            for spine in self.ax.spines.values():
                spine.set_visible(False)
            self.canvas.draw()
            return
            
        x_pos = range(len(labels))
            
        if self.current_period in ("harian", "mingguan"):
            # Bar Chart
            bar_width = 0.5 if self.current_period == "harian" else 0.4
            bars = self.ax.bar(x_pos, values, color=bar_color, width=bar_width, 
                              zorder=3, edgecolor='none', alpha=0.9)
            
            # Gradient highlight pada bar tertinggi
            max_val = max(values) if values else 0
            for bar, val in zip(bars, values):
                if val == max_val and val > 0:
                    bar.set_color(accent_color)
                    bar.set_alpha(1.0)
                    
            # Annotasi nilai di atas bar
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    self.ax.annotate(f'{int(height)}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 5),
                                textcoords="offset points",
                                ha='center', va='bottom', color=fg_color, 
                                fontsize=9, fontweight='bold')
            
            self.ax.set_xticks(list(x_pos))
            self.ax.set_xticklabels(labels, fontsize=9)
        else:
            # Line Chart (Tahunan)
            self.ax.plot(x_pos, values, color=accent_color, marker='o', 
                        linewidth=2.5, markersize=7, zorder=3,
                        markerfacecolor=accent_color, markeredgecolor=bg_color, 
                        markeredgewidth=2)
            self.ax.fill_between(x_pos, values, color=accent_color, alpha=0.1, zorder=2)
            
            for i, val in enumerate(values):
                if val > 0:
                    self.ax.annotate(f'{int(val)}', (x_pos[i], values[i]), 
                                    textcoords="offset points", xytext=(0, 8), 
                                    ha='center', color=fg_color, fontsize=9, fontweight='bold')
            
            self.ax.set_xticks(list(x_pos))
            self.ax.set_xticklabels(labels, fontsize=9)

        # Grid styling
        self.ax.grid(True, axis='y', linestyle='--', linewidth=0.5, color=grid_color, alpha=0.7, zorder=0)
        self.ax.set_axisbelow(True)
        
        # Spine styling
        for name, spine in self.ax.spines.items():
            if name in ('top', 'right'):
                spine.set_visible(False)
            else:
                spine.set_color(spine_color)
                spine.set_linewidth(0.8)
                
        # Tick styling
        self.ax.tick_params(axis='x', colors=label_color, labelsize=9, length=0, pad=8)
        self.ax.tick_params(axis='y', colors=label_color, labelsize=9, length=0, pad=5)
        
        # Y-axis: pastikan integer
        max_y = max(values) if values else 1
        self.ax.set_ylim(bottom=0, top=max_y + max(1, int(max_y * 0.3)))
        from matplotlib.ticker import MaxNLocator
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Rotate daily labels sedikit
        if self.current_period == "harian":
            self.ax.tick_params(axis='x', rotation=15)
                
        self.figure.subplots_adjust(left=0.08, right=0.96, top=0.92, bottom=0.18)
        self.canvas.draw()


class AdminDashboardStatsWidget(QWidget):
    """Widget panel utama yang menampilkan statistik, diagram donat, tren, dan aktivitas terbaru."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 32, 32, 32)
        self.main_layout.setSpacing(24)
        
        # Inisialisasi data tren
        self.harian_data = {}
        self.mingguan_data = {}
        self.tahunan_data = {}
        
        self._build_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _build_ui(self):
        # 1. Header Title
        header_bar = QHBoxLayout()
        header_title = QLabel("Dashboard Analitik Reservasi")
        header_title.setStyleSheet("font-size: 22px; font-weight: 800; background-color: transparent;")
        header_bar.addWidget(header_title)
        self.main_layout.addLayout(header_bar)
        
        # 2. Grid KPI Cards
        self.kpi_layout = QGridLayout()
        self.kpi_layout.setSpacing(16)
        
        self.card_total_rooms = self._create_kpi_card("Total Ruangan", "0", "#9b5de5")
        self.card_available = self._create_kpi_card("Ruangan Tersedia", "0", "#10B981")
        self.card_booked = self._create_kpi_card("Ruangan Terbooking", "0", "#F59E0B")
        self.card_used = self._create_kpi_card("Ruangan Terpakai", "0", "#EF4444")
        
        self.kpi_layout.addWidget(self.card_total_rooms, 0, 0)
        self.kpi_layout.addWidget(self.card_available, 0, 1)
        self.kpi_layout.addWidget(self.card_booked, 0, 2)
        self.kpi_layout.addWidget(self.card_used, 0, 3)
        self.main_layout.addLayout(self.kpi_layout)
        
        # 3. Baris Tengah: Split Chart dan Gedung
        middle_row = QHBoxLayout()
        middle_row.setSpacing(20)
        
        # 3a. Kontainer Kiri: Utilitas Gedung
        self.util_card = QFrame()
        self.util_card.setProperty("class", "dashboard_card")
        self.util_layout = QVBoxLayout(self.util_card)
        self.util_layout.setContentsMargins(20, 20, 20, 20)
        self.util_layout.setSpacing(12)
        
        util_title = QLabel("📊 UTILITAS GEDUNG")
        util_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #6b5e8a; background-color: transparent;")
        self.util_layout.addWidget(util_title)
        
        self.util_list_layout = QVBoxLayout()
        self.util_list_layout.setSpacing(10)
        self.util_layout.addLayout(self.util_list_layout)
        self.util_layout.addStretch()
        
        # 3b. Kontainer Kanan: Chart Status
        self.chart_card = QFrame()
        self.chart_card.setProperty("class", "dashboard_card")
        chart_layout = QVBoxLayout(self.chart_card)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        chart_layout.setSpacing(12)
        
        chart_title = QLabel("🍩 PROPORSI STATUS RUANGAN")
        chart_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #6b5e8a; background-color: transparent;")
        chart_layout.addWidget(chart_title)
        
        self.donut_chart = RoomStatusDonutChart()
        
        # Legenda di bawah chart
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        legend_layout.setAlignment(Qt.AlignCenter)
        
        def create_legend_item(label, color):
            item = QWidget()
            item.setStyleSheet("background-color: transparent;")
            l = QHBoxLayout(item)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(6)
            
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #a899c8; background-color: transparent;")
            
            l.addWidget(dot)
            l.addWidget(lbl)
            return item
            
        legend_layout.addWidget(create_legend_item("Tersedia", "#10B981"))
        legend_layout.addWidget(create_legend_item("Terbooking", "#F59E0B"))
        legend_layout.addWidget(create_legend_item("Terpakai", "#EF4444"))
        
        chart_center_layout = QHBoxLayout()
        chart_center_layout.addStretch()
        chart_center_layout.addWidget(self.donut_chart)
        chart_center_layout.addStretch()
        
        chart_layout.addLayout(chart_center_layout)
        chart_layout.addLayout(legend_layout)
        chart_layout.addStretch()
        
        middle_row.addWidget(self.util_card, 3)
        middle_row.addWidget(self.chart_card, 2)
        self.main_layout.addLayout(middle_row)
        
        # 4. Baris Grafik Tren Reservasi (Matplotlib)
        self.trend_card = QFrame()
        self.trend_card.setProperty("class", "dashboard_card")
        trend_layout = QVBoxLayout(self.trend_card)
        trend_layout.setContentsMargins(20, 20, 20, 20)
        trend_layout.setSpacing(12)
        
        # Header Tren Card (Title + Toggle Buttons)
        trend_header = QHBoxLayout()
        trend_title = QLabel("📈 TREN RESERVASI RUANGAN")
        trend_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #6b5e8a; background-color: transparent;")
        trend_header.addWidget(trend_title)
        trend_header.addStretch()
        
        # Toggle Buttons
        self.current_trend_period = "harian"
        self.btn_harian = QPushButton("Harian")
        self.btn_harian.setCursor(Qt.PointingHandCursor)
        self.btn_harian.clicked.connect(lambda: self.set_trend_period("harian"))
        
        self.btn_mingguan = QPushButton("Mingguan")
        self.btn_mingguan.setCursor(Qt.PointingHandCursor)
        self.btn_mingguan.clicked.connect(lambda: self.set_trend_period("mingguan"))
        
        self.btn_tahunan = QPushButton("Tahunan")
        self.btn_tahunan.setCursor(Qt.PointingHandCursor)
        self.btn_tahunan.clicked.connect(lambda: self.set_trend_period("tahunan"))
        
        trend_header.addWidget(self.btn_harian)
        trend_header.addWidget(self.btn_mingguan)
        trend_header.addWidget(self.btn_tahunan)
        trend_layout.addLayout(trend_header)
        
        # Embed Trend Chart Widget
        self.trend_chart = ReservationTrendChart()
        trend_layout.addWidget(self.trend_chart)
        
        self.main_layout.addWidget(self.trend_card)
        
        # 5. Baris Bawah: Aktivitas Reservasi Terbaru (dari file terpisah)
        self.aktivitas_widget = AktivitasTerbaruWidget()
        self.main_layout.addWidget(self.aktivitas_widget)

    def _create_kpi_card(self, title, value, color_hex):
        card = QFrame()
        card.setProperty("class", "dashboard_card")
        card.setFixedHeight(90)
        
        l = QVBoxLayout(card)
        l.setContentsMargins(16, 12, 16, 12)
        l.setSpacing(4)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #6b5e8a; background-color: transparent;")
        
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {color_hex}; background-color: transparent;")
        
        l.addWidget(title_lbl)
        l.addWidget(val_lbl)
        
        # Simpan reference agar valuenya bisa diperbarui
        card.val_lbl = val_lbl
        return card

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def update_toggle_styles(self):
        is_dark = theme_manager.is_dark
        if is_dark:
            active_style = "background-color: rgba(147, 90, 255, 0.25); color: #ffffff; border: 1px solid #c084fc; border-radius: 6px; padding: 4px 12px; font-weight: bold; font-size: 11px;"
            inactive_style = "background-color: rgba(28, 20, 51, 0.55); color: #a899c8; border: 1px solid rgba(147, 90, 255, 0.15); border-radius: 6px; padding: 4px 12px; font-size: 11px;"
        else:
            active_style = "background-color: rgba(124, 58, 237, 0.15); color: #7c3aed; border: 1px solid #7c3aed; border-radius: 6px; padding: 4px 12px; font-weight: bold; font-size: 11px;"
            inactive_style = "background-color: #ffffff; color: #6b5e8a; border: 1px solid rgba(124, 58, 237, 0.15); border-radius: 6px; padding: 4px 12px; font-size: 11px;"
            
        self.btn_harian.setStyleSheet(active_style if self.current_trend_period == "harian" else inactive_style)
        self.btn_mingguan.setStyleSheet(active_style if self.current_trend_period == "mingguan" else inactive_style)
        self.btn_tahunan.setStyleSheet(active_style if self.current_trend_period == "tahunan" else inactive_style)

    def set_trend_period(self, period):
        self.current_trend_period = period
        self.update_toggle_styles()
        
        if period == "harian":
            data = self.harian_data
        elif period == "mingguan":
            data = self.mingguan_data
        else:
            data = self.tahunan_data
            
        self.trend_chart.set_data(period, data)

    def refresh_data(self):
        """Memuat statistik realtime dari database Supabase."""
        try:
            supabase = get_supabase_client()
            
            # 1. Fetch Rooms & Users & Reservations
            rooms = supabase.table('ruangan').select() or []
            reservations = supabase.table('reservasi').select() or []
            users = supabase.table('pengguna').select() or []
            
            # Map database records
            room_map = {r['id']: r for r in rooms}
            user_map = {u['id']: u for u in users}
            
            # 2. Count Room Statuses
            tersedia = 0
            terbooking = 0
            terpakai = 0
            
            building_counts = {} # e.g., {"Gedung A": {"total": 0, "active": 0}}
            
            for r in rooms:
                status = r.get('status', 'Tersedia')
                # Fallback format
                if status == "Digunakan" or status in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
                    status = "Terpakai"
                elif status == "Dosen":
                    status = "Terbooking"
                
                if status == "Tersedia":
                    tersedia += 1
                elif status == "Terbooking":
                    terbooking += 1
                elif status == "Terpakai":
                    terpakai += 1
                    
                # Building stats
                gedung = r.get('gedung', 'Lainnya')
                if gedung not in building_counts:
                    building_counts[gedung] = {"total": 0, "active": 0}
                building_counts[gedung]["total"] += 1
                if status in ("Terbooking", "Terpakai"):
                    building_counts[gedung]["active"] += 1
            
            # Update KPI Card Values
            self.card_total_rooms.val_lbl.setText(str(len(rooms)))
            self.card_available.val_lbl.setText(str(tersedia))
            self.card_booked.val_lbl.setText(str(terbooking))
            self.card_used.val_lbl.setText(str(terpakai))
            
            # Update Donut Chart
            self.donut_chart.set_data(tersedia, terbooking, terpakai)
            
            # 3. Aggregasi Tren Reservasi (Matplotlib)
            today = datetime.now().date()
            months_id = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
            
            # 3a. Harian (7 Hari Terakhir)
            dates_list = [today - timedelta(days=i) for i in range(6, -1, -1)]
            self.harian_data = {}
            for d in dates_list:
                display_str = f"{d.day} {months_id[d.month - 1]}"
                self.harian_data[display_str] = 0
                
            # 3b. Mingguan (4 Minggu Terakhir)
            self.mingguan_data = {
                "3 Mgg Lalu": 0,
                "2 Mgg Lalu": 0,
                "1 Mgg Lalu": 0,
                "Mgg Ini": 0
            }
            
            # 3c. Tahunan (12 Bulan di Tahun Ini)
            current_year = today.year
            self.tahunan_data = {m: 0 for m in months_id}
            
            for res in reservations:
                res_date_str = res.get('tanggal')
                if res_date_str:
                    try:
                        res_date = datetime.strptime(res_date_str, "%Y-%m-%d").date()
                        # Harian
                        if res_date in dates_list:
                            display_str = f"{res_date.day} {months_id[res_date.month - 1]}"
                            self.harian_data[display_str] += 1
                        
                        # Mingguan
                        days_diff = (today - res_date).days
                        if 0 <= days_diff < 7:
                            self.mingguan_data["Mgg Ini"] += 1
                        elif 7 <= days_diff < 14:
                            self.mingguan_data["1 Mgg Lalu"] += 1
                        elif 14 <= days_diff < 21:
                            self.mingguan_data["2 Mgg Lalu"] += 1
                        elif 21 <= days_diff < 28:
                            self.mingguan_data["3 Mgg Lalu"] += 1
                            
                        # Tahunan
                        if res_date.year == current_year:
                            month_name = months_id[res_date.month - 1]
                            self.tahunan_data[month_name] += 1
                    except Exception as ex:
                        pass
                        
            # Update Trend Chart data
            self.set_trend_period(self.current_trend_period)
            
            # 4. Render Building Progress Bars
            self.clear_layout(self.util_list_layout)
            
            # Urutkan berdasarkan nama gedung
            for b_name in sorted(building_counts.keys()):
                stats = building_counts[b_name]
                tot = stats["total"]
                act = stats["active"]
                pct = int((act / tot) * 100) if tot > 0 else 0
                
                b_row = QWidget()
                b_row.setStyleSheet("background-color: transparent;")
                b_layout = QHBoxLayout(b_row)
                b_layout.setContentsMargins(0, 4, 0, 4)
                
                b_label = QLabel(f"{b_name} ({act}/{tot} Ruang)")
                b_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #f0e8ff; background-color: transparent;")
                b_label.setFixedWidth(160)
                
                pbar = QProgressBar()
                pbar.setRange(0, 100)
                pbar.setValue(pct)
                pbar.setTextVisible(False)
                pbar.setFixedHeight(8)
                pbar.setStyleSheet("""
                    QProgressBar {
                        background-color: rgba(147, 90, 255, 0.08);
                        border: none;
                        border-radius: 4px;
                    }
                    QProgressBar::chunk {
                        background-color: #9b5de5;
                        border-radius: 4px;
                    }
                """)
                
                pct_label = QLabel(f"{pct}%")
                pct_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #c084fc; background-color: transparent;")
                pct_label.setFixedWidth(30)
                pct_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                b_layout.addWidget(b_label)
                b_layout.addWidget(pbar)
                b_layout.addWidget(pct_label)
                self.util_list_layout.addWidget(b_row)
                
            # 5. Render Aktivitas Terbaru (pass data yang sudah di-fetch)
            self.aktivitas_widget.refresh_data(reservations, room_map, user_map)
                
        except Exception as e:
            print(f"Error loading stats dashboard: {e}")

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
        if hasattr(self, 'trend_chart'):
            self.update_toggle_styles()
            self.trend_chart.draw_chart()


class AdminDashboard(QWidget):
    """Parent Admin Window yang membungkus Sidebar dan QStackedWidget konten."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main Layout (Horizontal split: Sidebar and Content Area)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Stacked Widget untuk konten area
        self.stacked_widget = QStackedWidget()
        self.stats_widget = AdminDashboardStatsWidget()
        self.rooms_widget = KelolaRuanganWidget(self)
        
        # Wrap Stats Widget in a Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.stats_widget)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        
        self.stacked_widget.addWidget(self.scroll_area) # Index 0
        self.stacked_widget.addWidget(self.rooms_widget) # Index 1
        
        self._build_sidebar()
        self._build_content_area()
        
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(24, 32, 24, 32)
        sidebar_layout.setSpacing(12)
        
        # Logo & App Title
        logo_layout = QHBoxLayout()
        logo_lbl = QLabel("🏢")
        logo_lbl.setStyleSheet("font-size: 24px; background-color: transparent;")
        
        title_lbl = QLabel("Admin Panel")
        title_lbl.setObjectName("sidebar_title_lbl")
        title_lbl.setStyleSheet("background-color: transparent;")
        
        logo_layout.addWidget(logo_lbl)
        logo_layout.addWidget(title_lbl)
        logo_layout.addStretch()
        sidebar_layout.addLayout(logo_layout)
        
        subtitle_lbl = QLabel("ReservasiKampus")
        subtitle_lbl.setObjectName("sidebar_subtitle_lbl")
        subtitle_lbl.setStyleSheet("background-color: transparent; margin-bottom: 24px;")
        sidebar_layout.addWidget(subtitle_lbl)
        
        # Navigasi Buttons
        self.nav_stats_btn = QPushButton("📊 Dashboard Statistik")
        self.nav_stats_btn.setCursor(Qt.PointingHandCursor)
        self.nav_stats_btn.setFixedHeight(40)
        self.nav_stats_btn.setObjectName("nav_btn")
        self.nav_stats_btn.setProperty("class", "active")
        self.nav_stats_btn.clicked.connect(self.show_stats_view)
        sidebar_layout.addWidget(self.nav_stats_btn)
        
        self.nav_ruangan_btn = QPushButton("📂 Kelola Ruangan")
        self.nav_ruangan_btn.setCursor(Qt.PointingHandCursor)
        self.nav_ruangan_btn.setFixedHeight(40)
        self.nav_ruangan_btn.setObjectName("nav_btn")
        self.nav_ruangan_btn.clicked.connect(self.show_rooms_view)
        sidebar_layout.addWidget(self.nav_ruangan_btn)
        
        sidebar_layout.addStretch()
        
        # Logout Button
        self.logout_btn = QPushButton("🚪 Keluar / Logout")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setFixedHeight(40)
        self.logout_btn.setObjectName("logout_btn")
        self.logout_btn.clicked.connect(self.handle_logout)
        sidebar_layout.addWidget(self.logout_btn)
        
        self.main_layout.addWidget(self.sidebar)

    def _build_content_area(self):
        self.main_layout.addWidget(self.stacked_widget)

    def show_stats_view(self):
        self.nav_stats_btn.setProperty("class", "active")
        self.nav_ruangan_btn.setProperty("class", "")
        # Refresh stylesheet properties
        self.nav_stats_btn.style().unpolish(self.nav_stats_btn)
        self.nav_stats_btn.style().polish(self.nav_stats_btn)
        self.nav_ruangan_btn.style().unpolish(self.nav_ruangan_btn)
        self.nav_ruangan_btn.style().polish(self.nav_ruangan_btn)
        
        self.stacked_widget.setCurrentIndex(0)
        self.stats_widget.refresh_data()

    def show_rooms_view(self):
        self.nav_stats_btn.setProperty("class", "")
        self.nav_ruangan_btn.setProperty("class", "active")
        # Refresh stylesheet properties
        self.nav_stats_btn.style().unpolish(self.nav_stats_btn)
        self.nav_stats_btn.style().polish(self.nav_stats_btn)
        self.nav_ruangan_btn.style().unpolish(self.nav_ruangan_btn)
        self.nav_ruangan_btn.style().polish(self.nav_ruangan_btn)
        
        self.stacked_widget.setCurrentIndex(1)
        self.rooms_widget.refresh_data()

    def refresh_data(self):
        # Dipanggil saat window dibuka utama
        self.show_stats_view()

    def handle_logout(self):
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'switch_to_public'):
            parent_widget.switch_to_public()

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
