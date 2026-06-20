"""
Admin Dashboard - ReservasiKampus
Perbaikan utama:
  - Avatar circular beneran pakai QPainter mask (bukan border-radius CSS yg nggak works di QLabel)
  - Profile section layout lebih rapi & konsisten ukurannya
  - set_user_profile pakai ukuran yang sama (36x36) seragam
  - Fallback avatar pakai initial huruf kalau gambar nggak ada
  - Minor polish: spacing, font weight
"""

import os
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy,
    QLayout, QStackedWidget, QGridLayout
)
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QCursor, QPixmap, QBrush
from utils.components import CubeWidget
from api.supabase import get_supabase_client
from utils.chatbot import ChatbotDialog
from utils.detail_hari import DayDetailPopup

from utils.mode import theme_manager
from ui.admin.ruangan.kelola_ruangan import KelolaRuanganWidget
from ui.admin.pengguna.kelola_pengguna import KelolaPenggunaWidget
from ui.admin.reservasi.kelola_reservasi import KelolaReservasiWidget
from ui.admin.statistik.statistik_widget import StatistikWidget

STATUS_META = {
    "Tersedia": { "color": "#22c55e", "bg": "rgba(34,197,94,0.12)", "text": "#14532d", "label": "Tersedia" },
    "Digunakan": { "color": "#ef4444", "bg": "rgba(239,68,68,0.12)", "text": "#7f1d1d", "label": "Digunakan" },
    "Dosen": { "color": "#3b82f6", "bg": "rgba(59,130,246,0.12)", "text": "#1e3a8a", "label": "Dosen Booked" },
    "Konflik": { "color": "#f97316", "bg": "rgba(249,115,22,0.12)", "text": "#7c2d12", "label": "Konflik!" },
}

def normalize_status(raw: str) -> str:
    raw = raw or "Tersedia"
    if raw in ("Digunakan", "Terpakai"):  return "Digunakan"
    if raw in ("Dosen", "Terbooking"):    return "Dosen"
    if raw == "Konflik":                  return "Konflik"
    return "Tersedia"


# ──────────────────────────────────────────────
#  HELPER: buat pixmap lingkaran beneran
# ──────────────────────────────────────────────
def make_circular_pixmap(source: QPixmap, size: int) -> QPixmap:
    """
    Crop & mask pixmap jadi lingkaran sempurna.
    border-radius CSS di QLabel nggak clip pixmap,
    jadi harus pakai QPainter + QPainterPath.
    """
    scaled = source.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # crop tengah kalau aspek ratio nggak 1:1
    if scaled.width() != size or scaled.height() != size:
        x = (scaled.width()  - size) // 2
        y = (scaled.height() - size) // 2
        scaled = scaled.copy(x, y, size, size)

    result = QPixmap(size, size)
    result.fill(Qt.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()

    return result


def make_initial_avatar(initials: str, size: int, bg_color: str = "#4f46e5") -> QPixmap:
    """Fallback avatar dengan inisial huruf kalau gambar nggak ada."""
    result = QPixmap(size, size)
    result.fill(Qt.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing, True)

    # lingkaran background
    painter.setBrush(QBrush(QColor(bg_color)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)

    # teks inisial
    font = QFont("Arial", int(size * 0.38), QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("white"))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter, initials.upper()[:2])

    painter.end()
    return result


# ──────────────────────────────────────────────
#  FLOW LAYOUT
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
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(210, 190)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

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

        self.cube = CubeWidget(self.meta["color"], should_animate=False)
        self.cube.setFixedSize(36, 36)
        top.addWidget(self.cube)
        layout.addLayout(top)

        name = QLabel(self.room_data.get("nama", "Unknown"))
        name.setObjectName("CardName")
        name.setProperty('class', 'roomcard_title')
        layout.addWidget(name)

        layout.addSpacing(2)

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
        if self.status_key == "Konflik":
            self.setProperty("status", "Konflik")
            self.style().unpolish(self)
            self.style().polish(self)

    def enterEvent(self, event):
        color = self.meta["color"]
        self.setStyleSheet(f"#RoomCard {{ border: 2px solid {color}; }}")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("")
        super().leaveEvent(event)

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
        self.setProperty("class", "active" if self._active else "")
        self.style().unpolish(self)
        self.style().polish(self)


# ──────────────────────────────────────────────
#  KPI CARD
# ──────────────────────────────────────────────
class KpiCard(QFrame):
    def __init__(self, title: str, value: str, icon: str, accent: str = "#4f46e5", parent=None):
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
#  DETAIL PANEL
# ──────────────────────────────────────────────
class RoomDetailPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(290)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        self.lbl_header = QLabel("Detail Ruangan")
        self.lbl_header.setObjectName("PanelHeader")
        root.addWidget(self.lbl_header)

        self.cube_wrap = QHBoxLayout()
        root.addLayout(self.cube_wrap)

        self.lbl_name = QLabel("—")
        self.lbl_name.setObjectName("PanelName")
        self.lbl_name.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_name)

        self.lbl_status = QLabel("—")
        self.lbl_status.setObjectName("PanelStatus")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFixedHeight(28)
        root.addWidget(self.lbl_status, alignment=Qt.AlignCenter)

        root.addSpacing(8)

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

        self.btn_book = QPushButton("📅  Buat Reservasi")
        self.btn_book.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_book.setFixedHeight(40)
        root.addWidget(self.btn_book)

    def load(self, data: dict, is_dark: bool):
        status = normalize_status(data.get("status", "Tersedia"))
        meta   = STATUS_META[status]

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

        for i in reversed(range(self.cube_wrap.count())):
            w = self.cube_wrap.itemAt(i).widget()
            if w: w.deleteLater()
        cube = CubeWidget(meta["color"], should_animate=True)
        cube.setFixedSize(120, 120)
        self.cube_wrap.addWidget(cube, alignment=Qt.AlignCenter)

    def apply_palette(self):
        pass


# ──────────────────────────────────────────────
#  ADMIN DASHBOARD
# ──────────────────────────────────────────────
class ClickableFrame(QFrame):
    clicked = Signal()
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit()

class AdminDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self._build_ruangan_page()
        self._build_pengguna_page()
        self._build_reservasi_page()
        self._build_statistik_page()

        self.refresh_data()
        self.apply_theme()

    def _build_dashboard_page(self):
        self.dashboard_page = QWidget()
        dash_layout = QHBoxLayout(self.dashboard_page)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        dash_layout.setSpacing(0)

        self._build_main(dash_layout)

        self.content_stack.addWidget(self.dashboard_page)

    def _build_ruangan_page(self):
        self.kelola_ruangan_page = KelolaRuanganWidget(self)
        self.content_stack.addWidget(self.kelola_ruangan_page)

    def _build_pengguna_page(self):
        self.kelola_pengguna_page = KelolaPenggunaWidget(self)
        self.content_stack.addWidget(self.kelola_pengguna_page)

    def _build_reservasi_page(self):
        self.kelola_reservasi_page = KelolaReservasiWidget(self)
        self.content_stack.addWidget(self.kelola_reservasi_page)

    def _build_statistik_page(self):
        self.statistik_page = StatistikWidget(self)
        self.content_stack.addWidget(self.statistik_page)

    def switch_page(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)

        if index < self.content_stack.count():
            self.content_stack.setCurrentIndex(index)

        if index == 0:
            self.refresh_data()
        elif index == 1 and hasattr(self, 'kelola_ruangan_page'):
            self.kelola_ruangan_page.refresh_data()
        elif index == 2 and hasattr(self, 'kelola_pengguna_page'):
            self.kelola_pengguna_page.refresh_data()
        elif index == 3 and hasattr(self, 'kelola_reservasi_page'):
            self.kelola_reservasi_page.refresh_data()
        elif index == 4 and hasattr(self, 'statistik_page'):
            self.statistik_page.refresh_data()

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
        prof.setObjectName("AdminProfile")
        prof.setStyleSheet(
            "QFrame#AdminProfile {"
            "  background: rgba(255,255,255,0.07);"
            "  border: 1px solid rgba(255,255,255,0.1);"
            "  border-radius: 14px;"
            "  margin: 0 12px;"
            "}"
        )

        pf = QHBoxLayout(prof)
        pf.setContentsMargins(12, 10, 12, 10)
        pf.setSpacing(10)

        # Avatar — pakai QLabel dengan circular pixmap
        AVATAR_SIZE = 40
        self.lbl_profile_ava = QLabel()
        self.lbl_profile_ava.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.lbl_profile_ava.setAlignment(Qt.AlignCenter)
        # Coba load gambar, fallback ke inisial
        self._set_avatar_image("Admin", AVATAR_SIZE)

        # Text
        vp = QVBoxLayout()
        vp.setSpacing(1)
        vp.setContentsMargins(0, 0, 0, 0)

        self.lbl_profile_name = QLabel("Admin")
        self.lbl_profile_name.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #f1f5f9; background: transparent;"
        )
        # Pastikan teks nggak overflow
        self.lbl_profile_name.setMaximumWidth(120)

        self.lbl_profile_role = QLabel("Administrator")
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
            "QPushButton{background:#4f46e5;color:white;border:none;border-radius:10px;"
            "font-weight:700;font-size:12px;margin:0 12px;}"
            "QPushButton:hover{background:#4338ca;}"
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
            ("🏢", "Kelola Ruangan"),
            ("👥", "Kelola Pengguna"),
            ("📅", "Kelola Reservasi"),
            ("📊", "Statistik"),
            ("⚙️", "Pengaturan"),
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

    def _set_avatar_image(self, name: str, size: int = 40):
        """
        Load gambar dari assets, kalau nggak ada buat avatar inisial.
        Semua path & ukuran dihandle di sini, bukan tersebar di beberapa method.
        """
        img_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'admin_profile.png')
        if os.path.exists(img_path):
            raw = QPixmap(img_path)
            if not raw.isNull():
                circular = make_circular_pixmap(raw, size)
                self.lbl_profile_ava.setPixmap(circular)
                self.lbl_profile_ava.setText("")
                return

        # Fallback: inisial dari nama
        initials = "".join(w[0] for w in name.split() if w)[:2] or "?"
        avatar = make_initial_avatar(initials, size, bg_color="#4f46e5")
        self.lbl_profile_ava.setPixmap(avatar)
        self.lbl_profile_ava.setText("")

    # ─── MAIN CONTENT ───────────────────────────
    def _build_main(self, root):
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        ml = QVBoxLayout(self.main_frame)
        ml.setContentsMargins(28, 20, 16, 20)
        ml.setSpacing(12)

        # Top Bar
        top = QHBoxLayout()
        self.lbl_page = QLabel("Dashboard (Kalender Bulanan)")
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
        self.kpi_rooms   = KpiCard("Total Ruangan",    "0", "🏢", "#4f46e5")
        self.kpi_active  = KpiCard("Reservasi Bln Ini","0", "📅", "#0ea5e9")
        self.kpi_konflik = KpiCard("Konflik Bulan Ini","0", "⚠️", "#f97316")
        self.kpi_users   = KpiCard("Total Pengguna",   "0", "👥", "#22c55e")
        for kpi in (self.kpi_rooms, self.kpi_active, self.kpi_konflik, self.kpi_users):
            kpi_row.addWidget(kpi)
        ml.addLayout(kpi_row)

        # Filters
        from datetime import date
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tahun:"))
        from PySide6.QtWidgets import QComboBox
        self.cb_year = QComboBox()
        current_year = date.today().year
        self.cb_year.addItems([str(y) for y in range(current_year-1, current_year+3)])
        self.cb_year.setCurrentText(str(current_year))
        self.cb_year.currentIndexChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.cb_year)
        
        filter_layout.addSpacing(16)
        
        filter_layout.addWidget(QLabel("Bulan:"))
        self.cb_month = QComboBox()
        months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
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
            lbl.setStyleSheet("font-weight: 800; font-size: 11px; padding: 12px 0; color: #94a3b8; border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.1);")
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

    def _select_week(self, idx: int):
        if idx >= len(self.current_month_weeks):
            idx = max(0, len(self.current_month_weeks) - 1)
            
        self.current_week_idx = idx
        for i, btn in enumerate(self.week_buttons):
            btn.setChecked(i == idx)
            btn.setVisible(i < len(self.current_month_weeks))
            
        self._render_calendar_week()

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

        icon  = "🌙" if self.is_dark else "☀️"
        label = " Terang" if self.is_dark else " Gelap"
        self.btn_theme.setText(icon + label)

    def set_user_profile(self, user: dict):
        if not user: return
        AVATAR_SIZE = 40
        name = user.get("nama", "Admin")
        role = user.get("role", "Administrator")
        self.lbl_profile_name.setText(name)
        self.lbl_profile_role.setText(role)
        role_lower = role.lower()
        if role_lower == "admin":
            initials = "".join(w[0] for w in name.split() if w)[:2] or "AD"
            self.lbl_profile_ava.setPixmap(make_initial_avatar(initials, AVATAR_SIZE, bg_color="#4f46e5"))
        elif role_lower == "dosen":
            initials = "".join(w[0] for w in name.split() if w)[:2] or "DS"
            self.lbl_profile_ava.setPixmap(make_initial_avatar(initials, AVATAR_SIZE, bg_color="#0284c7"))
        else:
            initials = "".join(w[0] for w in name.split() if w)[:2] or "MH"
            self.lbl_profile_ava.setPixmap(make_initial_avatar(initials, AVATAR_SIZE, bg_color="#22c55e"))

    # ─── DATA & RENDERING ───────────────────────
    def refresh_data(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            return
        try:
            year = int(self.cb_year.currentText())
            month = self.cb_month.currentIndex() + 1
            
            import calendar
            # firstweekday=6 means Sunday
            cal = calendar.Calendar(firstweekday=6)
            self.current_month_dates = cal.monthdatescalendar(year, month)
            
            start_date = self.current_month_dates[0][0]
            end_date = self.current_month_dates[-1][-1]

            from utils.worker import Worker
            self.worker = Worker(self._fetch_dashboard_data, start_date, end_date)
            self.worker.finished.connect(lambda result: self._on_dashboard_data(result, month))
            self.worker.error.connect(self._on_dashboard_error)
            self.worker.start()
            
        except Exception as e:
            print("Error parsing dates:", e)

    def _fetch_dashboard_data(self, start_date, end_date):
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        rooms = supabase.table("ruangan").select() or []
        users = supabase.table("pengguna").select() or []
        reservations = supabase.table("reservasi").select(
            "*,pengguna(role,nama)", f"tanggal=gte.{start_date}&tanggal=lte.{end_date}&status=eq.Disetujui"
        )
        return {
            "rooms": rooms,
            "users": users,
            "reservations": reservations if isinstance(reservations, list) else []
        }

    def _on_dashboard_data(self, data, month):
        rooms = data["rooms"]
        users = data["users"]
        self.current_month_reservations = data["reservations"]
        self.room_map = {r["id"]: r for r in rooms}
        
        self.kpi_rooms.set_value(str(len(set([r["nama"] for r in rooms]))))
        self.kpi_users.set_value(str(len(users)))
        self.kpi_active.set_value(str(len(self.current_month_reservations)))
        self.kpi_konflik.set_value("0")
        
        self._render_monthly_calendar(month)

    def _on_dashboard_error(self, err):
        print("Error loading admin dashboard data:", err)

    def _render_monthly_calendar(self, target_month: int):
        self.clear_layout(self.grid_layout)
        
        for row, week in enumerate(self.current_month_dates):
            # QGridLayout row sizes should stretch uniformly
            self.grid_layout.setRowStretch(row, 1)
            for col, dt in enumerate(week):
                self.grid_layout.setColumnStretch(col, 1)
                
                # Cell container
                cell = ClickableFrame()
                cell.setStyleSheet(
                    "QFrame { border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05); background: transparent; }"
                    "QFrame:hover { background: rgba(255,255,255,0.03); }"
                )
                
                # Fixed minimum height for cells to look good
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
                
                day_res = [r for r in self.current_month_reservations if r.get("tanggal") == dt.strftime("%Y-%m-%d")]
                day_res.sort(key=lambda x: x.get("jam_mulai", "00:00"))
                
                # -- ROOM STATUS SUMMARY --
                from datetime import date
                today_date = date.today()
                
                total_rooms = len(self.room_map)
                c_terbooking = 0
                c_terpakai = 0
                
                for r_id in self.room_map:
                    r_res = [r for r in day_res if str(r.get("ruangan_id")) == str(r_id)]
                    if r_res:
                        # If date is in the future, it's 'Terbooking'. If today or past, it's 'Terpakai'.
                        if dt > today_date:
                            c_terbooking += 1
                        else:
                            c_terpakai += 1
                
                c_tersedia = total_rooms - c_terbooking - c_terpakai
                
                summary_html = (
                    f"<span style='color: #22c55e;'>●</span> {c_tersedia} &nbsp; "
                    f"<span style='color: #f97316;'>●</span> {c_terbooking} &nbsp; "
                    f"<span style='color: #ef4444;'>●</span> {c_terpakai}"
                )
                summary_lbl = QLabel(summary_html)
                summary_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; padding-bottom: 4px; border: none; background: transparent;")
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
                        more_lbl = QLabel(f"+{len(day_res) - max_events} acara")
                        more_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; border: none;")
                        ev_layout.addWidget(more_lbl)
                        break
                        
                    # Use str() matching to safely find the room in case of int/string mismatch
                    ruangan = next((v for k, v in self.room_map.items() if str(k) == str(res.get("ruangan_id"))), {})
                    nama_ruang = ruangan.get("nama", "Unknown")
                    jam = res.get("jam_mulai", "")[:5] # "08:00:00" -> "08:00"
                    
                    role = res.get("pengguna", {}).get("role", "").lower()
                    
                    bg_color = "rgba(59,130,246,0.2)" if role == "dosen" else "rgba(34,197,94,0.2)"
                    text_color = "#93c5fd" if role == "dosen" else "#86efac"
                    if not self.is_dark:
                        bg_color = "rgba(59,130,246,0.15)" if role == "dosen" else "rgba(34,197,94,0.15)"
                        text_color = "#1e3a8a" if role == "dosen" else "#14532d"
                    
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
        self.switch_page(3)
        
    def _on_buat_reservasi(self, ruangan_id: int):
        self.switch_page(3)


    def show_day_detail(self, dt):
        day_res = [r for r in self.current_month_reservations if r.get("tanggal") == dt.strftime("%Y-%m-%d")]
        self.popup = DayDetailPopup(dt, self.room_map.values(), day_res, is_dark=self.is_dark, parent=self)
        self.popup.exec()

    def show_room_detail(self, data: dict):
        self.detail.load(data, self.is_dark)

    def show_chatbot(self):
        if not hasattr(self, "_chatbot") or self._chatbot is None:
            self._chatbot = ChatbotDialog(self, role="Admin")
        self._chatbot.show()
        self._chatbot.raise_()
        self._chatbot.activateWindow()

    def handle_logout(self):
        p = self.parent()
        if p and hasattr(p, "switch_to_public"):
            p.switch_to_public()