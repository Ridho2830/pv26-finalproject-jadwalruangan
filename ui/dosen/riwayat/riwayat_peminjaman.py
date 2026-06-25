# ui/dosen/riwayat/riwayat_peminjaman.py
"""
Halaman Riwayat Peminjaman untuk dosen.

Menampilkan semua reservasi milik user yang sudah selesai (status final):
Selesai, Ditolak, Dibatalkan.

Fitur:
- Daftar riwayat dari Supabase (filter pengguna_id + status final)
- Tampilkan: ruangan, tanggal, jam mulai-selesai, status, catatan admin
- Filter by status (Semua / Selesai / Ditolak / Dibatalkan)
- Filter by tanggal (rentang dari–sampai)
- Tombol reset filter
- Animasi fade-in staggered
- Empty state
"""


from PySide6.QtCore import (
    Qt,
    QDate,
)
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QScrollArea,
    QComboBox,
    QDateEdit,
)

from api.supabase import get_supabase_client
from utils.mode import theme_manager


# Status yang dianggap "riwayat" (sudah final / selesai)
STATUS_FINAL = ["Selesai", "Ditolak", "Dibatalkan"]

STATUS_STYLE = {
    "Selesai":    ("#EDE9FE", "#4C1D95", "🏁"),
    "Ditolak":    ("#FEE2E2", "#991B1B", "❌"),
    "Dibatalkan": ("#F3F4F6", "#6B7280", "🚫"),
}


class RiwayatPeminjamanPage(QWidget):
    def __init__(self, pengguna_id: int, pengguna_nama: str = "Dosen", parent=None):
        super().__init__(parent)

        self.pengguna_id   = pengguna_id
        self.pengguna_nama = pengguna_nama

        self.semua_riwayat = []   # data mentah dari Supabase
        self.cards         = []

        self._build_ui()
        self.refresh_data()
        
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

    # ==================================================================
    # BUILD UI
    # ==================================================================

    def _build_ui(self):
        self.setObjectName("riwayat_page")

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ------------------------------------------------------------------
        # HEADER
        # ------------------------------------------------------------------
        header_row = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title_lbl = QLabel("Riwayat Peminjaman")
        title_lbl.setObjectName("PageTitle")

        subtitle_lbl = QLabel(
            f"Daftar reservasi yang telah selesai, ditolak, atau dibatalkan "
            f"atas nama {self.pengguna_nama}."
        )
        subtitle_lbl.setObjectName("CardMeta")
        subtitle_lbl.setWordWrap(True)

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

        # ------------------------------------------------------------------
        # STATISTIK
        # ------------------------------------------------------------------
        self.stats_lbl = QLabel("Memuat data...")
        self.stats_lbl.setObjectName("stats_label")

        root.addWidget(self.stats_lbl)

        # ------------------------------------------------------------------
        # FILTER BAR
        # ------------------------------------------------------------------
        filter_frame = QFrame()
        filter_frame.setObjectName("filter_frame")

        filter_row = QHBoxLayout(filter_frame)
        filter_row.setContentsMargins(16, 12, 16, 12)
        filter_row.setSpacing(12)

        # Label
        filter_lbl = QLabel("Filter:")
        filter_lbl.setObjectName("filter_label")

        # Dropdown status
        self.status_combo = QComboBox()
        self.status_combo.setObjectName("filter_combo")
        self.status_combo.setCursor(Qt.PointingHandCursor)
        self.status_combo.addItem("Semua Status")
        for s in STATUS_FINAL:
            self.status_combo.addItem(s)
        self.status_combo.setFixedHeight(38)
        self.status_combo.currentIndexChanged.connect(self._apply_filter)

        # Label rentang tanggal
        dari_lbl = QLabel("Dari:")
        dari_lbl.setObjectName("filter_label")

        sampai_lbl = QLabel("Sampai:")
        sampai_lbl.setObjectName("filter_label")

        # Date picker dari
        self.date_dari = QDateEdit()
        self.date_dari.setObjectName("filter_date")
        self.date_dari.setCalendarPopup(True)
        self.date_dari.setDate(QDate.currentDate().addMonths(-3))
        self.date_dari.setFixedHeight(38)
        self.date_dari.dateChanged.connect(self._apply_filter)

        # Date picker sampai
        self.date_sampai = QDateEdit()
        self.date_sampai.setObjectName("filter_date")
        self.date_sampai.setCalendarPopup(True)
        self.date_sampai.setDate(QDate.currentDate())
        self.date_sampai.setFixedHeight(38)
        self.date_sampai.dateChanged.connect(self._apply_filter)

        # Tombol reset filter
        reset_btn = QPushButton("✕ Reset")
        reset_btn.setObjectName("btn_reset")
        reset_btn.setFixedHeight(38)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_filter)

        filter_row.addWidget(filter_lbl)
        filter_row.addWidget(self.status_combo)
        filter_row.addWidget(dari_lbl)
        filter_row.addWidget(self.date_dari)
        filter_row.addWidget(sampai_lbl)
        filter_row.addWidget(self.date_sampai)
        filter_row.addWidget(reset_btn)
        filter_row.addStretch()

        root.addWidget(filter_frame)

        # ------------------------------------------------------------------
        # HASIL FILTER INFO
        # ------------------------------------------------------------------
        self.result_lbl = QLabel("")
        self.result_lbl.setObjectName("result_label")

        root.addWidget(self.result_lbl)

        # ------------------------------------------------------------------
        # SCROLL AREA — daftar kartu
        # ------------------------------------------------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 8, 0)
        self.list_layout.setSpacing(14)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_widget)

        root.addWidget(scroll)

    # ==================================================================
    # REFRESH DATA (dari Supabase)
    # ==================================================================

    def refresh_data(self):
        self._clear_cards()
        self.semua_riwayat = []

        if hasattr(self, 'worker') and self.worker.isRunning():
            return
            
        self.stats_lbl.setText("Memuat data...")
        from utils.worker import Worker
        self.worker = Worker(self._fetch_riwayat_worker)
        self.worker.finished.connect(self._on_riwayat_fetched)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _fetch_riwayat_worker(self):
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        result = supabase.table("reservasi").select(
            "*,ruangan(id,nama,gedung,lantai,kapasitas)",
            f"pengguna_id=eq.{self.pengguna_id}&status=in.(Selesai,Ditolak,Dibatalkan)&order=tanggal.desc"
        )
        return result

    def _on_error(self, err_msg):
        self.stats_lbl.setText("Gagal memuat data")
        self.semua_riwayat = []
        print(f"[RiwayatPage] Error fetch data: {err_msg}")
        self._update_stats()
        self._apply_filter()

    def _on_riwayat_fetched(self, result):
        if isinstance(result, list):
            self.semua_riwayat = result
        else:
            self.semua_riwayat = []
            
        self._update_stats()
        self._apply_filter()

    # ==================================================================
    # FILTER
    # ==================================================================

    def _apply_filter(self):
        """Terapkan filter status dan rentang tanggal ke semua_riwayat."""
        self._clear_cards()
        self.cards = []

        status_filter = self.status_combo.currentText()
        date_dari     = self.date_dari.date()
        date_sampai   = self.date_sampai.date()

        filtered = []

        for r in self.semua_riwayat:
            # Filter status
            if status_filter != "Semua Status" and r.get("status") != status_filter:
                continue

            # Filter tanggal
            tanggal_str = r.get("tanggal", "")
            if tanggal_str:
                try:
                    qdate = QDate.fromString(tanggal_str, "yyyy-MM-dd")
                    if qdate < date_dari or qdate > date_sampai:
                        continue
                except Exception:
                    pass

            filtered.append(r)

        # Info jumlah hasil
        if filtered:
            self.result_lbl.setText(f"Menampilkan {len(filtered)} riwayat")
        else:
            self.result_lbl.setText("")

        if not filtered:
            self._show_empty_state(
                kosong_total=len(self.semua_riwayat) == 0
            )
            return

        for i, reservasi in enumerate(filtered):
            card = self._build_card(reservasi, i)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)
            self.cards.append(card)

    def _reset_filter(self):
        """Kembalikan semua filter ke default."""
        self.status_combo.setCurrentIndex(0)
        self.date_dari.setDate(QDate.currentDate().addMonths(-3))
        self.date_sampai.setDate(QDate.currentDate())
        # _apply_filter otomatis terpanggil lewat signal dateChanged / currentIndexChanged

    # ==================================================================
    # STATISTIK
    # ==================================================================

    def _update_stats(self):
        counts = {s: 0 for s in STATUS_FINAL}

        for r in self.semua_riwayat:
            s = r.get("status", "")
            if s in counts:
                counts[s] += 1

        total = len(self.semua_riwayat)

        if total == 0:
            self.stats_lbl.setText("Belum ada riwayat peminjaman")
        else:
            self.stats_lbl.setText(
                f"Total {total} riwayat  •  "
                f"🏁 {counts['Selesai']} Selesai  •  "
                f"❌ {counts['Ditolak']} Ditolak  •  "
                f"🚫 {counts['Dibatalkan']} Dibatalkan"
            )

    # ==================================================================
    # BUILD CARD
    # ==================================================================

    def _build_card(self, reservasi: dict, index: int) -> QFrame:
        card = QFrame()
        card.setObjectName("RoomCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        ruangan    = reservasi.get("ruangan") or {}
        nama_ruangan = ruangan.get("nama", "-")
        gedung       = ruangan.get("gedung", "-")
        lantai       = ruangan.get("lantai", "-")

        tanggal    = reservasi.get("tanggal", "-")
        jam_mulai  = reservasi.get("jam_mulai", "-")
        jam_selesai= reservasi.get("jam_selesai", "-")
        keperluan  = reservasi.get("keperluan", "-") or "-"
        status     = reservasi.get("status", "Selesai")

        # ---- baris atas: nama ruangan + badge status ----
        top_row = QHBoxLayout()

        room_lbl = QLabel(nama_ruangan)
        room_lbl.setObjectName("SectionTitle")

        bg, fg, icon = STATUS_STYLE.get(status, ("#E5E7EB", "#111827", "•"))
        badge = QLabel(f"{icon} {status}")
        badge.setStyleSheet(
            f"background:{bg}; color:{fg}; padding:5px 12px; "
            f"border-radius:10px; font-size:12px; font-weight:700;"
        )

        top_row.addWidget(room_lbl)
        top_row.addStretch()
        top_row.addWidget(badge)

        layout.addLayout(top_row)

        # ---- separator tipis ----
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: rgba(255, 255, 255, 0.1);")
        layout.addWidget(sep)

        # ---- grid info 2 kolom ----
        info_row = QHBoxLayout()
        info_row.setSpacing(32)

        left_info = QLabel(
            f"<b>📍 Lokasi</b><br>"
            f"Gedung {gedung} • Lantai {lantai}<br><br>"
            f"<b>📅 Tanggal</b><br>"
            f"{tanggal}"
        )
        left_info.setObjectName("card_info")
        left_info.setTextFormat(Qt.RichText)

        right_info = QLabel(
            f"<b>🕒 Waktu</b><br>"
            f"{jam_mulai} – {jam_selesai}<br><br>"
            f"<b>📝 Keperluan</b><br>"
            f"{keperluan}"
        )
        right_info.setObjectName("card_info")
        right_info.setTextFormat(Qt.RichText)
        right_info.setWordWrap(True)

        info_row.addWidget(left_info, 1)
        info_row.addWidget(right_info, 1)

        layout.addLayout(info_row)

        # ---- catatan admin (tampil hanya jika ada isi) ----
        # Catatan admin bisa di kolom 'catatan_admin' atau 'catatan'
        catatan_admin = (
            reservasi.get("catatan_admin")
            or reservasi.get("catatan")
            or ""
        )
        if catatan_admin.strip():
            catatan_frame = QFrame()
            catatan_frame.setObjectName("catatan_frame")

            catatan_layout = QHBoxLayout(catatan_frame)
            catatan_layout.setContentsMargins(12, 10, 12, 10)
            catatan_layout.setSpacing(10)

            icon_lbl = QLabel("💬")
            icon_lbl.setStyleSheet(
                "font-size:18px; background:transparent;"
            )
            icon_lbl.setFixedWidth(28)

            catatan_lbl = QLabel(
                f"<b>Catatan Admin:</b> {catatan_admin}"
            )
            catatan_lbl.setObjectName("catatan_text")
            catatan_lbl.setTextFormat(Qt.RichText)
            catatan_lbl.setWordWrap(True)

            catatan_layout.addWidget(icon_lbl)
            catatan_layout.addWidget(catatan_lbl)

            layout.addWidget(catatan_frame)

        # ---- bukti laporan ----
        bukti_frame = QFrame()
        bukti_frame.setObjectName("RoomCard")

        bukti_layout = QVBoxLayout(bukti_frame)
        bukti_layout.setContentsMargins(12, 12, 12, 12)

        judul = QLabel("📷 Bukti Laporan (Sebelum & Sesudah)")
        judul.setObjectName("SectionTitle")
        bukti_layout.addWidget(judul)

        foto_sebelum = reservasi.get("foto_sebelum")
        foto_sesudah = reservasi.get("foto_sesudah")

        foto_row = QHBoxLayout()
        foto_row.setSpacing(16)

        def setup_gambar_label(url, placeholder_text):
            """Load foto dari URL Supabase, tampilkan preview + tombol buka browser."""
            from PySide6.QtWidgets import QVBoxLayout, QWidget
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl

            container = QWidget()
            container.setStyleSheet("background: transparent;")
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(8)

            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumHeight(200)

            if url and url != "-":
                try:
                    import requests
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(resp.content)
                        if not pixmap.isNull():
                            lbl.setPixmap(pixmap.scaled(260, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                            lbl.setStyleSheet("background:white; border:1px solid #E5E7EB; border-radius:14px; padding:10px;")
                        else:
                            raise ValueError("Pixmap null")
                    else:
                        raise ValueError(f"HTTP {resp.status_code}")
                except Exception:
                    lbl.setText(f"🖼\n\n{placeholder_text} tidak dapat dibuka")
                    lbl.setStyleSheet("background:#F9FAFB; border:2px dashed #CBD5E1; border-radius:14px; color:#6B7280; font-size:14px; font-weight:600;")

                btn_buka = QPushButton("🌐 Buka di Browser")
                btn_buka.setCursor(Qt.PointingHandCursor)
                btn_buka.setFixedHeight(32)
                btn_buka.setStyleSheet(
                    "QPushButton{background:#4f46e5;color:white;border:none;"
                    "border-radius:8px;font-size:11px;font-weight:700;padding:0 10px;}"
                    "QPushButton:hover{background:#4338ca;}"
                )
                btn_buka.clicked.connect(lambda checked=False, u=url: QDesktopServices.openUrl(QUrl(u)))
                vbox.addWidget(lbl)
                vbox.addWidget(btn_buka, alignment=Qt.AlignCenter)
            else:
                lbl.setText(f"📷\n\nBelum ada {placeholder_text}")
                lbl.setStyleSheet("background:#F9FAFB; border:2px dashed #CBD5E1; border-radius:14px; color:#94A3B8; font-size:14px; font-weight:600;")
                vbox.addWidget(lbl)

            return container

        gambar_sebelum = setup_gambar_label(foto_sebelum, "Foto Sebelum")
        gambar_sesudah = setup_gambar_label(foto_sesudah, "Foto Sesudah")

        foto_row.addWidget(gambar_sebelum)
        foto_row.addWidget(gambar_sesudah)
        bukti_layout.addLayout(foto_row)

        layout.addWidget(bukti_frame)
        return card

    # ==================================================================
    # EMPTY STATE
    # ==================================================================

    def _show_empty_state(self, kosong_total: bool = False):
        if kosong_total:
            icon_txt  = "📭"
            title_txt = "Belum Ada Riwayat"
            desc_txt  = "Kamu belum memiliki riwayat peminjaman ruangan."
        else:
            icon_txt  = "🔍"
            title_txt = "Tidak Ada Hasil"
            desc_txt  = "Tidak ada riwayat yang sesuai dengan filter yang dipilih."

        icon = QLabel(icon_txt)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            "font-size:56px; padding-top:60px; background:transparent;"
        )

        title = QLabel(title_txt)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size:20px; font-weight:700; background:transparent;"
        )

        desc = QLabel(desc_txt)
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(
            "font-size:14px; color:#6b7280; background:transparent;"
        )

        for w in [icon, title, desc]:
            self.list_layout.insertWidget(self.list_layout.count() - 1, w)

    # ==================================================================
    # CLEAR CARDS
    # ==================================================================

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