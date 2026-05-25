"""
Admin Dashboard - ReservasiKampus
UI/UX improvements:
  - Clean 3-zone layout: fixed sidebar | scrollable main | slide-in detail panel
  - Impactful KPI strip with color-coded accents
  - Polished RoomCard with status ring indicator
  - Smooth detail panel with animated CubeWidget
  - Consistent dark/light theming via a central palette dict
  - Better typography hierarchy & spacing
"""

from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal, Slot, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy,
    QLayout, QLayoutItem, QLineEdit, QGraphicsOpacityEffect,
    QSpacerItem, QApplication,
)
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QCursor, QPixmap
from utils.components import CubeWidget
from api.supabase import get_supabase_client
from ui.chatbot import ChatbotDialog

# ──────────────────────────────────────────────
#  PALETTE  (single source of truth)
# ──────────────────────────────────────────────
LIGHT = {
    "bg":           "#f0f4ff",
    "surface":      "#ffffff",
    "surface2":     "#f8faff",
    "border":       "#e4e9f5",
    "sidebar_bg":   "#1c1854",
    "sidebar_act":  "#312e81",
    "text_h":       "#0f172a",
    "text_b":       "#334155",
    "text_m":       "#64748b",
    "text_s":       "#94a3b8",
    "accent":       "#4f46e5",
    "accent_light": "#ede9fe",
    "warn_bg":      "#fff7ed",
    "warn_text":    "#c2410c",
    "warn_border":  "#fed7aa",
}
DARK = {
    "bg":           "#0a0f1e",
    "surface":      "#111827",
    "surface2":     "#1e293b",
    "border":       "#1e293b",
    "sidebar_bg":   "#050a14",
    "sidebar_act":  "#1e1b4b",
    "text_h":       "#f1f5f9",
    "text_b":       "#cbd5e1",
    "text_m":       "#94a3b8",
    "text_s":       "#475569",
    "accent":       "#818cf8",
    "accent_light": "#1e1b4b",
    "warn_bg":      "#1c0f00",
    "warn_text":    "#fb923c",
    "warn_border":  "#431407",
}

STATUS_META = {
    "Tersedia": {
        "color": "#22c55e", "bg": "rgba(34,197,94,0.12)",
        "text": "#14532d", "label": "Tersedia",
    },
    "Digunakan": {
        "color": "#ef4444", "bg": "rgba(239,68,68,0.12)",
        "text": "#7f1d1d", "label": "Digunakan",
    },
    "Dosen": {
        "color": "#3b82f6", "bg": "rgba(59,130,246,0.12)",
        "text": "#1e3a8a", "label": "Dosen Booked",
    },
    "Konflik": {
        "color": "#f97316", "bg": "rgba(249,115,22,0.12)",
        "text": "#7c2d12", "label": "Konflik!",
    },
}

def normalize_status(raw: str) -> str:
    raw = raw or "Tersedia"
    if raw in ("Digunakan", "Terpakai"):  return "Digunakan"
    if raw in ("Dosen", "Terbooking"):    return "Dosen"
    if raw == "Konflik":                  return "Konflik"
    return "Tersedia"


# ──────────────────────────────────────────────
#  FLOW LAYOUT  (unchanged logic, kept compact)
# ──────────────────────────────────────────────
class FlowLayout(QLayout):
    def addWidget(self, w): super().addWidget(w)
    def __init__(self, parent=None, margin=0, hSpacing=12, vSpacing=12):
        super().__init__(parent)
        if margin != -1: self.setContentsMargins(margin, margin, margin, margin)
        self._hSpace, self._vSpace, self.itemList = hSpacing, vSpacing, []
    def __del__(self):
        item = self.takeAt(0)
        while item: item = self.takeAt(0)
    def addItem(self, item):            self.itemList.append(item)
    def horizontalSpacing(self):        return self._hSpace
    def verticalSpacing(self):          return self._vSpace
    def count(self):                    return len(self.itemList)
    def itemAt(self, i):                return self.itemList[i] if 0 <= i < len(self.itemList) else None
    def takeAt(self, i):                return self.itemList.pop(i) if 0 <= i < len(self.itemList) else None
    def expandingDirections(self):      return Qt.Orientations(0)
    def hasHeightForWidth(self):        return True
    def heightForWidth(self, w):        return self.doLayout(QRect(0, 0, w, 0), True)
    def setGeometry(self, rect):
        super().setGeometry(rect); self.doLayout(rect, False)
    def sizeHint(self):                 return self.minimumSize()
    def minimumSize(self):
        s = QSize()
        for item in self.itemList: s = s.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return s + QSize(m.left()+m.right(), m.top()+m.bottom())
    def doLayout(self, rect, testOnly):
        m  = self.contentsMargins()
        er = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y, lineH = er.x(), er.y(), 0
        for item in self.itemList:
            nX = x + item.sizeHint().width() + self._hSpace
            if nX - self._hSpace > er.right() and lineH > 0:
                x, y = er.x(), y + lineH + self._vSpace
                nX = x + item.sizeHint().width() + self._hSpace
                lineH = 0
            if not testOnly: item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = nX
            lineH = max(lineH, item.sizeHint().height())
        return y + lineH - rect.y() + m.bottom()


# ──────────────────────────────────────────────
#  ROOM CARD
# ──────────────────────────────────────────────
class RoomCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, room_data: dict, parent=None):
        super().__init__(parent)
        self.room_data  = room_data
        self.status_key = normalize_status(room_data.get("status", "Tersedia"))
        self.meta       = STATUS_META[self.status_key]
        self.is_dark    = False

        self.setObjectName("RoomCard")
        self.setFixedSize(210, 190)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        # ── Status ring dot + status pill ──
        top = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {self.meta['color']}; font-size: 10px; background: transparent;")
        pill = QLabel(self.meta["label"])
        pill.setStyleSheet(
            f"color: {self.meta['text']}; background: {self.meta['bg']};"
            f"border-radius: 6px; padding: 2px 8px; font-size: 10px; font-weight: 700;"
        )
        top.addWidget(dot)
        top.addWidget(pill)
        top.addStretch()

        # Cube (small, top-right)
        self.cube = CubeWidget(self.meta["color"], should_animate=False)
        self.cube.setFixedSize(36, 36)
        top.addWidget(self.cube)
        layout.addLayout(top)

        # ── Room name ──
        name = QLabel(self.room_data.get("nama", "Unknown"))
        name.setObjectName("CardName")
        name.setStyleSheet("font-size: 15px; font-weight: 800; background: transparent;")
        layout.addWidget(name)

        layout.addSpacing(2)

        # ── Info rows ──
        kap = self.room_data.get("kapasitas", 0)
        fas = self.room_data.get("fasilitas", "-")

        def info_row(icon, text):
            h = QHBoxLayout()
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("font-size: 11px; background: transparent; min-width:16px;")
            lbl_text = QLabel(text)
            lbl_text.setObjectName("CardMeta")
            lbl_text.setStyleSheet("font-size: 11px; background: transparent;")
            lbl_text.setWordWrap(True)
            h.addWidget(lbl_icon)
            h.addWidget(lbl_text)
            h.addStretch()
            return h

        layout.addLayout(info_row("👥", f"{kap} kursi"))
        layout.addLayout(info_row("🔧", fas[:28] + ("…" if len(fas) > 28 else "")))
        layout.addStretch()

        # ── Action button for Konflik ──
        if self.status_key == "Konflik":
            btn = QPushButton("⚡ Selesaikan Konflik")
            btn.setStyleSheet(
                "QPushButton{background:#f97316;color:white;border:none;border-radius:6px;"
                "padding:5px 8px;font-weight:700;font-size:10px;}"
                "QPushButton:hover{background:#ea580c;}"
            )
            layout.addWidget(btn)

    def update_theme(self, is_dark: bool):
        self.is_dark = is_dark
        p = DARK if is_dark else LIGHT
        border_color = self.meta["color"] if self.status_key == "Konflik" else p["border"]
        self.setStyleSheet(f"""
            QFrame#RoomCard {{
                background: {p['surface']};
                border: 1.5px solid {border_color};
                border-radius: 14px;
            }}
            QFrame#RoomCard:hover {{
                border-color: {self.meta['color']};
                background: {p['surface2']};
            }}
            QLabel#CardName  {{ color: {p['text_h']}; }}
            QLabel#CardMeta  {{ color: {p['text_m']}; }}
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.room_data)
        super().mousePressEvent(event)


# ──────────────────────────────────────────────
#  SIDEBAR NAV BUTTON
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
        self._active = v; self._apply()

    def _apply(self):
        if self._active:
            self.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,0.15);
                    color: white; font-weight: 700;
                    text-align: left; border: none;
                    border-left: 3px solid #818cf8;
                    border-radius: 0px;
                    padding-left: 20px; font-size: 13px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #94a3b8; font-weight: 500;
                    text-align: left; border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                    padding-left: 20px; font-size: 13px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.07);
                    color: #e2e8f0;
                }
            """)


# ──────────────────────────────────────────────
#  KPI CARD  (wider strip design)
# ──────────────────────────────────────────────
class KpiCard(QFrame):
    def __init__(self, title: str, value: str, icon: str, accent: str = "#4f46e5", parent=None):
        super().__init__(parent)
        self.accent = accent
        self.setObjectName("KpiCard")
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
        icon_lbl.setStyleSheet(
            f"font-size:18px; background:{accent}22; border-radius:8px;"
            f"padding:4px 6px; color:{accent};"
        )
        top.addWidget(self.lbl_title)
        top.addStretch()
        top.addWidget(icon_lbl)
        layout.addLayout(top)

        self.lbl_value = QLabel(value)
        self.lbl_value.setObjectName("KpiValue")
        self.lbl_value.setStyleSheet(f"font-size:28px; font-weight:900; color:{accent}; background:transparent;")
        layout.addWidget(self.lbl_value)

        # accent bottom bar
        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {accent}, stop:1 transparent); border-radius:2px;")
        layout.addWidget(bar)

    def set_value(self, v: str):
        self.lbl_value.setText(v)

    def apply_palette(self, p: dict):
        self.setStyleSheet(f"""
            QFrame#KpiCard {{
                background: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 14px;
            }}
            QLabel#KpiTitle {{
                color: {p['text_m']};
                font-size: 11px; font-weight: 600;
                background: transparent;
            }}
        """)


# ──────────────────────────────────────────────
#  DETAIL PANEL
# ──────────────────────────────────────────────
class RoomDetailPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailPanel")
        self.setFixedWidth(290)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        self.lbl_header = QLabel("Detail Ruangan")
        self.lbl_header.setObjectName("PanelHeader")
        root.addWidget(self.lbl_header)

        # Cube
        self.cube_wrap = QHBoxLayout()
        root.addLayout(self.cube_wrap)

        # Name
        self.lbl_name = QLabel("—")
        self.lbl_name.setObjectName("PanelName")
        self.lbl_name.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_name)

        # Status pill
        self.lbl_status = QLabel("—")
        self.lbl_status.setObjectName("PanelStatus")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFixedHeight(28)
        root.addWidget(self.lbl_status, alignment=Qt.AlignCenter)

        root.addSpacing(8)

        # Info section
        self.info_frame = QFrame()
        self.info_frame.setObjectName("InfoBox")
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(8)

        self.lbl_info_label = QLabel("PENGHUNI SAAT INI")
        self.lbl_info_label.setObjectName("InfoLabel")
        info_layout.addWidget(self.lbl_info_label)

        self.lbl_user = QLabel("—")
        self.lbl_user.setObjectName("InfoUser")
        self.lbl_user.setWordWrap(True)
        info_layout.addWidget(self.lbl_user)

        root.addWidget(self.info_frame)

        # Schedule section
        sched_frame = QFrame()
        sched_frame.setObjectName("InfoBox")
        sched_layout = QVBoxLayout(sched_frame)
        sched_layout.setContentsMargins(14, 12, 14, 12)
        sched_layout.setSpacing(6)

        lbl_s = QLabel("JADWAL BERIKUTNYA")
        lbl_s.setObjectName("InfoLabel")
        sched_layout.addWidget(lbl_s)

        self.lbl_sched = QLabel("14:00 – 16:00\nMateri: Kuliah Umum AI")
        self.lbl_sched.setObjectName("InfoUser")
        self.lbl_sched.setWordWrap(True)
        sched_layout.addWidget(self.lbl_sched)
        root.addWidget(sched_frame)

        root.addStretch()

        # Book button
        self.btn_book = QPushButton("📅  Buat Reservasi")
        self.btn_book.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_book.setFixedHeight(40)
        root.addWidget(self.btn_book)

    def load(self, data: dict, is_dark: bool):
        status = normalize_status(data.get("status", "Tersedia"))
        meta   = STATUS_META[status]
        p      = DARK if is_dark else LIGHT

        self.lbl_name.setText(data.get("nama", "Unknown"))

        self.lbl_status.setText(f"  {meta['label']}  ")
        self.lbl_status.setStyleSheet(
            f"color:{meta['text']}; background:{meta['bg']};"
            f"border-radius:12px; font-weight:700; font-size:12px;"
        )

        self.lbl_user.setText(
            "Ahmad Gunawan\nHIMA – Kegiatan Mahasiswa"
            if status != "Tersedia" else "Ruangan kosong"
        )

        # Rebuild cube
        for i in reversed(range(self.cube_wrap.count())):
            w = self.cube_wrap.itemAt(i).widget()
            if w: w.deleteLater()
        cube = CubeWidget(meta["color"], should_animate=True)
        cube.setFixedSize(120, 120)
        self.cube_wrap.addWidget(cube, alignment=Qt.AlignCenter)

        self.apply_palette(p)

    def apply_palette(self, p: dict):
        accent = p["accent"]
        self.setStyleSheet(f"""
            QFrame#DetailPanel {{
                background: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 16px;
            }}
            QLabel#PanelHeader {{
                color: {p['text_m']}; font-size: 11px;
                font-weight: 700; letter-spacing: 1px;
                background: transparent;
                text-transform: uppercase;
            }}
            QLabel#PanelName {{
                color: {p['text_h']}; font-size: 22px;
                font-weight: 900; background: transparent;
            }}
            QFrame#InfoBox {{
                background: {p['surface2']};
                border: 1px solid {p['border']};
                border-radius: 10px;
            }}
            QLabel#InfoLabel {{
                color: {p['text_s']}; font-size: 10px;
                font-weight: 700; letter-spacing: 1px;
                background: transparent;
            }}
            QLabel#InfoUser {{
                color: {p['text_b']}; font-size: 12px;
                font-weight: 600; background: transparent;
            }}
            QPushButton {{
                background: {accent}; color: white;
                border: none; border-radius: 10px;
                font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{
                background: {p['accent_light']};
                color: {accent};
            }}
        """)


# ──────────────────────────────────────────────
#  ADMIN DASHBOARD
# ──────────────────────────────────────────────
class AdminDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.setObjectName("AdminDashboard")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._build_sidebar(root)
        self._build_main(root)
        self._build_detail_panel(root)

        self.refresh_data()
        self.apply_theme()

    # ─── SIDEBAR ────────────────────────────────
    def _build_sidebar(self, root):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)

        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(0, 28, 0, 24)
        sb.setSpacing(2)

        # Logo / Brand
        brand = QLabel("  🏛  ReservasiKampus")
        brand.setStyleSheet(
            "color: white; font-size: 13px; font-weight: 800;"
            "letter-spacing: 0.5px; padding: 0 20px 20px 8px;"
            "background: transparent;"
        )
        sb.addWidget(brand)

        # Profile
        prof = QFrame()
        prof.setStyleSheet(
            "background: rgba(255,255,255,0.08); border-radius: 12px;"
            "margin: 0 12px; padding: 10px;"
        )
        pf = QHBoxLayout(prof)
        pf.setContentsMargins(10, 8, 10, 8)
        ava = QLabel("👨‍🏫")
        ava.setStyleSheet(
            "font-size: 20px; background: rgba(255,255,255,0.15);"
            "border-radius: 14px; padding: 4px 6px;"
        )
        vp = QVBoxLayout()
        vp.addWidget(QLabel("Budi Santoso", styleSheet="color:white;font-weight:700;font-size:12px;background:transparent;"))
        vp.addWidget(QLabel("Admin / Dosen",  styleSheet="color:#818cf8;font-size:10px;background:transparent;"))
        pf.addWidget(ava)
        pf.addLayout(vp)
        pf.addStretch()
        sb.addWidget(prof)
        sb.addSpacing(16)

        # Quick actions
        btn_new = QPushButton("＋  Reservasi Baru")
        btn_new.setCursor(QCursor(Qt.PointingHandCursor))
        btn_new.setFixedHeight(38)
        btn_new.setStyleSheet(
            "QPushButton{background:#4f46e5;color:white;border:none;border-radius:10px;"
            "font-weight:700;font-size:12px;margin:0 12px;}"
            "QPushButton:hover{background:#4338ca;}"
        )
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

        # Divider label
        div = QLabel("  NAVIGASI")
        div.setStyleSheet("color:#475569;font-size:9px;font-weight:700;letter-spacing:2px;background:transparent;padding-left:20px;")
        sb.addWidget(div)
        sb.addSpacing(4)

        # Nav items
        self.nav_buttons = []
        nav_items = [
            ("🏠", "Dashboard", True),
            ("📅", "Jadwal Ruangan", False),
            ("📋", "Peminjaman Saya", False),
            ("🕒", "Riwayat", False),
            ("⚙️", "Pengaturan", False),
        ]
        for icon, label, active in nav_items:
            btn = NavButton(icon, label, active)
            sb.addWidget(btn)
            self.nav_buttons.append(btn)

        sb.addStretch()

        # Logout
        btn_out = QPushButton("⎋  Keluar")
        btn_out.setCursor(QCursor(Qt.PointingHandCursor))
        btn_out.setFixedHeight(38)
        btn_out.setStyleSheet(
            "QPushButton{background:transparent;color:#ef4444;border:1px solid #ef444430;"
            "border-radius:10px;font-weight:600;font-size:12px;margin:0 12px;}"
            "QPushButton:hover{background:#ef444415;}"
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
        ml.setSpacing(16)

        # ── Top Bar ──
        top = QHBoxLayout()

        self.lbl_page = QLabel("Dashboard")
        self.lbl_page.setObjectName("PageTitle")
        top.addWidget(self.lbl_page)
        top.addStretch()

        self.lbl_time = QLabel("🕒 --:--")
        self.lbl_time.setObjectName("TimeLabel")
        top.addWidget(self.lbl_time)

        # Update clock
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

        # ── KPI Strip ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_rooms   = KpiCard("Total Ruangan",      "0",  "🏢", "#4f46e5")
        self.kpi_active  = KpiCard("Reservasi Aktif",    "0",  "📅", "#0ea5e9")
        self.kpi_konflik = KpiCard("Konflik Menunggu",   "0",  "⚠️", "#f97316")
        self.kpi_users   = KpiCard("Total Pengguna",     "0",  "👥", "#22c55e")

        for kpi in (self.kpi_rooms, self.kpi_active, self.kpi_konflik, self.kpi_users):
            kpi_row.addWidget(kpi)
        ml.addLayout(kpi_row)

        # ── Warning Banner ──
        self.warn_banner = QFrame()
        self.warn_banner.setObjectName("WarnBanner")
        wb = QHBoxLayout(self.warn_banner)
        wb.setContentsMargins(16, 10, 16, 10)
        self.lbl_warn = QLabel()
        self.lbl_warn.setObjectName("WarnText")
        btn_fix = QPushButton("Lihat Konflik →")
        btn_fix.setCursor(QCursor(Qt.PointingHandCursor))
        btn_fix.setStyleSheet(
            "QPushButton{background:#f97316;color:white;border:none;border-radius:8px;"
            "padding:5px 14px;font-weight:700;font-size:11px;}"
            "QPushButton:hover{background:#ea580c;}"
        )
        wb.addWidget(self.lbl_warn)
        wb.addStretch()
        wb.addWidget(btn_fix)
        ml.addWidget(self.warn_banner)
        self.warn_banner.hide()

        # ── Rooms List Header ──
        list_hdr = QHBoxLayout()
        self.lbl_section = QLabel("Status Ruangan Hari Ini")
        self.lbl_section.setObjectName("SectionTitle")
        list_hdr.addWidget(self.lbl_section)
        list_hdr.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Cari ruangan…")
        self.search.setFixedWidth(200)
        self.search.setFixedHeight(32)
        self.search.setObjectName("SearchBox")
        self.search.textChanged.connect(self._filter_cards)
        list_hdr.addWidget(self.search)

        # Legend
        legend = QLabel("  ●  Tersedia    ●  Digunakan    ●  Dosen    ●  Konflik")
        legend.setObjectName("Legend")
        legend.setStyleSheet(
            "font-size: 10px; color: transparent; background: transparent;"
            "background-clip: text;"
        )
        # Simple colored legend
        legend2 = QLabel()
        legend2.setObjectName("Legend")
        legend2.setText(
            "<span style='color:#22c55e'>●</span> Tersedia &nbsp;"
            "<span style='color:#ef4444'>●</span> Digunakan &nbsp;"
            "<span style='color:#3b82f6'>●</span> Dosen &nbsp;"
            "<span style='color:#f97316'>●</span> Konflik"
        )
        legend2.setTextFormat(Qt.RichText)
        legend2.setStyleSheet("font-size:10px; background:transparent;")
        list_hdr.addWidget(legend2)
        ml.addLayout(list_hdr)

        # ── Room Cards Scroll ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background:transparent;")

        self.flow_container = QWidget()
        self.flow_container.setStyleSheet("background:transparent;")
        self.flow_layout = FlowLayout(self.flow_container, margin=0, hSpacing=12, vSpacing=12)
        self.scroll.setWidget(self.flow_container)
        ml.addWidget(self.scroll)

        root.addWidget(self.main_frame, stretch=1)

    # ─── DETAIL PANEL ───────────────────────────
    def _build_detail_panel(self, root):
        self.detail = RoomDetailPanel()
        root.addWidget(self.detail)

    # ─── HELPERS ────────────────────────────────
    def _tick_clock(self):
        from datetime import datetime
        self.lbl_time.setText(f"🕒 {datetime.now().strftime('%H:%M')}")

    def _filter_cards(self, text: str):
        text = text.lower().strip()
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                nama = w.room_data.get("nama", "").lower()
                w.setVisible(text == "" or text in nama)

    # ─── THEME ──────────────────────────────────
    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()

    def apply_theme(self):
        p = DARK if self.is_dark else LIGHT

        # Root background
        self.setStyleSheet(f"QWidget#AdminDashboard {{ background: {p['bg']}; }}")

        # Sidebar
        self.sidebar.setStyleSheet(f"""
            QFrame#Sidebar {{
                background: {p['sidebar_bg']};
                border-right: 1px solid rgba(255,255,255,0.05);
            }}
        """)

        # Main frame
        self.main_frame.setStyleSheet(f"QFrame#MainFrame {{ background: {p['bg']}; }}")

        # Top bar labels
        self.lbl_page.setStyleSheet(
            f"font-size:20px; font-weight:900; color:{p['text_h']}; background:transparent;"
        )
        self.lbl_time.setStyleSheet(
            f"font-size:12px; color:{p['text_m']}; background:transparent; margin-right:8px;"
        )

        # Theme button
        icon  = "☀️" if self.is_dark else "🌙"
        label = " Terang" if self.is_dark else " Gelap"
        self.btn_theme.setText(icon + label)
        self.btn_theme.setStyleSheet(f"""
            QPushButton#ThemeBtn {{
                background: {p['surface']};
                color: {p['text_b']};
                border: 1px solid {p['border']};
                border-radius: 10px;
                font-weight: 600; font-size: 11px;
            }}
            QPushButton#ThemeBtn:hover {{
                background: {p['surface2']};
            }}
        """)

        # Section title
        self.lbl_section.setStyleSheet(
            f"font-size:15px; font-weight:800; color:{p['text_h']}; background:transparent;"
        )

        # Search
        self.search.setStyleSheet(f"""
            QLineEdit#SearchBox {{
                background: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 8px;
                padding: 0 10px;
                color: {p['text_b']};
                font-size: 12px;
            }}
        """)

        # Warn banner
        self.warn_banner.setStyleSheet(f"""
            QFrame#WarnBanner {{
                background: {p['warn_bg']};
                border: 1px solid {p['warn_border']};
                border-radius: 10px;
            }}
        """)
        self.lbl_warn.setStyleSheet(f"color:{p['warn_text']};font-weight:700;font-size:12px;background:transparent;")

        # KPI cards
        for kpi in (self.kpi_rooms, self.kpi_active, self.kpi_konflik, self.kpi_users):
            kpi.apply_palette(p)

        # Room cards
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), "update_theme"):
                item.widget().update_theme(self.is_dark)

        # Detail panel
        self.detail.apply_palette(p)

    # ─── DATA ───────────────────────────────────
    def refresh_data(self):
        # Clear existing cards
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        try:
            supabase = get_supabase_client()
            rooms = supabase.table("ruangan").select() or []
            users = supabase.table("pengguna").select() or []

            # Demo: force first room to Konflik
            if len(rooms) >= 1:
                rooms[0]["status"] = "Konflik"
                rooms[0]["nama"]   = "LAB-AI-01"

            konflik_count = 0
            for room in rooms:
                card = RoomCard(room)
                card.clicked.connect(self.show_room_detail)
                self.flow_layout.addWidget(card)
                if normalize_status(room.get("status", "")) == "Konflik":
                    konflik_count += 1

            self.kpi_rooms.set_value(str(len(rooms)))
            self.kpi_users.set_value(str(len(users)))
            self.kpi_active.set_value("87")
            self.kpi_konflik.set_value(str(konflik_count))

            if konflik_count > 0:
                self.warn_banner.show()
                self.lbl_warn.setText(f"⚡  {konflik_count} konflik prioritas membutuhkan perhatian Anda")
            else:
                self.warn_banner.hide()

            if rooms:
                self.show_room_detail(rooms[0])

        except Exception as e:
            print("Error loading dashboard data:", e)

    # ─── SIGNALS ────────────────────────────────
    def show_room_detail(self, data: dict):
        self.detail.load(data, self.is_dark)

    def show_chatbot(self):
        if not hasattr(self, "_chatbot") or self._chatbot is None:
            self._chatbot = ChatbotDialog(self)
        self._chatbot.show()
        self._chatbot.raise_()
        self._chatbot.activateWindow()

    def handle_logout(self):
        p = self.parent()
        if p and hasattr(p, "switch_to_public"):
            p.switch_to_public()