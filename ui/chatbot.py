import requests
from datetime import datetime
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextBrowser, QLineEdit, QPushButton, QFrame, QSizePolicy, QWidget, QScrollArea
)

# ── Palette ──────────────────────────────────────────────────────────────────
BG_WINDOW   = "#0d0f14"
BG_SURFACE  = "#13161e"
BG_BUBBLE   = "#1a1d28"
BG_USER     = "#6366f1"      # indigo
ACCENT      = "#6366f1"
ACCENT_DARK = "#4f46e5"
BORDER      = "#1e2230"
TEXT_PRI    = "#f1f5f9"
TEXT_SEC    = "#94a3b8"
TEXT_MUT    = "#475569"
GREEN       = "#22c55e"
RED_BG      = "#1f1318"
RED_BORDER  = "#3b1a1a"
RED_TEXT    = "#f87171"


# ── Worker thread ─────────────────────────────────────────────────────────────
class AIWorker(QThread):
    response_received = Signal(str)
    error_occurred    = Signal(str)

    def __init__(self, prompt, model_name="phyrus:latest", parent=None):
        super().__init__(parent)
        self.prompt     = prompt
        self.model_name = model_name

    def run(self):
        try:
            # Ambil data ruangan dari Supabase
            try:
                from api.supabase import get_supabase_client
                supabase   = get_supabase_client()
                rooms_data = supabase.table('ruangan').select('*').execute().data or []
                context_lines = [
                    f"- {r.get('nama')}: Kapasitas {r.get('kapasitas')} kursi, "
                    f"Status: {r.get('status')}, Fasilitas: {r.get('fasilitas')}"
                    for r in rooms_data
                ]
                db_context = "\n".join(context_lines) if context_lines else "Tidak ada data ruangan."
            except Exception as e:
                db_context = f"(Gagal mengambil data: {e})"

            system_prompt = (
                "Anda adalah asisten AI yang membantu mengelola sistem Reservasi Ruangan Kampus. "
                "Jawablah dengan ringkas dan informatif dalam Bahasa Indonesia. "
                "Berikut adalah data ruangan saat ini:\n"
                f"{db_context}"
            )

            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": self.prompt},
                    ],
                    "stream": False,
                },
                timeout=300,
            )
            response.raise_for_status()

            reply = response.json().get("message", {}).get("content", "")
            if reply:
                self.response_received.emit(reply)
            else:
                self.error_occurred.emit("AI memberikan balasan kosong.")

        except requests.exceptions.ConnectionError:
            self.error_occurred.emit(
                "Koneksi ke Ollama gagal.\nPastikan Ollama sudah berjalan (localhost:11434)."
            )
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Error menghubungi AI: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Kesalahan internal: {e}")


# ── Bubble helpers ────────────────────────────────────────────────────────────
def _time_now() -> str:
    return datetime.now().strftime("%H:%M")


def _user_bubble(text: str) -> str:
    t = text.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"""
    <table width='100%' cellspacing='0' cellpadding='0'>
      <tr>
        <td width='18%'></td>
        <td width='82%' align='right'>
          <p style='font-size:10px;font-weight:600;letter-spacing:0.06em;
                    text-transform:uppercase;color:{TEXT_SEC};
                    margin:0 4px 5px 0;text-align:right;'>Anda</p>
          <div style='display:inline-block;background:{BG_USER};
                      color:#ffffff;padding:10px 14px;
                      border-radius:14px 14px 4px 14px;
                      font-size:13px;line-height:1.65;text-align:left;'>{t}</div>
          <p style='font-size:10px;color:{TEXT_MUT};margin:4px 4px 0 0;
                    text-align:right;'>{_time_now()}</p>
        </td>
      </tr>
    </table><br>"""


def _ai_bubble(text: str) -> str:
    t = text.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"""
    <table width='100%' cellspacing='0' cellpadding='0'>
      <tr>
        <td width='82%' align='left'>
          <p style='font-size:10px;font-weight:600;letter-spacing:0.06em;
                    text-transform:uppercase;color:{ACCENT};
                    margin:0 0 5px 4px;'>AI</p>
          <div style='display:inline-block;background:{BG_BUBBLE};
                      color:{TEXT_SEC};padding:10px 14px;
                      border-radius:14px 14px 14px 4px;
                      border:1px solid {BORDER};
                      font-size:13px;line-height:1.65;'>{t}</div>
          <p style='font-size:10px;color:{TEXT_MUT};margin:4px 0 0 4px;'>{_time_now()}</p>
        </td>
        <td width='18%'></td>
      </tr>
    </table><br>"""


def _typing_bubble() -> str:
    dot = (
        f"<span style='display:inline-block;width:7px;height:7px;"
        f"border-radius:50%;background:{TEXT_MUT};margin:0 2px;'></span>"
    )
    return f"""
    <table width='100%' cellspacing='0' cellpadding='0'>
      <tr>
        <td width='82%' align='left'>
          <p style='font-size:10px;font-weight:600;letter-spacing:0.06em;
                    text-transform:uppercase;color:{ACCENT};
                    margin:0 0 5px 4px;'>AI</p>
          <div style='display:inline-block;background:{BG_BUBBLE};
                      padding:13px 16px;border-radius:14px 14px 14px 4px;
                      border:1px solid {BORDER};'>{dot}{dot}{dot}</div>
        </td>
        <td width='18%'></td>
      </tr>
    </table><br>"""


def _error_bubble(text: str) -> str:
    t = text.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"""
    <table width='100%' cellspacing='0' cellpadding='0'>
      <tr>
        <td width='82%' align='left'>
          <p style='font-size:10px;font-weight:600;letter-spacing:0.06em;
                    text-transform:uppercase;color:{RED_TEXT};
                    margin:0 0 5px 4px;'>⚠ Error</p>
          <div style='display:inline-block;background:{RED_BG};
                      color:{RED_TEXT};padding:10px 14px;
                      border-radius:14px 14px 14px 4px;
                      border:1px solid {RED_BORDER};
                      font-size:13px;line-height:1.65;'>{t}</div>
        </td>
        <td width='18%'></td>
      </tr>
    </table><br>"""


# ── Main dialog ───────────────────────────────────────────────────────────────
class ChatbotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Assistant – Reservasi Kampus")
        self.setMinimumSize(460, 640)
        self.resize(480, 660)
        self.worker = None

        self._apply_palette()
        self._build_ui()
        self._append_welcome()

    # ── Palette ──────────────────────────────────────────────────────────────
    def _apply_palette(self):
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(BG_WINDOW))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())

        # Chat browser
        self.chat = QTextBrowser()
        self.chat.setOpenExternalLinks(True)
        self.chat.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {BG_WINDOW};
                border: none;
                padding: 20px 16px;
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                color: {TEXT_SEC};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 4px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 2px;
                min-height: 24px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        root.addWidget(self.chat)

        root.addWidget(self._make_divider())
        root.addWidget(self._make_input_area())

    def _make_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(68)
        w.setStyleSheet(f"background-color: {BG_SURFACE}; border-bottom: 1px solid {BORDER};")

        h = QHBoxLayout(w)
        h.setContentsMargins(20, 0, 20, 0)
        h.setSpacing(12)

        # Avatar
        avatar = QLabel("🤖")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 {ACCENT}, stop:1 #8b5cf6);
            border-radius: 12px;
            font-size: 20px;
        """)
        h.addWidget(avatar)

        # Name + status
        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel("Asisten Reservasi Kampus")
        name.setStyleSheet(f"color: {TEXT_PRI}; font-size: 14px; font-weight: 600;")
        info.addWidget(name)

        status_row = QHBoxLayout()
        status_row.setSpacing(5)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {GREEN}; font-size: 9px;")
        status_row.addWidget(dot)
        status_lbl = QLabel("Online · Siap membantu")
        status_lbl.setStyleSheet(f"color: {TEXT_MUT}; font-size: 11px;")
        status_row.addWidget(status_lbl)
        status_row.addStretch()
        info.addLayout(status_row)

        h.addLayout(info)
        h.addStretch()

        # Model badge
        badge = QLabel("phyrus:latest")
        badge.setStyleSheet(f"""
            color: {ACCENT};
            background: rgba(99,102,241,0.10);
            border: 1px solid rgba(99,102,241,0.25);
            border-radius: 6px;
            padding: 3px 9px;
            font-family: 'Cascadia Code', 'Consolas', monospace;
            font-size: 10px;
        """)
        h.addWidget(badge)

        return w

    def _make_divider(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet(f"background-color: {BORDER}; border: none;")
        return f

    def _make_input_area(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background-color: {BG_SURFACE};")

        outer = QVBoxLayout(w)
        outer.setContentsMargins(16, 14, 16, 18)
        outer.setSpacing(8)

        # Input row container
        row_container = QWidget()
        row_container.setStyleSheet(f"""
            QWidget {{
                background: {BG_BUBBLE};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        row = QHBoxLayout(row_container)
        row.setContentsMargins(16, 6, 6, 6)
        row.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ketik pesan...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {TEXT_PRI};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13.5px;
                padding: 6px 0;
                selection-background-color: {ACCENT};
            }}
        """)
        self.input_field.returnPressed.connect(self.send_message)
        row.addWidget(self.input_field)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(38, 38)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setStyleSheet(f"""
            QPushButton#sendBtn {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                            stop:0 {ACCENT}, stop:1 #7c3aed);
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 10px;
            }}
            QPushButton#sendBtn:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                            stop:0 {ACCENT_DARK}, stop:1 #6d28d9);
            }}
            QPushButton#sendBtn:disabled {{
                background: {BORDER};
                color: {TEXT_MUT};
            }}
        """)
        self.send_btn.clicked.connect(self.send_message)
        row.addWidget(self.send_btn)

        outer.addWidget(row_container)

        # Footer hint
        hint = QLabel("AI lokal · Data dijaga privat")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {BORDER}; font-size: 10px;")
        outer.addWidget(hint)

        return w

    # ── Chat helpers ──────────────────────────────────────────────────────────
    def _scroll_bottom(self):
        sb = self.chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _append_welcome(self):
        self.chat.append(_ai_bubble(
            "Halo! Saya asisten AI lokal untuk sistem Reservasi Ruangan Kampus.\n"
            "Ada yang bisa saya bantu hari ini?"
        ))
        self._scroll_bottom()

    def _set_ui_loading(self, loading: bool):
        self.input_field.setEnabled(not loading)
        self.send_btn.setEnabled(not loading)
        self.send_btn.setText("…" if loading else "➤")

    # ── Send ──────────────────────────────────────────────────────────────────
    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.chat.append(_user_bubble(text))
        self.input_field.clear()
        self._scroll_bottom()

        # Show typing indicator
        self.chat.append(_typing_bubble())
        self._scroll_bottom()

        self._set_ui_loading(True)

        self.worker = AIWorker(text, model_name="phyrus:latest", parent=self)
        self.worker.response_received.connect(self._on_response)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _remove_last_block(self):
        """Remove the last appended HTML block (typing indicator)."""
        cursor = self.chat.textCursor()
        cursor.movePosition(cursor.End)
        # Select and delete last paragraph block
        doc = self.chat.document()
        block = doc.lastBlock()
        # Walk back until we hit the typing bubble's opening table tag
        # Simplest: just undo one append by clearing and re-rendering isn't ideal;
        # instead we store a marker and replace.
        pass  # handled by re-rendering below

    def _on_response(self, reply: str):
        # Clear typing indicator: easiest via undo of last append
        self._replace_typing(reply, is_error=False)
        self._scroll_bottom()

    def _on_error(self, error_msg: str):
        self._replace_typing(error_msg, is_error=True)
        self._scroll_bottom()

    def _replace_typing(self, content: str, is_error: bool):
        """Remove typing indicator and append real bubble."""
        html = self.chat.toHtml()
        # Remove typing block (identified by the dot span marker)
        marker = '<span style=\'display:inline-block;width:7px;height:7px;'
        idx = html.rfind(marker)
        # Find the enclosing <table> before marker
        table_start = html.rfind("<table", 0, idx)
        table_end   = html.find("</table>", idx)
        if table_start != -1 and table_end != -1:
            html = html[:table_start] + html[table_end + len("</table>"):]
            self.chat.setHtml(html)
        # Append actual response
        if is_error:
            self.chat.append(_error_bubble(content))
        else:
            self.chat.append(_ai_bubble(content))

    def _on_finished(self):
        self._set_ui_loading(False)
        self.input_field.setFocus()