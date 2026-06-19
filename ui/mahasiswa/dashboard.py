# ui/mahasiswa/dashboard_mahasiswa.py
"""
Mahasiswa Dashboard - ReservasiKampus
Desain mengikuti admin dashboard:
  - Sidebar dengan profile card, nav buttons, logout
  - Dashboard page dengan KPI cards, kalender bulanan
  - Sub-pages: Peminjaman Saya, Riwayat
"""

from PySide6.QtCore import Qt, QRect, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy,
    QStackedWidget, QGridLayout, QComboBox
)
from PySide6.QtGui import QColor, QFont, QPainter, QCursor, QPixmap, QBrush

from api.supabase import get_supabase_client
from utils.chatbot import ChatbotDialog
from utils.detail_hari import DayDetailPopup
from utils.mode import theme_manager

from ui.mahasiswa.peminjaman.reservasi_mahasiswa import ReservasiMahasiswaPage
from ui.mahasiswa.riwayat.riwayat_peminjaman import RiwayatPeminjamanPage
from ui.mahasiswa.peminjaman.dialog_reservasi import DialogBuatReservasi


# ──────────────────────────────────────────────
#  HELPER: Avatar inisial
# ──────────────────────────────────────────────
def make_initial_avatar(initials: str, size: int, bg_color: str = "#22c55e") -> QPixmap:
    result = QPixmap(size, size)
    result.fill(Qt.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing, True)

    painter.setBrush(QBrush(QColor(bg_color)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)

    font = QFont("Arial", int(size * 0.38), QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("white"))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter, initials.upper()[:2])

    painter.end()
    return result


# ──────────────────────────────────────────────
#  NAV BUTTON
# ──────────────────────────────────────────────
class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, active=False, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self._active = active
        self.setCheckable(False)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(40)
        self._apply()

    def set_active(self, v: bool):
        self._active = v
        self._apply()

    def _apply(self):
        self.setProperty("class", "active" if self._active else "")
        self.style().unpolish(self)
        self.style().polish(self)


# ──────────────────────────────────────────────
#  KPI CARD
# ──────────────────────────────────────────────
class KpiCard(QFrame):
    def __init__(self, title: str, value: str, icon: str, accent: str = "#22c55e", parent=None):
        super().__init__(parent)
        self.accent = accent
        self.setObjectName("KpiCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(96)
        self.setMinimumWidth(170)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        top = QHBoxLayout()
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("KpiTitle")
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setStyleSheet(f"font-size:18px; background:#20{accent[1:]}; border-radius:8px; color:{accent};")
        top.addWidget(self.lbl_title)
        top.addStretch()
        top.addWidget(icon_lbl, alignment=Qt.AlignVCenter)
        layout.addLayout(top)

        self.lbl_value = QLabel(value)
        self.lbl_value.setObjectName("KpiValue")
        self.lbl_value.setStyleSheet(f"font-size:28px; font-weight:900; color:{accent}; background:transparent;")
        layout.addWidget(self.lbl_value)

        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {accent}, stop:1 transparent); border-radius:2px;")
        layout.addWidget(bar)

    def set_value(self, v: str):
        self.lbl_value.setText(v)


# ──────────────────────────────────────────────
#  CLICKABLE FRAME
# ──────────────────────────────────────────────
class ClickableFrame(QFrame):
    clicked = Signal()
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit()


# ──────────────────────────────────────────────
#  MAHASISWA DASHBOARD
# ──────────────────────────────────────────────
class MahasiswaPage(QWidget):
    def __init__(self, pengguna_id, pengguna_nama, parent=None):
        super().__init__(parent)

        # Simpan referensi MainWindow
        self.main_window = parent

        self.pengguna_id = pengguna_id
        self.pengguna_nama = pengguna_nama
        self.is_dark = theme_manager.is_dark

        self.setObjectName("AdminDashboard")
        self.setAttribute(Qt.WA_StyledBackground, True)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._build_sidebar(root)

        self.content_stack = QStackedWidget()
        root.addWidget(self.content_stack, stretch=1)

        self._build_dashboard_page()
        self._build_peminjaman_page()
        self._build_riwayat_page()

        self.refresh_data()
        self.apply_theme()

    # ─── BUILD PAGES ────────────────────────────
    def _build_dashboard_page(self):
        self.dashboard_page = QWidget()
        dash_layout = QHBoxLayout(self.dashboard_page)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        dash_layout.setSpacing(0)

        self._build_main(dash_layout)

        self.content_stack.addWidget(self.dashboard_page)

    def _build_peminjaman_page(self):
        self.peminjaman_page = ReservasiMahasiswaPage(
            pengguna_id=self.pengguna_id,
            pengguna_nama=self.pengguna_nama
        )
        self.content_stack.addWidget(self.peminjaman_page)

    def _build_riwayat_page(self):
        self.riwayat_page = RiwayatPeminjamanPage(
            pengguna_id=self.pengguna_id,
            pengguna_nama=self.pengguna_nama
        )
        self.content_stack.addWidget(self.riwayat_page)

    def switch_page(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)

        if index < self.content_stack.count():
            self.content_stack.setCurrentIndex(index)

        if index == 0:
            self.refresh_data()
        elif index == 1 and hasattr(self, 'peminjaman_page'):
            self.peminjaman_page.refresh_data()
        elif index == 2 and hasattr(self, 'riwayat_page'):
            self.riwayat_page.refresh_data()

    # ─── SIDEBAR ────────────────────────────────
    def _build_sidebar(self, root):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)

        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(0, 28, 0, 24)
        sb.setSpacing(2)

        # ── Brand ──
        brand = QLabel("  🏛  ReservasiKampus")
        brand.setStyleSheet(
            "color: white; font-size: 13px; font-weight: 800;"
            "letter-spacing: 0.5px; padding: 0 20px 20px 8px;"
            "background: transparent;"
        )
        sb.addWidget(brand)

        # ── Profile ──
        prof = QFrame()
        prof.setObjectName("MhsProfile")
        prof.setStyleSheet(
            "QFrame#MhsProfile {"
            "  background: rgba(255,255,255,0.07);"
            "  border: 1px solid rgba(255,255,255,0.1);"
            "  border-radius: 14px;"
            "  margin: 0 12px;"
            "}"
        )

        pf = QHBoxLayout(prof)
        pf.setContentsMargins(12, 10, 12, 10)
        pf.setSpacing(10)

        # Avatar
        AVATAR_SIZE = 40
        self.lbl_profile_ava = QLabel()
        self.lbl_profile_ava.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.lbl_profile_ava.setAlignment(Qt.AlignCenter)

        initials = "".join(w[0] for w in self.pengguna_nama.split() if w)[:2] or "MH"
        avatar = make_initial_avatar(initials, AVATAR_SIZE, bg_color="#22c55e")
        self.lbl_profile_ava.setPixmap(avatar)
        self.lbl_profile_ava.setText("")

        # Text
        vp = QVBoxLayout()
        vp.setSpacing(1)
        vp.setContentsMargins(0, 0, 0, 0)

        self.lbl_profile_name = QLabel(self.pengguna_nama)
        self.lbl_profile_name.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #f1f5f9; background: transparent;"
        )
        self.lbl_profile_name.setMaximumWidth(120)

        self.lbl_profile_role = QLabel("Mahasiswa")
        self.lbl_profile_role.setStyleSheet(
            "font-size: 10px; font-weight: 500; color: #94a3b8; background: transparent;"
        )
        self.lbl_profile_role.setMaximumWidth(120)

        vp.addWidget(self.lbl_profile_name)
        vp.addWidget(self.lbl_profile_role)

        pf.addWidget(self.lbl_profile_ava)
        pf.addLayout(vp)
        pf.addStretch()

        sb.addWidget(prof)
        sb.addSpacing(16)

        # ── Quick actions ──
        btn_new = QPushButton("＋  Reservasi Baru")
        btn_new.setCursor(QCursor(Qt.PointingHandCursor))
        btn_new.setFixedHeight(38)
        btn_new.setStyleSheet(
            "QPushButton{background:#22c55e;color:white;border:none;border-radius:10px;"
            "font-weight:700;font-size:12px;margin:0 12px;}"
            "QPushButton:hover{background:#16a34a;}"
        )
        btn_new.clicked.connect(self._on_new_reservasi)
        sb.addWidget(btn_new)
        sb.addSpacing(4)

        btn_ai = QPushButton("🤖  Tanya Asisten AI")
        btn_ai.setCursor(QCursor(Qt.PointingHandCursor))
        btn_ai.setFixedHeight(38)
        btn_ai.setStyleSheet(
            "QPushButton{background:#0284c7;color:white;border:none;border-radius:10px;"
            "font-weight:700;font-size:12px;margin:0 12px;}"
            "QPushButton:hover{background:#0369a1;}"
        )
        btn_ai.clicked.connect(self.show_chatbot)
        sb.addWidget(btn_ai)
        sb.addSpacing(20)

        # ── Nav label ──
        div = QLabel("  NAVIGASI")
        div.setStyleSheet(
            "color:#475569;font-size:9px;font-weight:700;"
            "letter-spacing:2px;background:transparent;padding-left:20px;"
        )
        sb.addWidget(div)
        sb.addSpacing(4)

        # ── Nav buttons ──
        self.nav_buttons = []
        nav_items = [
            ("🏠", "Dashboard"),
            ("📋", "Peminjaman Saya"),
            ("📜", "Riwayat"),
        ]
        for i, (icon, label) in enumerate(nav_items):
            btn = NavButton(icon, label, active=(i == 0))
            btn.clicked.connect(lambda checked=False, idx=i: self.switch_page(idx))
            sb.addWidget(btn)
            self.nav_buttons.append(btn)

        sb.addStretch()

        # ── Logout ──
        btn_out = QPushButton("⎋  Keluar")
        btn_out.setCursor(QCursor(Qt.PointingHandCursor))
        btn_out.setFixedHeight(38)
        btn_out.setStyleSheet(
            "QPushButton{background:transparent;color:#ef4444;border:1px solid rgba(239, 68, 68, 0.3);"
            "border-radius:10px;font-weight:600;font-size:12px;margin:0 12px;}"
            "QPushButton:hover{background:rgba(239, 68, 68, 0.15);}"
        )
        btn_out.clicked.connect(self.handle_logout)
        sb.addWidget(btn_out)

        root.addWidget(self.sidebar)

    # ─── MAIN CONTENT ───────────────────────────
    def _build_main(self, root):
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        ml = QVBoxLayout(self.main_frame)
        ml.setContentsMargins(28, 20, 16, 20)
        ml.setSpacing(12)

        # Top Bar
        top = QHBoxLayout()
        self.lbl_page = QLabel("Dashboard Mahasiswa")
        self.lbl_page.setObjectName("PageTitle")
        top.addWidget(self.lbl_page)
        top.addStretch()
        self.lbl_time = QLabel("🕒 --:--")
        self.lbl_time.setObjectName("TimeLabel")
        top.addWidget(self.lbl_time)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(30_000)
        self._tick_clock()
        self.btn_theme = QPushButton()
        self.btn_theme.setObjectName("ThemeBtn")
        self.btn_theme.setFixedSize(90, 32)
        self.btn_theme.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_theme.clicked.connect(self.toggle_theme)
        top.addWidget(self.btn_theme)
        ml.addLayout(top)

        # KPI Strip
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self.kpi_rooms    = KpiCard("Total Ruangan",      "0", "🏢", "#4f46e5")
        self.kpi_active   = KpiCard("Reservasi Bln Ini",  "0", "📅", "#0ea5e9")
        self.kpi_pending  = KpiCard("Pending",            "0", "⏳", "#f97316")
        self.kpi_approved = KpiCard("Disetujui",          "0", "✅", "#22c55e")
        for kpi in (self.kpi_rooms, self.kpi_active, self.kpi_pending, self.kpi_approved):
            kpi_row.addWidget(kpi)
        ml.addLayout(kpi_row)

        # Filters
        from datetime import date
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tahun:"))
        self.cb_year = QComboBox()
        current_year = date.today().year
        self.cb_year.addItems([str(y) for y in range(current_year - 1, current_year + 3)])
        self.cb_year.setCurrentText(str(current_year))
        self.cb_year.currentIndexChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.cb_year)

        filter_layout.addSpacing(16)

        filter_layout.addWidget(QLabel("Bulan:"))
        self.cb_month = QComboBox()
        months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        self.cb_month.addItems(months)
        self.cb_month.setCurrentIndex(date.today().month - 1)
        self.cb_month.currentIndexChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.cb_month)

        filter_layout.addStretch()
        ml.addLayout(filter_layout)

        # Calendar Container
        self.calendar_bg = QFrame()
        self.calendar_bg.setStyleSheet(
            "QFrame { background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; }"
        )
        cal_layout = QVBoxLayout(self.calendar_bg)
        cal_layout.setContentsMargins(0, 0, 0, 0)
        cal_layout.setSpacing(0)

        # Header Hari
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        days_of_week = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        for d in days_of_week:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                "font-weight: 800; font-size: 11px; padding: 12px 0; color: #94a3b8;"
                "border-right: 1px solid rgba(255,255,255,0.05);"
                "border-bottom: 1px solid rgba(255,255,255,0.1);"
            )
            header_layout.addWidget(lbl)

        cal_layout.addWidget(header_widget)

        # Grid Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background:transparent; }")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background:transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(0)

        self.scroll.setWidget(self.grid_container)
        cal_layout.addWidget(self.scroll, stretch=1)

        ml.addWidget(self.calendar_bg, stretch=1)
        root.addWidget(self.main_frame, stretch=1)

        self.current_month_reservations = []
        self.current_month_dates = []

    # ─── HELPERS ────────────────────────────────
    def _tick_clock(self):
        from datetime import datetime
        self.lbl_time.setText(f"🕒 {datetime.now().strftime('%H:%M')}")

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self.clear_layout(item.layout())

    # ─── THEME ──────────────────────────────────
    def toggle_theme(self):
        theme_manager.toggle()
        self.is_dark = theme_manager.is_dark
        self.apply_theme()

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

        icon = "🌙" if self.is_dark else "☀️"
        label = " Terang" if self.is_dark else " Gelap"
        self.btn_theme.setText(icon + label)

    # ─── DATA & RENDERING ───────────────────────
    def refresh_data(self):
        try:
            year = int(self.cb_year.currentText())
            month = self.cb_month.currentIndex() + 1

            import calendar
            cal = calendar.Calendar(firstweekday=6)
            self.current_month_dates = cal.monthdatescalendar(year, month)

            supabase = get_supabase_client()
            rooms = supabase.table("ruangan").select() or []

            self.room_map = {r["id"]: r for r in rooms}

            self.kpi_rooms.set_value(str(len(set([r["nama"] for r in rooms]))))

            # Fetch reservations for this user in the date range
            start_date = self.current_month_dates[0][0]
            end_date = self.current_month_dates[-1][-1]

            reservations = supabase.table("reservasi").select(
                "*,pengguna(role,nama)",
                f"pengguna_id=eq.{self.pengguna_id}&tanggal=gte.{start_date}&tanggal=lte.{end_date}"
            )
            self.current_month_reservations = reservations if isinstance(reservations, list) else []

            # Count KPIs
            total_this_month = len(self.current_month_reservations)
            pending_count = sum(1 for r in self.current_month_reservations if r.get("status") == "Pending")
            approved_count = sum(1 for r in self.current_month_reservations if r.get("status") == "Disetujui")

            self.kpi_active.set_value(str(total_this_month))
            self.kpi_pending.set_value(str(pending_count))
            self.kpi_approved.set_value(str(approved_count))

            self._render_monthly_calendar(month)

        except Exception as e:
            print("Error loading mahasiswa dashboard data:", e)

    def _render_monthly_calendar(self, target_month: int):
        self.clear_layout(self.grid_layout)

        for row, week in enumerate(self.current_month_dates):
            self.grid_layout.setRowStretch(row, 1)
            for col, dt in enumerate(week):
                self.grid_layout.setColumnStretch(col, 1)

                cell = ClickableFrame()
                cell.setStyleSheet(
                    "QFrame { border-right: 1px solid rgba(255,255,255,0.05);"
                    "border-bottom: 1px solid rgba(255,255,255,0.05); background: transparent; }"
                    "QFrame:hover { background: rgba(255,255,255,0.03); }"
                )

                cell.setMinimumHeight(120)

                cell_layout = QVBoxLayout(cell)
                cell_layout.setContentsMargins(4, 8, 4, 8)
                cell_layout.setSpacing(4)

                # Date label
                lbl_day = QLabel(str(dt.day))
                lbl_day.setAlignment(Qt.AlignHCenter)
                if dt.month == target_month:
                    lbl_day.setStyleSheet("font-weight: bold; font-size: 13px; color: #f1f5f9; border: none;")
                else:
                    lbl_day.setStyleSheet("font-size: 13px; color: #475569; border: none;")
                cell_layout.addWidget(lbl_day)

                day_res = [r for r in self.current_month_reservations
                           if r.get("tanggal") == dt.strftime("%Y-%m-%d")]
                day_res.sort(key=lambda x: x.get("jam_mulai", "00:00"))

                # Room status summary for this day
                from datetime import date
                today_date = date.today()

                rooms_booked = set()
                for r in day_res:
                    rooms_booked.add(str(r.get("ruangan_id")))

                total_rooms = len(self.room_map)
                c_booked = len(rooms_booked)
                c_tersedia = total_rooms - c_booked

                summary_html = (
                    f"<span style='color: #22c55e;'>●</span> {c_tersedia} &nbsp; "
                    f"<span style='color: #f97316;'>●</span> {c_booked}"
                )
                summary_lbl = QLabel(summary_html)
                summary_lbl.setStyleSheet(
                    "font-size: 11px; font-weight: 700; color: #94a3b8;"
                    "padding-bottom: 4px; border: none; background: transparent;"
                )
                summary_lbl.setAlignment(Qt.AlignCenter)
                cell_layout.addWidget(summary_lbl)

                # Events area
                events_area = QWidget()
                events_area.setStyleSheet("border: none; background: transparent;")
                ev_layout = QVBoxLayout(events_area)
                ev_layout.setContentsMargins(0, 0, 0, 0)
                ev_layout.setSpacing(4)

                max_events = 4
                for i, res in enumerate(day_res):
                    if i >= max_events:
                        more_lbl = QLabel(f"+{len(day_res) - max_events} lagi")
                        more_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; border: none;")
                        ev_layout.addWidget(more_lbl)
                        break

                    ruangan = next((v for k, v in self.room_map.items()
                                    if str(k) == str(res.get("ruangan_id"))), {})
                    nama_ruang = ruangan.get("nama", "Unknown")
                    jam = res.get("jam_mulai", "")[:5]
                    status = res.get("status", "Pending")

                    # Color by status
                    if status == "Disetujui":
                        bg_color = "rgba(34,197,94,0.2)"
                        text_color = "#86efac"
                        if not self.is_dark:
                            bg_color = "rgba(34,197,94,0.15)"
                            text_color = "#14532d"
                    elif status == "Pending":
                        bg_color = "rgba(249,115,22,0.2)"
                        text_color = "#fdba74"
                        if not self.is_dark:
                            bg_color = "rgba(249,115,22,0.15)"
                            text_color = "#7c2d12"
                    elif status == "Ditolak":
                        bg_color = "rgba(239,68,68,0.2)"
                        text_color = "#fca5a5"
                        if not self.is_dark:
                            bg_color = "rgba(239,68,68,0.15)"
                            text_color = "#991b1b"
                    else:
                        bg_color = "rgba(107,114,128,0.2)"
                        text_color = "#9ca3af"
                        if not self.is_dark:
                            bg_color = "rgba(107,114,128,0.15)"
                            text_color = "#374151"

                    btn = QPushButton(f"{jam} {nama_ruang}")
                    btn.setCursor(QCursor(Qt.PointingHandCursor))
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {bg_color};
                            color: {text_color};
                            border: none;
                            border-radius: 4px;
                            padding: 3px 6px;
                            font-size: 10px;
                            font-weight: 700;
                            text-align: left;
                        }}
                        QPushButton:hover {{
                            background: rgba(255,255,255,0.1);
                        }}
                    """)

                    btn.setAttribute(Qt.WA_TransparentForMouseEvents)
                    ev_layout.addWidget(btn)

                ev_layout.addStretch()
                cell_layout.addWidget(events_area, stretch=1)

                # Connect cell click
                cell.clicked.connect(lambda d=dt: self.show_day_detail(d))
                self.grid_layout.addWidget(cell, row, col)

    # ─── SIGNALS ────────────────────────────────
    def _on_new_reservasi(self):
        dialog = DialogBuatReservasi(
            pengguna_id=self.pengguna_id,
            parent=self,
        )
        if dialog.exec():
            self.refresh_data()

    def show_day_detail(self, dt):
        day_res = [r for r in self.current_month_reservations
                   if r.get("tanggal") == dt.strftime("%Y-%m-%d")]
        self.popup = DayDetailPopup(
            dt, self.room_map.values(), day_res,
            is_dark=self.is_dark, parent=self
        )
        self.popup.exec()

    def show_chatbot(self):
        if not hasattr(self, "_chatbot") or self._chatbot is None:
            self._chatbot = ChatbotDialog(self, is_dark=self.is_dark, role="Mahasiswa")
        self._chatbot.show()
        self._chatbot.raise_()
        self._chatbot.activateWindow()

    def handle_logout(self):
        """Kembali ke halaman login."""
        if self.main_window and hasattr(self.main_window, 'switch_to_login'):
            self.main_window.switch_to_login()