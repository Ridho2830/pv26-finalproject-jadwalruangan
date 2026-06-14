"""
ChatbotDialog — ReservasiKampus AI Assistant
Design: matches admin_v2.py palette & language exactly.

Layout:
  ┌─────────────────────────────┐
  │  Header (brand + close)     │
  ├─────────────────────────────┤
  │                             │
  │  Message list (scroll)      │
  │                             │
  ├─────────────────────────────┤
  │  Quick-prompt chips         │
  ├─────────────────────────────┤
  │  Input bar (text + send)    │
  └─────────────────────────────┘

Theming: pass is_dark=True/False from parent; default light.
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore    import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QSize, QThread
from PySide6.QtGui     import QCursor, QTextCursor
from PySide6.QtWidgets import (
    QDialog, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QTextEdit,
    QSizePolicy, QWidget, QGraphicsOpacityEffect,
)
import requests
import json

# ── Shared palette (mirrors admin_v2.py) ──────────────────────────────────────
LIGHT = {
    "bg":           "#f0f4ff",
    "surface":      "#ffffff",
    "surface2":     "#f8faff",
    "border":       "#e4e9f5",
    "sidebar_bg":   "#1c1854",
    "text_h":       "#0f172a",
    "text_b":       "#334155",
    "text_m":       "#64748b",
    "text_s":       "#94a3b8",
    "accent":       "#4f46e5",
    "accent_light": "#ede9fe",
    "user_bubble":  "#4f46e5",
    "bot_bubble":   "#f1f5f9",
    "bot_text":     "#1e293b",
    "input_bg":     "#ffffff",
    "send_hover":   "#4338ca",
}
DARK = {
    "bg":           "#0a0f1e",
    "surface":      "#111827",
    "surface2":     "#1e293b",
    "border":       "#1e293b",
    "sidebar_bg":   "#050a14",
    "text_h":       "#f1f5f9",
    "text_b":       "#cbd5e1",
    "text_m":       "#94a3b8",
    "text_s":       "#475569",
    "accent":       "#818cf8",
    "accent_light": "#1e1b4b",
    "user_bubble":  "#4f46e5",
    "bot_bubble":   "#1e293b",
    "bot_text":     "#e2e8f0",
    "input_bg":     "#1e293b",
    "send_hover":   "#6d65f5",
}

QUICK_PROMPTS = [
    "Ruangan yang tersedia sekarang",
    "Cara reservasi ruangan",
    "Cek konflik jadwal",
    "Aturan peminjaman",
]

# ── Typing indicator (3 bouncing dots) ───────────────────────────────────────
class TypingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dots: list[QLabel] = []
        self._timers: list[QTimer] = []
        self._setup()

    def _setup(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        for i in range(3):
            dot = QLabel("●")
            dot.setFixedSize(10, 10)
            dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet("font-size:8px; color:#94a3b8;")
            h.addWidget(dot)
            self._dots.append(dot)

            t = QTimer(self)
            t.setInterval(400)
            delay = i * 160
            QTimer.singleShot(delay, lambda _t=t: _t.start())
            t.timeout.connect(lambda d=dot: self._bounce(d))
            self._timers.append(t)

        h.addStretch()

    def _bounce(self, dot: QLabel):
        c = dot.styleSheet()
        if "color:#4f46e5" in c or "color:#818cf8" in c:
            dot.setStyleSheet("font-size:8px; color:#94a3b8;")
        else:
            dot.setStyleSheet("font-size:8px; color:#4f46e5;")

    def stop(self):
        for t in self._timers:
            t.stop()


# ── Single message bubble ─────────────────────────────────────────────────────
class MessageBubble(QFrame):
    def __init__(self, text: str, is_user: bool, is_dark: bool, timestamp: str, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.is_dark = is_dark
        self._build(text, timestamp)
        self.apply_palette(DARK if is_dark else LIGHT)

    def _build(self, text: str, timestamp: str):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(8)

        # Avatar
        ava = QLabel("👤" if self.is_user else "🤖")
        ava.setFixedSize(32, 32)
        ava.setAlignment(Qt.AlignCenter)
        ava.setObjectName("BubbleAva")

        # Content column
        col = QVBoxLayout()
        col.setSpacing(3)

        # Bubble text
        self.bubble = QLabel(text)
        self.bubble.setTextFormat(Qt.MarkdownText)
        self.bubble.setWordWrap(True)
        self.bubble.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.bubble.setOpenExternalLinks(True)
        self.bubble.setObjectName("BubbleUser" if self.is_user else "BubbleBot")
        self.bubble.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Timestamp
        ts = QLabel(timestamp)
        ts.setObjectName("BubbleTs")
        ts.setAlignment(Qt.AlignRight if self.is_user else Qt.AlignLeft)

        col.addWidget(self.bubble)
        col.addWidget(ts)

        if self.is_user:
            outer.addStretch()
            outer.addLayout(col)
            outer.addWidget(ava)
        else:
            outer.addWidget(ava)
            outer.addLayout(col)
            outer.addStretch()

    def apply_palette(self, p: dict):
        user_bg   = p["user_bubble"]
        bot_bg    = p["bot_bubble"]
        bot_text  = p["bot_text"]
        ts_color  = p["text_s"]
        border    = p["border"]
        surface2  = p["surface2"]

        self.setStyleSheet("background: transparent;")

        if self.is_user:
            self.bubble.setStyleSheet(f"""
                QLabel#BubbleUser {{
                    background: {user_bg};
                    color: white;
                    border-radius: 16px 16px 4px 16px;
                    padding: 10px 14px;
                    font-size: 13px;
                    line-height: 1.5;
                }}
            """)
        else:
            self.bubble.setStyleSheet(f"""
                QLabel#BubbleBot {{
                    background: {bot_bg};
                    color: {bot_text};
                    border: 1px solid {border};
                    border-radius: 16px 16px 16px 4px;
                    padding: 10px 14px;
                    font-size: 13px;
                    line-height: 1.5;
                }}
            """)

        # Avatar style
        for child in self.findChildren(QLabel, "BubbleAva"):
            child.setStyleSheet(f"""
                QLabel#BubbleAva {{
                    background: {surface2};
                    border: 1px solid {border};
                    border-radius: 16px;
                    font-size: 14px;
                }}
            """)

        for child in self.findChildren(QLabel, "BubbleTs"):
            child.setStyleSheet(f"color: {ts_color}; font-size: 10px; background: transparent;")


# ── Quick prompt chip ─────────────────────────────────────────────────────────
class QuickChip(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(28)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

    def apply_palette(self, p: dict):
        self.setStyleSheet(f"""
            QPushButton {{
                background: {p['accent_light']};
                color: {p['accent']};
                border: 1px solid {p['accent']}44;
                border-radius: 14px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {p['accent']};
                color: white;
                border-color: {p['accent']};
            }}
        """)


# ── AI Worker (Ollama) ────────────────────────────────────────────────────────
class OllamaWorker(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, prompt: str, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.model = "phyrus:latest"

    def run(self):
        url = "http://localhost:11434/api/generate"
        
        # Ambil data real-time dari Supabase
        db_context = ""
        try:
            from api.supabase import get_supabase_client
            supabase = get_supabase_client()
            rooms = supabase.table('ruangan').select()
            if rooms:
                counts = {"Tersedia": 0, "Terbooking": 0, "Terpakai": 0}
                details = []
                for r in rooms:
                    s = r.get('status', 'Tersedia')
                    if s == "Digunakan": s = "Terpakai"
                    elif s in ("Tidak Tersedia", "Nonaktif", "Maintenance"): s = "Terpakai"
                    elif s == "Dosen": s = "Terbooking"
                    
                    if s in counts: 
                        counts[s] += 1
                    
                    # Tambahkan ke detail (dibatasi 50 ruangan agar prompt tidak kepanjangan)
                    if len(details) < 50:
                        details.append(f"- {r.get('nama', 'Unknown')} (Kapasitas: {r.get('kapasitas', 0)}): {s}")
                
                if len(rooms) > 50:
                    details.append(f"... (dan {len(rooms) - 50} ruangan lainnya)")

                db_context = (
                    f"\n\n--- DATA DATABASE SAAT INI (REAL-TIME) ---\n"
                    f"Total Ruangan: {len(rooms)}\n"
                    f"Statistik: {counts['Tersedia']} Tersedia, {counts['Terpakai']} Terpakai, {counts['Terbooking']} Terbooking\n"
                    f"Daftar Detail Ruangan:\n" + "\n".join(details) + "\n----------------------------------------\n"
                )
        except Exception as e:
            print(f"[AI Worker] Gagal mengambil data Supabase: {e}")

        system_prompt = (
            "Anda adalah Asisten AI untuk Sistem Reservasi Kampus. "
            "Gunakan bahasa Indonesia yang ramah, ringkas, dan profesional. "
            "Bantu pengguna terkait ketersediaan ruangan, aturan reservasi, atau fasilitas kampus."
            f"{db_context}"
        )
        
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nPertanyaan pengguna: {self.prompt}\n\nJawaban Assistant: ",
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=180)
            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "").strip()
                if not reply:
                    reply = "Maaf, saya tidak memberikan jawaban yang dapat dibaca."
                self.finished_signal.emit(reply)
            else:
                self.error_signal.emit(f"Error API: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.error_signal.emit(
                f"Gagal terhubung ke AI Lokal (Ollama).\n"
                f"Pastikan aplikasi Ollama berjalan di localhost:11434.\nDetail Error: {str(e)}"
            )


# ── Main dialog ───────────────────────────────────────────────────────────────
class ChatbotDialog(QDialog):
    def __init__(self, parent=None, is_dark: bool = False):
        super().__init__(parent)
        self.is_dark = is_dark
        self._chips: list[QuickChip] = []
        self._bubbles: list[MessageBubble] = []
        self._typing_widget: QWidget | None = None

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(420, 620)
        self.resize(460, 660)

        self._build()
        self._push_welcome()
        self.apply_palette()

    # ── Build ──────────────────────────────────────────────────────────────
    def _build(self):
        # Outer frame (rounded, shadow-like border)
        self.outer = QFrame(self)
        self.outer.setObjectName("ChatOuter")
        self.outer.setGeometry(0, 0, self.width(), self.height())

        root = QVBoxLayout(self.outer)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────
        self.header = QFrame()
        self.header.setObjectName("ChatHeader")
        self.header.setFixedHeight(60)
        hdr = QHBoxLayout(self.header)
        hdr.setContentsMargins(16, 0, 16, 0)

        # Bot avatar + name
        ava = QLabel("🤖")
        ava.setFixedSize(36, 36)
        ava.setAlignment(Qt.AlignCenter)
        ava.setObjectName("HeaderAva")

        v_name = QVBoxLayout()
        v_name.setSpacing(1)
        self.lbl_name = QLabel("Asisten AI")
        self.lbl_name.setObjectName("HeaderName")
        self.lbl_online = QLabel("● Online")
        self.lbl_online.setObjectName("HeaderOnline")
        v_name.addWidget(self.lbl_name)
        v_name.addWidget(self.lbl_online)

        hdr.addWidget(ava)
        hdr.addLayout(v_name)
        hdr.addStretch()

        # Theme toggle
        self.btn_theme = QPushButton()
        self.btn_theme.setFixedSize(32, 32)
        self.btn_theme.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_theme.setObjectName("IconBtn")
        self.btn_theme.clicked.connect(self.toggle_theme)
        hdr.addWidget(self.btn_theme)

        # Close
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setObjectName("CloseBtn")
        btn_close.clicked.connect(self.close)
        hdr.addWidget(btn_close)

        root.addWidget(self.header)

        # Thin accent line under header
        self.accent_bar = QFrame()
        self.accent_bar.setFixedHeight(2)
        self.accent_bar.setObjectName("AccentBar")
        root.addWidget(self.accent_bar)

        # ── Message area ────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setObjectName("MsgScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.msg_container = QWidget()
        self.msg_container.setObjectName("MsgContainer")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(16, 16, 16, 16)
        self.msg_layout.setSpacing(8)
        self.msg_layout.addStretch()

        self.scroll.setWidget(self.msg_container)
        root.addWidget(self.scroll, stretch=1)

        # ── Quick prompts ────────────────────────────────────────────────
        self.chip_frame = QFrame()
        self.chip_frame.setObjectName("ChipFrame")
        chip_h = QHBoxLayout(self.chip_frame)
        chip_h.setContentsMargins(12, 8, 12, 8)
        chip_h.setSpacing(6)

        for text in QUICK_PROMPTS:
            chip = QuickChip(text)
            chip.clicked.connect(lambda _, t=text: self._on_quick(t))
            chip_h.addWidget(chip)
            self._chips.append(chip)
        chip_h.addStretch()

        root.addWidget(self.chip_frame)

        # Divider
        div = QFrame()
        div.setObjectName("Divider")
        div.setFixedHeight(1)
        root.addWidget(div)

        # ── Input bar ───────────────────────────────────────────────────
        self.input_frame = QFrame()
        self.input_frame.setObjectName("InputFrame")
        self.input_frame.setFixedHeight(60)
        inp = QHBoxLayout(self.input_frame)
        inp.setContentsMargins(12, 10, 12, 10)
        inp.setSpacing(8)

        self.text_input = QTextEdit()
        self.text_input.setObjectName("TextInput")
        self.text_input.setPlaceholderText("Ketik pesan…")
        self.text_input.setFixedHeight(40)
        self.text_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Enter = send, Shift+Enter = newline
        self.text_input.installEventFilter(self)
        inp.addWidget(self.text_input)

        self.btn_send = QPushButton("➤")
        self.btn_send.setObjectName("SendBtn")
        self.btn_send.setFixedSize(40, 40)
        self.btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_send.clicked.connect(self._send)
        inp.addWidget(self.btn_send)

        root.addWidget(self.input_frame)

    # ── Event filter (Enter key) ───────────────────────────────────────────
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui  import QKeyEvent
        if obj is self.text_input and event.type() == QEvent.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if key in (Qt.Key_Return, Qt.Key_Enter) and not (mods & Qt.ShiftModifier):
                self._send()
                return True
        return super().eventFilter(obj, event)

    # ── Resize: keep outer frame filling dialog ────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.outer.setGeometry(0, 0, self.width(), self.height())

    # ── Welcome message ───────────────────────────────────────────────────
    def _push_welcome(self):
        self._add_bubble(
            "Halo! Saya asisten AI ReservasiKampus 👋\n"
            "Saya bisa membantu Anda cek ketersediaan ruangan, panduan reservasi, "
            "atau menyelesaikan konflik jadwal. Ada yang bisa saya bantu?",
            is_user=False,
        )

    # ── Add bubble ────────────────────────────────────────────────────────
    def _add_bubble(self, text: str, is_user: bool):
        ts = datetime.now().strftime("%H:%M")
        bubble = MessageBubble(text, is_user, self.is_dark, ts)
        # Insert before the trailing stretch (last item)
        self.msg_layout.insertWidget(self.msg_layout.count() - 1, bubble)
        self._bubbles.append(bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    # ── Typing indicator ──────────────────────────────────────────────────
    def _show_typing(self):
        p = DARK if self.is_dark else LIGHT
        wrap = QFrame()
        wrap.setObjectName("TypingWrap")
        wrap.setStyleSheet(f"""
            QFrame#TypingWrap {{
                background: {p['bot_bubble']};
                border: 1px solid {p['border']};
                border-radius: 16px 16px 16px 4px;
                padding: 8px 14px;
                max-width: 80px;
            }}
        """)
        h = QHBoxLayout(wrap)
        h.setContentsMargins(6, 4, 6, 4)
        indicator = TypingIndicator()
        h.addWidget(indicator)

        # Put in row with bot avatar
        row = QFrame()
        row.setStyleSheet("background:transparent;")
        row_h = QHBoxLayout(row)
        row_h.setContentsMargins(0, 2, 0, 2)
        row_h.setSpacing(8)
        ava = QLabel("🤖")
        ava.setFixedSize(32, 32)
        ava.setAlignment(Qt.AlignCenter)
        ava.setStyleSheet(f"background:{p['surface2']};border:1px solid {p['border']};border-radius:16px;font-size:14px;")
        row_h.addWidget(ava)
        row_h.addWidget(wrap)
        row_h.addStretch()

        self.msg_layout.insertWidget(self.msg_layout.count() - 1, row)
        self._typing_widget = row
        self._typing_indicator = indicator
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _hide_typing(self):
        if self._typing_widget:
            self._typing_indicator.stop()
            self._typing_widget.deleteLater()
            self._typing_widget = None

    # ── Send ──────────────────────────────────────────────────────────────
    def _send(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return
        self.text_input.clear()
        self._add_bubble(text, is_user=True)
        self._show_typing()
        # Simulate async reply
        QTimer.singleShot(1200, lambda: self._bot_reply(text))

    def _on_quick(self, text: str):
        self._add_bubble(text, is_user=True)
        self._show_typing()
        QTimer.singleShot(1000, lambda: self._bot_reply(text))

    def _bot_reply(self, query: str):
        # Mulai thread Ollama tanpa parent agar tidak dihancurkan saat dialog ditutup tiba-tiba
        worker = OllamaWorker(query, None)
        
        if not hasattr(self, '_workers'):
            self._workers = []
        self._workers.append(worker)

        worker.finished_signal.connect(self._on_bot_success)
        worker.error_signal.connect(self._on_bot_error)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        worker.start()

    def _cleanup_worker(self, worker):
        if hasattr(self, '_workers') and worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()

    def _on_bot_success(self, reply: str):
        self._hide_typing()
        self._add_bubble(reply, is_user=False)
        
    def _on_bot_error(self, error_msg: str):
        self._hide_typing()
        self._add_bubble(error_msg, is_user=False)

    # ── Scroll ────────────────────────────────────────────────────────────
    def _scroll_to_bottom(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Theme ─────────────────────────────────────────────────────────────
    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_palette()

        # Re-apply all existing bubbles
        p = DARK if self.is_dark else LIGHT
        for b in self._bubbles:
            b.is_dark = self.is_dark
            b.apply_palette(p)

    def apply_palette(self):
        p = DARK if self.is_dark else LIGHT

        # Outer dialog frame
        self.outer.setStyleSheet(f"""
            QFrame#ChatOuter {{
                background: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 20px;
            }}
        """)

        # Header
        self.header.setStyleSheet(f"""
            QFrame#ChatHeader {{
                background: {p['sidebar_bg']};
                border-radius: 20px 20px 0 0;
            }}
        """)

        # Accent bar
        accent = p["accent"]
        self.accent_bar.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {accent}, stop:0.6 {accent}88, stop:1 transparent);"
        )

        # Header labels
        self.lbl_name.setStyleSheet(
            "color: white; font-size: 14px; font-weight: 800; background: transparent;"
        )
        self.lbl_online.setStyleSheet(
            "color: #4ade80; font-size: 10px; font-weight: 600; background: transparent;"
        )

        # Header avatar
        for w in self.header.findChildren(QLabel, "HeaderAva"):
            w.setStyleSheet(
                "background: rgba(255,255,255,0.12); border-radius: 18px;"
                "font-size: 18px; border: none;"
            )

        # Theme button
        icon = "☀️" if self.is_dark else "🌙"
        self.btn_theme.setText(icon)
        self.btn_theme.setStyleSheet(f"""
            QPushButton#IconBtn {{
                background: rgba(255,255,255,0.1);
                color: white; border: none; border-radius: 8px;
                font-size: 14px;
            }}
            QPushButton#IconBtn:hover {{ background: rgba(255,255,255,0.2); }}
        """)

        # Close button
        self.findChild(QPushButton, "CloseBtn").setStyleSheet(f"""
            QPushButton#CloseBtn {{
                background: rgba(239,68,68,0.15);
                color: #ef4444; border: none; border-radius: 8px;
                font-size: 14px; font-weight: 700;
            }}
            QPushButton#CloseBtn:hover {{
                background: #ef4444; color: white;
            }}
        """)

        # Message scroll area + container
        self.scroll.setStyleSheet(f"""
            QScrollArea#MsgScroll {{ background: {p['bg']}; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 4px; }}
            QScrollBar::handle:vertical {{
                background: {p['border']}; border-radius: 2px; min-height: 20px;
            }}
        """)
        self.msg_container.setStyleSheet(f"QWidget#MsgContainer {{ background: {p['bg']}; }}")

        # Chips row
        self.chip_frame.setStyleSheet(f"""
            QFrame#ChipFrame {{
                background: {p['surface']};
                border-top: 1px solid {p['border']};
            }}
        """)
        for chip in self._chips:
            chip.apply_palette(p)

        # Divider
        self.findChild(QFrame, "Divider").setStyleSheet(
            f"background: {p['border']};"
        )

        # Input frame
        self.input_frame.setStyleSheet(f"""
            QFrame#InputFrame {{
                background: {p['surface']};
                border-radius: 0 0 20px 20px;
            }}
        """)
        self.text_input.setStyleSheet(f"""
            QTextEdit#TextInput {{
                background: {p['input_bg']};
                color: {p['text_b']};
                border: 1px solid {p['border']};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
            }}
        """)
        self.btn_send.setStyleSheet(f"""
            QPushButton#SendBtn {{
                background: {p['accent']};
                color: white; border: none; border-radius: 10px;
                font-size: 16px; font-weight: 700;
            }}
            QPushButton#SendBtn:hover {{ background: {p['send_hover']}; }}
            QPushButton#SendBtn:pressed {{ background: #3730a3; }}
        """)