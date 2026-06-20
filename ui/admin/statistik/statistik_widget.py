from collections import Counter
from datetime import datetime, timedelta, date
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton
)
from PySide6.QtGui import QColor, QCursor

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from api.supabase import get_supabase_client
from utils.mode import theme_manager

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

class StatistikWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatistikWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_dark = theme_manager.is_dark
        self.all_data = []
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        # Title and Subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        self.lbl_title = QLabel("Statistik Reservasi")
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 900;")
        title_layout.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel("Overview peminjaman seluruh waktu (All-Time)")
        self.lbl_subtitle.setStyleSheet("font-size: 14px; color: #64748b;")
        title_layout.addWidget(self.lbl_subtitle)
        
        root.addLayout(title_layout)

        # KPI Container
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)
        self.lbl_total_res = self._create_kpi_card(kpi_layout, "Total Reservasi", "0", "📅", "#6366f1")
        self.lbl_approved = self._create_kpi_card(kpi_layout, "Disetujui", "0", "✅", "#10b981")
        self.lbl_rejected = self._create_kpi_card(kpi_layout, "Ditolak/Dibatalkan", "0", "❌", "#ef4444")
        root.addLayout(kpi_layout)

        # Charts Container - Row 1
        chart_layout_top = QHBoxLayout()
        chart_layout_top.setSpacing(20)
        
        # Bar Chart Frame (Top 5 Ruangan)
        bar_frame = QFrame()
        bar_frame.setObjectName("ChartFrame")
        bar_frame.setStyleSheet("QFrame#ChartFrame { background: rgba(100, 116, 139, 0.05); border-radius: 16px; border: 1px solid rgba(100, 116, 139, 0.1); }")
        bar_layout = QVBoxLayout(bar_frame)
        bar_layout.setContentsMargins(10, 10, 10, 10)
        self.bar_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.bar_canvas.setStyleSheet("background: transparent;")
        bar_layout.addWidget(self.bar_canvas)
        chart_layout_top.addWidget(bar_frame, stretch=2)

        # Pie Chart Frame (Status)
        pie_frame = QFrame()
        pie_frame.setObjectName("ChartFrame")
        pie_frame.setStyleSheet("QFrame#ChartFrame { background: rgba(100, 116, 139, 0.05); border-radius: 16px; border: 1px solid rgba(100, 116, 139, 0.1); }")
        pie_layout = QVBoxLayout(pie_frame)
        pie_layout.setContentsMargins(10, 10, 10, 10)
        self.pie_canvas = MplCanvas(self, width=4, height=4, dpi=100)
        self.pie_canvas.setStyleSheet("background: transparent;")
        pie_layout.addWidget(self.pie_canvas)
        chart_layout_top.addWidget(pie_frame, stretch=1)

        root.addLayout(chart_layout_top)
        
        # Charts Container - Row 2 (Hari Teramai)
        self.current_date = datetime.now().date()
        
        hari_frame = QFrame()
        hari_frame.setObjectName("ChartFrame")
        hari_frame.setStyleSheet("QFrame#ChartFrame { background: rgba(100, 116, 139, 0.05); border-radius: 16px; border: 1px solid rgba(100, 116, 139, 0.1); }")
        hari_layout = QVBoxLayout(hari_frame)
        hari_layout.setContentsMargins(16, 16, 16, 16)
        hari_layout.setSpacing(10)
        
        hari_header = QHBoxLayout()
        self.lbl_hari_title = QLabel("Hari Teramai (Berdasarkan Minggu)")
        self.lbl_hari_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        self.btn_prev_week = QPushButton("<")
        self.btn_prev_week.setFixedSize(32, 32)
        self.btn_prev_week.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_prev_week.setStyleSheet("background: #6366f1; color: white; border-radius: 8px; font-weight: bold; font-size: 16px;")
        self.btn_prev_week.clicked.connect(self._prev_week)
        
        self.lbl_week_range = QLabel()
        self.lbl_week_range.setAlignment(Qt.AlignCenter)
        self.lbl_week_range.setStyleSheet("font-weight: bold; font-size: 14px; color: #6366f1; padding: 0 10px;")
        self._update_week_label()
        
        self.btn_next_week = QPushButton(">")
        self.btn_next_week.setFixedSize(32, 32)
        self.btn_next_week.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_next_week.setStyleSheet("background: #6366f1; color: white; border-radius: 8px; font-weight: bold; font-size: 16px;")
        self.btn_next_week.clicked.connect(self._next_week)
        
        hari_header.addWidget(self.lbl_hari_title)
        hari_header.addStretch()
        hari_header.addWidget(self.btn_prev_week)
        hari_header.addWidget(self.lbl_week_range)
        hari_header.addWidget(self.btn_next_week)
        
        hari_layout.addLayout(hari_header)
        
        self.hari_canvas = MplCanvas(self, width=9, height=3, dpi=100)
        self.hari_canvas.setStyleSheet("background: transparent;")
        hari_layout.addWidget(self.hari_canvas)
        
        root.addWidget(hari_frame)
        
        self.apply_theme(self.is_dark)

    def _create_kpi_card(self, parent_layout, title, value, icon_text, accent_color):
        frame = QFrame()
        frame.setObjectName("StatKpiCard")
        frame.setStyleSheet(
            f"QFrame#StatKpiCard {{ background: rgba(100, 116, 139, 0.05); border-radius: 12px; border-bottom: 3px solid {accent_color}; }}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        
        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #94a3b8; background: transparent;")
        vbox.addWidget(lbl_title)
        
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {accent_color}; background: transparent;")
        vbox.addWidget(lbl_val)
        
        layout.addLayout(vbox)
        layout.addStretch()
        
        icon = QLabel(icon_text)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(54, 54)
        icon.setStyleSheet(f"font-size: 28px; background: #20{accent_color[1:]}; border-radius: 12px; color: {accent_color};")
        layout.addWidget(icon, alignment=Qt.AlignVCenter)
        
        parent_layout.addWidget(frame)
        return lbl_val

    def _prev_week(self):
        self.current_date -= timedelta(days=7)
        self._update_week_label()
        self._update_hari_chart()

    def _next_week(self):
        self.current_date += timedelta(days=7)
        self._update_week_label()
        self._update_hari_chart()

    def _update_week_label(self):
        start_of_week = self.current_date - timedelta(days=self.current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        fmt = "%d %b %Y"
        self.lbl_week_range.setText(f"{start_of_week.strftime(fmt)} - {end_of_week.strftime(fmt)}")

    def refresh_data(self):
        try:
            db = get_supabase_client()
            data = db.table("reservasi").select("*, ruangan(nama)")
            
            if not data:
                data = []
            
            self.all_data = data

            # Update KPIs
            total_res = len(data)
            approved = sum(1 for d in data if d.get("status") == "Disetujui")
            rejected = sum(1 for d in data if d.get("status") in ["Ditolak", "Dibatalkan"])
            
            self.lbl_total_res.setText(str(total_res))
            self.lbl_approved.setText(str(approved))
            self.lbl_rejected.setText(str(rejected))

            # Process Data for Charts
            self._update_pie_chart(data)
            self._update_bar_chart(data)
            self._update_hari_chart()

        except Exception as e:
            print("Error loading statistik:", e)

    def _update_pie_chart(self, data):
        statuses = [d.get("status", "Pending") for d in data]
        counts = Counter(statuses)
        
        labels = list(counts.keys())
        sizes = list(counts.values())
        
        color_map = {
            'Disetujui': '#10b981',
            'Ditolak': '#ef4444',
            'Dibatalkan': '#f43f5e',
            'Pending': '#f59e0b',
            'Selesai': '#3b82f6'
        }
        colors = [color_map.get(s, '#8b5cf6') for s in labels]

        self.pie_canvas.axes.clear()
        text_color = '#f8fafc' if self.is_dark else '#0f172a'
        
        self.pie_canvas.fig.patch.set_alpha(0.0)
        self.pie_canvas.axes.patch.set_alpha(0.0)
        
        if not sizes:
            self.pie_canvas.axes.text(0.5, 0.5, "Belum ada data", ha='center', va='center', color=text_color)
            self.pie_canvas.axes.axis('off')
        else:
            pie_result = self.pie_canvas.axes.pie(
                sizes, labels=labels, colors=colors, autopct='%1.0f%%',
                startangle=90, pctdistance=0.75,
                textprops=dict(color=text_color, fontsize=10),
                wedgeprops=dict(width=0.4, edgecolor='none')
            )
            
            if len(pie_result) >= 3:
                autotexts = pie_result[2]
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_weight('bold')
                
        self.pie_canvas.axes.set_title("Status Reservasi", color=text_color, fontweight='bold', fontsize=14, pad=15)
        self.pie_canvas.fig.tight_layout()
        self.pie_canvas.draw()

    def _update_bar_chart(self, data):
        ruangan_names = []
        for d in data:
            r = d.get("ruangan")
            if r and isinstance(r, dict):
                ruangan_names.append(r.get("nama", "Unknown"))
        
        counts = Counter(ruangan_names)
        top_5 = counts.most_common(5)
        
        labels = [item[0] for item in top_5]
        values = [item[1] for item in top_5]

        self.bar_canvas.axes.clear()
        text_color = '#f8fafc' if self.is_dark else '#0f172a'
        bar_color = '#6366f1'
        
        self.bar_canvas.fig.patch.set_alpha(0.0)
        self.bar_canvas.axes.patch.set_alpha(0.0)
        
        if not values:
            self.bar_canvas.axes.text(0.5, 0.5, "Belum ada data", ha='center', va='center', color=text_color)
            self.bar_canvas.axes.axis('off')
        else:
            bars = self.bar_canvas.axes.bar(labels, values, color=bar_color, width=0.5, edgecolor='none')
            self.bar_canvas.axes.bar_label(bars, padding=3, color=text_color, fontweight='bold')
            
            self.bar_canvas.axes.set_title("Top 5 Ruangan Terpopuler", color=text_color, fontweight='bold', fontsize=14, pad=15)
            self.bar_canvas.axes.tick_params(colors=text_color, bottom=False, left=False)
            
            self.bar_canvas.axes.yaxis.set_visible(False)
            for spine in self.bar_canvas.axes.spines.values():
                spine.set_visible(False)
                
            self.bar_canvas.axes.grid(axis='y', linestyle='--', alpha=0.05, color=text_color)
            
        self.bar_canvas.fig.tight_layout()
        self.bar_canvas.draw()

    def _update_hari_chart(self):
        start_of_week = self.current_date - timedelta(days=self.current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        hari_counts = {
            'Senin': 0, 'Selasa': 0, 'Rabu': 0, 'Kamis': 0,
            'Jumat': 0, 'Sabtu': 0, 'Minggu': 0
        }
        hari_names = list(hari_counts.keys())
        
        for d in self.all_data:
            tanggal_str = d.get("tanggal")
            if tanggal_str:
                try:
                    dt = datetime.strptime(tanggal_str, "%Y-%m-%d").date()
                    if start_of_week <= dt <= end_of_week:
                        hari_idx = dt.weekday()
                        hari_counts[hari_names[hari_idx]] += 1
                except Exception:
                    pass

        labels = hari_names
        values = [hari_counts[h] for h in labels]
        
        self.hari_canvas.axes.clear()
        text_color = '#f8fafc' if self.is_dark else '#0f172a'
        bar_color = '#10b981' # Emerald color for this new chart
        
        self.hari_canvas.fig.patch.set_alpha(0.0)
        self.hari_canvas.axes.patch.set_alpha(0.0)
        
        # We always show 7 days even if 0
        bars = self.hari_canvas.axes.bar(labels, values, color=bar_color, width=0.6, edgecolor='none')
        
        # Only add label if value > 0
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                self.hari_canvas.axes.text(
                    bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}',
                    ha='center', va='bottom',
                    color=text_color, fontweight='bold'
                )
        
        self.hari_canvas.axes.tick_params(colors=text_color, bottom=False, left=False)
        self.hari_canvas.axes.yaxis.set_visible(False)
        for spine in self.hari_canvas.axes.spines.values():
            spine.set_visible(False)
            
        self.hari_canvas.axes.grid(axis='y', linestyle='--', alpha=0.05, color=text_color)
        self.hari_canvas.fig.tight_layout()
        self.hari_canvas.draw()

    def apply_theme(self, is_dark: bool):
        self.is_dark = is_dark
        text_h = "#f8fafc" if is_dark else "#0f172a"
        text_m = "#94a3b8" if is_dark else "#64748b"
        
        self.lbl_title.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {text_h};")
        self.lbl_subtitle.setStyleSheet(f"font-size: 14px; color: {text_m};")
        
        if self.is_dark:
            self.btn_prev_week.setStyleSheet("background: #4f46e5; color: white; border-radius: 8px; font-weight: bold; font-size: 16px;")
            self.btn_next_week.setStyleSheet("background: #4f46e5; color: white; border-radius: 8px; font-weight: bold; font-size: 16px;")
            self.lbl_week_range.setStyleSheet("font-weight: bold; font-size: 14px; color: #818cf8; padding: 0 10px;")
        else:
            self.btn_prev_week.setStyleSheet("background: #6366f1; color: white; border-radius: 8px; font-weight: bold; font-size: 16px;")
            self.btn_next_week.setStyleSheet("background: #6366f1; color: white; border-radius: 8px; font-weight: bold; font-size: 16px;")
            self.lbl_week_range.setStyleSheet("font-weight: bold; font-size: 14px; color: #4f46e5; padding: 0 10px;")
            
        self.refresh_data()
