from functools import partial

from PySide6.QtCore import (
    Qt,
)


from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QScrollArea,
    QMessageBox,
)

from ui.mahasiswa.peminjaman.dialog_reservasi import DialogBuatReservasi, DialogSelesaiReservasi
from utils.mode import theme_manager


STATUS_STYLE = {
    "Pending": ("#FEF3C7", "#92400E", "⏳"),
    "Disetujui": ("#D1FAE5", "#065F46", "✅"),
    "Ditolak": ("#FEE2E2", "#991B1B", "❌"),
    "Dibatalkan": ("#F3F4F6", "#6B7280", "🚫"),
    "Selesai": ("#EDE9FE", "#4C1D95", "🏁"),
}


class ReservasiMahasiswaPage(QWidget):
    def __init__(self, pengguna_id: int, pengguna_nama: str = "Mahasiswa", parent=None):
        super().__init__(parent)

        self.pengguna_id = pengguna_id
        self.pengguna_nama = pengguna_nama

        self.reservasi_list = []
        self.cards = []

        self._build_ui()
        self.refresh_data()
        
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

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
        title_lbl.setObjectName("PageTitle")

        subtitle_lbl = QLabel(
            f"Riwayat dan status reservasi ruangan atas nama {self.pengguna_nama}."
        )
        subtitle_lbl.setObjectName("CardMeta")

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
        warning_card.setObjectName("WarnBanner")

        warning_layout = QHBoxLayout(warning_card)
        
        warning_layout.setContentsMargins(18, 16, 18, 16)
        warning_layout.setSpacing(12)

        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("""
            font-size:22px;
            background:transparent;
            """)

        warning_text = QLabel(
            "Reservasi dapat dibatalkan admin apabila ruangan digunakan "
            "untuk kegiatan resmi kampus."
        )
        warning_text.setObjectName("WarnText")
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
        if hasattr(self, 'worker') and self.worker.isRunning():
            return
            
        self.stats_lbl.setText("Memuat data...")
        from utils.worker import Worker
        self.worker = Worker(self._fetch_reservasi_worker)
        self.worker.finished.connect(self._on_reservasi_fetched)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _fetch_reservasi_worker(self):
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        query = "*,ruangan(id,nama,gedung,lantai,kapasitas)"
        filters = f"pengguna_id=eq.{self.pengguna_id}&order=created_at.desc"
        return supabase.table("reservasi").select(query, filters)

    def _on_error(self, err_msg):
        self.stats_lbl.setText("Gagal memuat data")
        self.reservasi_list = []
        self._show_empty_state()
        print(f"[ERROR REFRESH DATA] {err_msg}")

    def _on_reservasi_fetched(self, response):
        self.reservasi_list = response if isinstance(response, list) else []

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

        if hasattr(self, 'batal_worker') and self.batal_worker.isRunning():
            return
            
        from utils.worker import Worker
        reservasi_id = reservasi.get("id")
        self.batal_worker = Worker(self._batal_reservasi_worker, reservasi_id)
        self.batal_worker.finished.connect(self._on_batal_finished)
        self.batal_worker.error.connect(self._on_batal_error)
        self.batal_worker.start()

    def _batal_reservasi_worker(self, reservasi_id):
        from api.supabase import get_supabase_client
        return get_supabase_client().table("reservasi").update({"status": "Dibatalkan"}, f"id=eq.{reservasi_id}")

    def _on_batal_finished(self, res):
        QMessageBox.information(
            self,
            "Berhasil",
            "Reservasi berhasil dibatalkan.",
        )
        self.refresh_data()

    def _on_batal_error(self, err_msg):
        QMessageBox.critical(self, "Error", err_msg)

    # ==============================================================
    # SELESAIKAN BOOKING
    # ==============================================================

    def _on_selesaikan_clicked(self, index: int):
        if index >= len(self.reservasi_list):
            return

        reservasi = self.reservasi_list[index]

        dialog = DialogSelesaiReservasi(
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
        card.setObjectName("RoomCard")

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
        room_lbl.setObjectName("SectionTitle")

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
        
        detail_lbl.setTextFormat(Qt.RichText)
        detail_lbl.setWordWrap(True)
        detail_lbl.setObjectName("CardMeta")

        layout.addWidget(detail_lbl)

        # ==========================================================
        # KEPERLUAN
        # ==========================================================

        keperluan_lbl = QLabel(
            f"Keperluan:\n{keperluan}"
        )
        
        keperluan_lbl.setTextFormat(Qt.RichText)
        keperluan_lbl.setWordWrap(True)

        keperluan_lbl.setStyleSheet("""
            background:rgba(255, 255, 255, 0.05);
            border:1px solid rgba(255, 255, 255, 0.1);
            border-radius:12px;
            padding:12px;
            font-size:14px;
            """)

        keperluan_lbl.setWordWrap(True)

        layout.addWidget(keperluan_lbl)

        # ==========================================================
        # BUTTON
        # ==========================================================

        if status == "Pending":
            btn_row = QHBoxLayout()
            btn_row.addStretch()

            cancel_btn = QPushButton("Batalkan")
            cancel_btn.setStyleSheet("""
            QPushButton{
                background:#EF4444;
                color:white;
                border:none;
                border-radius:10px;
                padding:8px 20px;
                font-weight:600;
            }
            QPushButton:hover{
                background:#DC2626;
            }
            """)
            cancel_btn.setObjectName("btn_cancel")

            cancel_btn.clicked.connect(
                partial(self._on_batal_clicked, index)
            )
            btn_row.addWidget(cancel_btn)

            layout.addLayout(btn_row)
            
        if status == "Disetujui":
            btn_row = QHBoxLayout()
            btn_row.addStretch()

            selesai_btn = QPushButton("Selesaikan Reservasi")
            selesai_btn.setStyleSheet("""
                QPushButton{
                    background:#16A34A;
                    color:white;
                    border:none;
                    border-radius:10px;
                    padding:8px 20px;
                    font-weight:600;
                }
                QPushButton:hover{
                    background:#15803D;
                }
                """)
            selesai_btn.setObjectName("btn_selesai")

            cancel_btn = QPushButton("Batalkan")
            cancel_btn.setStyleSheet("""
            QPushButton{
                background:#EF4444;
                color:white;
                border:none;
                border-radius:10px;
                padding:8px 20px;
                font-weight:600;
            }
            QPushButton:hover{
                background:#DC2626;
            }
            """)
            cancel_btn.setObjectName("btn_cancel")

            selesai_btn.clicked.connect(
                partial(self._on_selesaikan_clicked, index)
            )

            cancel_btn.clicked.connect(
                partial(self._on_batal_clicked, index)
            )

            btn_row.addWidget(selesai_btn)
            btn_row.addWidget(cancel_btn)

            layout.addLayout(btn_row)

        # ==========================================================
        # ANIMASI DIHAPUS DEMI PERFORMA
        # ==========================================================
        return card


    def _clear_cards(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                try:
                    widget.setGraphicsEffect(None)
                except RuntimeError:
                    pass
                widget.deleteLater()