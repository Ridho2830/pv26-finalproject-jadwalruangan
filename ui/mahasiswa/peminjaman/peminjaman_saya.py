# ui/mahasiswa/peminjaman/peminjaman_saya.py
"""
Halaman "Peminjaman Saya" untuk mahasiswa.
Versi redesign modern mengikuti UI dashboard pada ZIP.

Fitur tetap:
- Refresh real-time dari Supabase
- Batalkan booking
- Ubah booking
- Panel detail reservasi
- Statistik reservasi
- Animasi fade-in
"""

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
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QPushButton,
    QScrollArea,
    QMessageBox,
)

from api.supabase import get_supabase_client
from ui.mahasiswa.dialog_book import DialogUpdateReservasi
from utils.mode import theme_manager


STATUS_STYLE = {
    "Pending": ("#FEF3C7", "#92400E", "⏳"),
    "Disetujui": ("#D1FAE5", "#065F46", "✅"),
    "Ditolak": ("#FEE2E2", "#991B1B", "❌"),
    "Dibatalkan": ("#F3F4F6", "#6B7280", "🚫"),
    "Selesai": ("#EDE9FE", "#4C1D95", "🏁"),
}


class PeminjamanSayaPage(QWidget):
    def __init__(self, pengguna_id: int, pengguna_nama: str = "Mahasiswa", parent=None):
        super().__init__(parent)

        self.pengguna_id = pengguna_id
        self.pengguna_nama = pengguna_nama

        self.reservasi_list = []
        self.cards = []
        self.anim_group = None

        self._build_ui()
        self._load_styles()
        self.refresh_data()

    # ==============================================================
    # UI
    # ==============================================================

    def _build_ui(self):
        self.setObjectName("peminjaman_saya_page")

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ==========================================================
        # HEADER
        # ==========================================================
        header_row = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title_lbl = QLabel("Peminjaman Saya")
        title_lbl.setObjectName("page_title")

        subtitle_lbl = QLabel(
            f"Riwayat dan status reservasi ruangan atas nama {self.pengguna_nama}."
        )
        subtitle_lbl.setObjectName("page_subtitle")

        title_col.addWidget(title_lbl)
        title_col.addWidget(subtitle_lbl)

        refresh_btn = QPushButton("🔄 Muat Ulang")
        refresh_btn.setObjectName("btn_refresh")
        refresh_btn.setFixedHeight(42)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)

        header_row.addLayout(title_col)
        header_row.addStretch()
        header_row.addWidget(refresh_btn)

        root.addLayout(header_row)

        # ==========================================================
        # STATS
        # ==========================================================
        self.stats_lbl = QLabel("Memuat data...")
        self.stats_lbl.setObjectName("stats_label")

        root.addWidget(self.stats_lbl)

        # ==========================================================
        # WARNING CARD
        # ==========================================================
        warning_card = QFrame()
        warning_card.setObjectName("warning_card")

        warning_layout = QHBoxLayout(warning_card)
        warning_layout.setContentsMargins(18, 16, 18, 16)
        warning_layout.setSpacing(12)

        warning_icon = QLabel("⚠️")
        warning_icon.setObjectName("warning_icon")

        warning_text = QLabel(
            "Reservasi dapat dibatalkan admin apabila ruangan digunakan "
            "untuk kegiatan resmi kampus."
        )
        warning_text.setObjectName("warning_text")
        warning_text.setWordWrap(True)

        warning_layout.addWidget(warning_icon)
        warning_layout.addWidget(warning_text)

        root.addWidget(warning_card)

        # ==========================================================
        # SCROLL AREA
        # ==========================================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.list_widget = QWidget()

        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 8, 0)
        self.list_layout.setSpacing(18)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_widget)

        root.addWidget(scroll)

    # ==============================================================
    # REFRESH DATA
    # ==============================================================

    def refresh_data(self):
        self._clear_cards()

        from api.supabase import get_supabase_client

        supabase = get_supabase_client()

        try:
            # ======================================================
            # AMBIL DATA DARI SUPABASE
            # ======================================================

            response = (
                supabase
                .table("reservasi")
                .select("""
                    *,
                    ruangan (
                        id,
                        nama,
                        gedung,
                        lantai,
                        kapasitas
                    )
                """)
                .eq("pengguna_id", self.pengguna_id)
                .order("created_at", desc=True)
                .execute()
            )

            self.reservasi_list = response.data or []

        except Exception as e:
            print(f"[ERROR REFRESH DATA] {e}")
            self.reservasi_list = []

        # ==========================================================
        # KOSONG
        # ==========================================================

        if not self.reservasi_list:
            self.stats_lbl.setText("Belum ada reservasi")
            self._show_empty_state()
            return

        # ==========================================================
        # HITUNG STATISTIK
        # ==========================================================

        counts = {s: 0 for s in STATUS_STYLE}

        for r in self.reservasi_list:
            status = r.get("status", "Pending")

            if status in counts:
                counts[status] += 1

        total = len(self.reservasi_list)

        self.stats_lbl.setText(
            f"Total {total} reservasi  •  "
            f"{counts['Pending']} Pending  •  "
            f"{counts['Disetujui']} Disetujui  •  "
            f"{counts['Ditolak']} Ditolak  •  "
            f"{counts['Dibatalkan']} Dibatalkan"
        )

        # ==========================================================
        # RENDER CARD
        # ==========================================================

        self.cards = []

        for i, reservasi in enumerate(self.reservasi_list):

            card = self._build_card(reservasi, i)

            self.list_layout.insertWidget(
                self.list_layout.count() - 1,
                card
            )

            self.cards.append(card)

        self._animate_cards()

    # ==============================================================
    # BATALKAN BOOKING
    # ==============================================================

    def _on_batal_clicked(self, index: int):
        if index >= len(self.reservasi_list):
            return

        reservasi = self.reservasi_list[index]

        reply = QMessageBox.question(
            self,
            "Batalkan Reservasi?",
            f"Yakin ingin membatalkan reservasi ruangan "
            f"{(reservasi.get('ruangan') or {}).get('nama', '-')}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        from api.supabase import get_supabase_client

        supabase = get_supabase_client()

        reservasi_id = reservasi.get("id")

        try:
            (
            supabase.table("reservasi")
            .update({"status": "Dibatalkan"})
            .eq("id", reservasi_id)
            .execute()
        )

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        QMessageBox.information(
            self,
            "Berhasil",
            "Reservasi berhasil dibatalkan.",
        )

        self.refresh_data()

    # ==============================================================
    # UBAH BOOKING
    # ==============================================================

    def _on_ubah_clicked(self, index: int):
        if index >= len(self.reservasi_list):
            return

        reservasi = self.reservasi_list[index]

        dialog = DialogUpdateReservasi(
            reservasi_data=reservasi,
            pengguna_id=self.pengguna_id,
            parent=self
        )

        if dialog.exec():
            self.refresh_data()

    # ==============================================================
    # EMPTY STATE
    # ==============================================================

    def _show_empty_state(self):
        icon = QLabel("📭")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            "font-size:64px; padding-top:70px; background:transparent;"
        )

        title = QLabel("Belum Ada Reservasi")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size:20px;font-weight:700;background:transparent;"
        )

        desc = QLabel(
            "Kamu belum pernah membuat reservasi ruangan."
        )

        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(
            "font-size:14px;color:#6b7280;background:transparent;"
        )

        self.list_layout.insertWidget(self.list_layout.count() - 1, icon)
        self.list_layout.insertWidget(self.list_layout.count() - 1, title)
        self.list_layout.insertWidget(self.list_layout.count() - 1, desc)

    # ==============================================================
    # CLEAR CARD
    # ==============================================================

    def _build_card(self, reservasi, index):
        card = QFrame()
        card.setObjectName("reservasi_card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        ruangan = reservasi.get("ruangan") or {}

        nama_ruangan = ruangan.get("nama", "-")
        gedung = ruangan.get("gedung", "-")
        lantai = ruangan.get("lantai", "-")

        tanggal = reservasi.get("tanggal", "-")
        jam_mulai = reservasi.get("jam_mulai", "-")
        jam_selesai = reservasi.get("jam_selesai", "-")

        keperluan = reservasi.get("keperluan", "-")
        status = reservasi.get("status", "Pending")

        # ==========================================================
        # HEADER
        # ==========================================================

        header = QHBoxLayout()

        room_lbl = QLabel(nama_ruangan)
        room_lbl.setObjectName("card_room_name")

        status_bg, status_text, status_icon = STATUS_STYLE.get(
            status,
            ("#E5E7EB", "#111827", "•")
        )

        status_lbl = QLabel(f"{status_icon} {status}")
        status_lbl.setStyleSheet(f"""
            background:{status_bg};
            color:{status_text};
            padding:6px 12px;
            border-radius:10px;
            font-size:12px;
            font-weight:700;
        """)

        header.addWidget(room_lbl)
        header.addStretch()
        header.addWidget(status_lbl)

        layout.addLayout(header)

        # ==========================================================
        # DETAIL
        # ==========================================================

        detail_lbl = QLabel(
            f"📍 Gedung {gedung} • Lantai {lantai}\n"
            f"📅 {tanggal}\n"
            f"🕒 {jam_mulai} - {jam_selesai}"
        )

        detail_lbl.setObjectName("card_detail")

        layout.addWidget(detail_lbl)

        # ==========================================================
        # KEPERLUAN
        # ==========================================================

        keperluan_lbl = QLabel(
            f"Keperluan:\n{keperluan}"
        )

        keperluan_lbl.setWordWrap(True)
        keperluan_lbl.setObjectName("card_keperluan")

        layout.addWidget(keperluan_lbl)

        # ==========================================================
        # BUTTON
        # ==========================================================

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        edit_btn = QPushButton("Ubah")
        edit_btn.setObjectName("btn_edit")

        cancel_btn = QPushButton("Batalkan")
        cancel_btn.setObjectName("btn_cancel")

        edit_btn.clicked.connect(
            partial(self._on_ubah_clicked, index)
        )

        cancel_btn.clicked.connect(
            partial(self._on_batal_clicked, index)
        )

        btn_row.addWidget(edit_btn)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

        # ==========================================================
        # ANIMASI
        # ==========================================================

        opacity = QGraphicsOpacityEffect()
        opacity.setOpacity(0)

        card.setGraphicsEffect(opacity)

        return card


    def _clear_cards(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

    # ==============================================================
    # ANIMATION
    # ==============================================================

    def _animate_cards(self):
        self.anim_group = QSequentialAnimationGroup(self)

        for card in self.cards:
            effect = card.graphicsEffect()

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(350)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(QEasingCurve.OutCubic)

            self.anim_group.addAnimation(anim)
            self.anim_group.addAnimation(QPauseAnimation(60))

        self.anim_group.start()

    # ==============================================================
    # STYLE
    # ==============================================================

    def _load_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: #f8f7fb;
                color: #1d1b20;
                font-family: 'DM Sans';
            }

            #page_title {
                font-size: 34px;
                font-weight: 700;
                color: #1f172a;
            }

            #page_subtitle {
                font-size: 14px;
                color: #6b7280;
            }

            #stats_label {
                font-size: 13px;
                font-weight: 600;
                color: #4f378a;
            }

            #btn_refresh {
                background: #4f378a;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 700;
                padding: 0 18px;
            }

            #btn_refresh:hover {
                background: #5b41a1;
            }

            #warning_card {
                background: #fff8db;
                border-left: 4px solid #eab308;
                border-radius: 14px;
            }

            #warning_icon {
                font-size: 22px;
                background: transparent;
            }

            #warning_text {
                background: transparent;
                color: #92400e;
                font-size: 14px;
                line-height: 22px;
            }

            QFrame#reservasi_card {
                background: white;
                border-radius: 18px;
                border: 1px solid #ece6ee;
            }

            QFrame#reservasi_card:hover {
                border: 1px solid #c4b5fd;
                background: #fcfbff;
            }

            #card_room_name {
                font-size: 18px;
                font-weight: 700;
                color: #111827;
                background: transparent;
            }

            #card_detail {
                font-size: 13px;
                color: #6b7280;
                background: transparent;
            }

            #card_keperluan {
                font-size: 13px;
                color: #374151;
                line-height: 22px;
                background: transparent;
            }

            #btn_edit {
                background: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
                padding: 0 18px;
            }

            #btn_edit:hover {
                background: #f9fafb;
            }

            #btn_cancel {
                background: white;
                color: #dc2626;
                border: 1px solid #ef4444;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
                padding: 0 18px;
            }

            #btn_cancel:hover {
                background: #fef2f2;
            }

            #detail_panel {
                background: white;
                border-radius: 20px;
                border: 1px solid #e5e7eb;
            }

            #detail_title {
                font-size: 24px;
                font-weight: 700;
                color: #111827;
                background: transparent;
            }

            #detail_content {
                background: transparent;
                font-size: 14px;
                color: #1f2937;
                line-height: 24px;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollBar:vertical {
                width: 10px;
                background: transparent;
            }

            QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 5px;
                min-height: 40px;
            }
        """)