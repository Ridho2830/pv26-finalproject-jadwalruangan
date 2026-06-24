# ui/admin/foto/foto_dokumentasi_widget.py
"""
Halaman Lihat Foto Dokumentasi — Admin
Fitur:
  - Galeri foto per reservasi (sebelum & sesudah)
  - Filter by ruangan dan tanggal
  - Tombol hapus foto
  - Tombol tandai reservasi 'Ada Masalah'
"""

from PySide6.QtCore import Qt, QUrl, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QDateEdit, QMessageBox,
    QGridLayout, QSizePolicy, QDialog
)
from PySide6.QtGui import QPixmap, QDesktopServices, QCursor
from api.supabase import get_supabase_client, get_storage_bucket
from utils.mode import theme_manager


# ──────────────────────────────────────────────────────────────
#  CARD FOTO PER RESERVASI
# ──────────────────────────────────────────────────────────────

class FotoCard(QFrame):
    def __init__(self, reservasi: dict, on_masalah, on_delete, parent=None):
        super().__init__(parent)
        self.reservasi = reservasi
        self.setObjectName("FotoCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(340)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self._build(on_masalah, on_delete)

    def _build(self, on_masalah, on_delete):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        r = self.reservasi
        ruangan  = (r.get("ruangan")  or {}).get("nama",  r.get("ruangan_id",  "?"))
        peminjam = (r.get("pengguna") or {}).get("nama",  r.get("pengguna_id", "?"))
        tanggal  = r.get("tanggal", "-")
        jam      = f"{str(r.get('jam_mulai',''))[:5]} – {str(r.get('jam_selesai',''))[:5]}"
        status   = r.get("status", "-")

        # ── Info reservasi ──
        lbl_ruangan = QLabel(f"🏢  {ruangan}")
        lbl_ruangan.setStyleSheet("font-weight: 800; font-size: 13px; background: transparent;")

        lbl_peminjam = QLabel(f"👤  {peminjam}")
        lbl_peminjam.setStyleSheet("font-size: 11px; background: transparent;")

        lbl_waktu = QLabel(f"📅  {tanggal}   🕒  {jam}")
        lbl_waktu.setStyleSheet("font-size: 11px; background: transparent;")

        STATUS_STYLE = {
            "Disetujui" : "color:#16a34a;",
            "Selesai"   : "color:#4f46e5;",
            "Ada Masalah": "color:#ef4444; font-weight:700;",
        }
        lbl_status = QLabel(f"Status: {status}")
        lbl_status.setStyleSheet(
            STATUS_STYLE.get(status, "color:#94a3b8;") + " font-size:11px; background:transparent;"
        )

        layout.addWidget(lbl_ruangan)
        layout.addWidget(lbl_peminjam)
        layout.addWidget(lbl_waktu)
        layout.addWidget(lbl_status)

        # ── Foto sebelum & sesudah ──
        foto_row = QHBoxLayout()
        foto_row.setSpacing(8)

        url_sebelum = r.get("foto_sebelum") or r.get("foto_laporan")
        url_sesudah = r.get("foto_sesudah")

        foto_row.addLayout(self._foto_box("Sebelum", url_sebelum))
        foto_row.addLayout(self._foto_box("Sesudah", url_sesudah))
        layout.addLayout(foto_row)

        # ── Tombol aksi ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        if status != "Ada Masalah":
            btn_masalah = QPushButton("⚠️ Ada Masalah")
            btn_masalah.setCursor(QCursor(Qt.PointingHandCursor))
            btn_masalah.setFixedHeight(32)
            btn_masalah.setStyleSheet(
                "QPushButton{background:#fef3c7;color:#92400e;border:1px solid #fcd34d;"
                "border-radius:6px;font-weight:700;font-size:11px;padding:0 8px;}"
                "QPushButton:hover{background:#fde68a;}"
            )
            btn_masalah.clicked.connect(lambda: on_masalah(r))
            btn_row.addWidget(btn_masalah)

        btn_hapus = QPushButton("🗑 Hapus Foto")
        btn_hapus.setCursor(QCursor(Qt.PointingHandCursor))
        btn_hapus.setFixedHeight(32)
        btn_hapus.setStyleSheet(
            "QPushButton{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;"
            "border-radius:6px;font-weight:700;font-size:11px;padding:0 8px;}"
            "QPushButton:hover{background:#fecaca;}"
        )
        btn_hapus.clicked.connect(lambda: on_delete(r))
        btn_row.addWidget(btn_hapus)
        btn_row.addStretch()

        layout.addLayout(btn_row)

    def _foto_box(self, label: str, url: str | None) -> QVBoxLayout:
        box = QVBoxLayout()
        box.setSpacing(4)

        lbl_title = QLabel(label)
        lbl_title.setStyleSheet(
            "font-size:10px; font-weight:700; color:#94a3b8; background:transparent;"
        )
        lbl_title.setAlignment(Qt.AlignCenter)

        preview = QLabel()
        preview.setFixedSize(130, 90)
        preview.setAlignment(Qt.AlignCenter)
        preview.setStyleSheet(
            "background:rgba(100,116,139,0.1); border:1.5px dashed #94a3b8;"
            "border-radius:8px;"
        )

        if url:
            preview.setText("🔗 Klik untuk buka")
            preview.setStyleSheet(
                "background:rgba(79,70,229,0.1); border:1.5px solid #a5b4fc;"
                "border-radius:8px; font-size:10px; color:#6366f1;"
            )
            preview.setCursor(QCursor(Qt.PointingHandCursor))
            preview.mousePressEvent = lambda e, u=url: QDesktopServices.openUrl(QUrl(u))
        else:
            preview.setText("—\nTidak ada\nfoto")
            preview.setStyleSheet(
                "background:rgba(100,116,139,0.07); border:1.5px dashed #475569;"
                "border-radius:8px; font-size:10px; color:#64748b;"
            )

        box.addWidget(lbl_title, alignment=Qt.AlignCenter)
        box.addWidget(preview,   alignment=Qt.AlignCenter)
        return box


# ──────────────────────────────────────────────────────────────
#  MAIN WIDGET
# ──────────────────────────────────────────────────────────────

class FotoDokumentasiWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FotoDokumentasiWidget")
        self.supabase = get_supabase_client()
        self._all_data: list = []
        self._room_list: list = []
        self._build_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(14)

        # ── Header ──
        header = QHBoxLayout()
        lbl_title = QLabel("📸 Foto Dokumentasi Reservasi")
        lbl_title.setStyleSheet(
            "font-size:22px; font-weight:800; background:transparent;"
        )
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setCursor(QCursor(Qt.PointingHandCursor))
        btn_refresh.setFixedHeight(36)
        btn_refresh.setStyleSheet(
            "QPushButton{background:#4f46e5;color:white;border:none;border-radius:8px;"
            "padding:0 16px;font-weight:700;}"
            "QPushButton:hover{background:#4338ca;}"
        )
        btn_refresh.clicked.connect(self.refresh_data)
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(btn_refresh)
        root.addLayout(header)

        # ── Filter bar ──
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)

        filter_bar.addWidget(QLabel("Ruangan:"))
        self.cb_ruangan = QComboBox()
        self.cb_ruangan.setFixedWidth(200)
        self.cb_ruangan.addItem("Semua Ruangan", None)
        self.cb_ruangan.currentIndexChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.cb_ruangan)

        filter_bar.addWidget(QLabel("Tanggal mulai:"))
        self.de_start = QDateEdit(QDate.currentDate().addDays(-30))
        self.de_start.setCalendarPopup(True)
        self.de_start.setDisplayFormat("dd/MM/yyyy")
        self.de_start.dateChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.de_start)

        filter_bar.addWidget(QLabel("s/d"))
        self.de_end = QDateEdit(QDate.currentDate())
        self.de_end.setCalendarPopup(True)
        self.de_end.setDisplayFormat("dd/MM/yyyy")
        self.de_end.dateChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.de_end)

        filter_bar.addStretch()
        self.lbl_count = QLabel("0 foto")
        self.lbl_count.setStyleSheet("color:#64748b; font-size:12px; background:transparent;")
        filter_bar.addWidget(self.lbl_count)

        root.addLayout(filter_bar)

        # ── Scroll area galeri ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea{background:transparent;}")

        self.gallery_widget = QWidget()
        self.gallery_widget.setStyleSheet("background:transparent;")
        self.gallery_layout = QGridLayout(self.gallery_widget)
        self.gallery_layout.setContentsMargins(0, 0, 0, 0)
        self.gallery_layout.setSpacing(16)

        self.scroll.setWidget(self.gallery_widget)
        root.addWidget(self.scroll, stretch=1)

    # ─── DATA ────────────────────────────────────────────────

    def refresh_data(self):
        try:
            start = self.de_start.date().toString("yyyy-MM-dd")
            end   = self.de_end.date().toString("yyyy-MM-dd")

            data = self.supabase.table("reservasi").select(
                "*,pengguna(nama,role),ruangan(nama)",
                f"tanggal=gte.{start}&tanggal=lte.{end}"
            )
            if not isinstance(data, list):
                data = []

            # Hanya tampilkan yang punya foto
            self._all_data = [
                r for r in data
                if r.get("foto_sebelum") or r.get("foto_sesudah") or r.get("foto_laporan")
            ]

            # Update dropdown ruangan
            rooms_seen = {}
            for r in self._all_data:
                rid  = r.get("ruangan_id")
                rnam = (r.get("ruangan") or {}).get("nama", str(rid))
                if rid and rid not in rooms_seen:
                    rooms_seen[rid] = rnam

            prev = self.cb_ruangan.currentData()
            self.cb_ruangan.blockSignals(True)
            self.cb_ruangan.clear()
            self.cb_ruangan.addItem("Semua Ruangan", None)
            for rid, rnam in sorted(rooms_seen.items(), key=lambda x: x[1]):
                self.cb_ruangan.addItem(rnam, rid)
            # restore previous selection
            for i in range(self.cb_ruangan.count()):
                if self.cb_ruangan.itemData(i) == prev:
                    self.cb_ruangan.setCurrentIndex(i)
                    break
            self.cb_ruangan.blockSignals(False)

            self._apply_filter()

        except Exception as e:
            print(f"[FotoDokumentasi] Error: {e}")
            QMessageBox.critical(self, "Error", f"Gagal memuat data:\n{e}")

    def _apply_filter(self):
        ruangan_filter = self.cb_ruangan.currentData()

        filtered = self._all_data
        if ruangan_filter is not None:
            filtered = [
                r for r in filtered
                if str(r.get("ruangan_id")) == str(ruangan_filter)
            ]

        self._render_gallery(filtered)

    def _render_gallery(self, data: list):
        # Hapus semua widget lama
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.lbl_count.setText(f"{len(data)} reservasi dengan foto")

        if not data:
            lbl_empty = QLabel("Tidak ada foto dokumentasi untuk filter ini.")
            lbl_empty.setAlignment(Qt.AlignCenter)
            lbl_empty.setStyleSheet("color:#64748b; font-size:14px; background:transparent;")
            self.gallery_layout.addWidget(lbl_empty, 0, 0)
            return

        COLS = 3
        for idx, r in enumerate(data):
            card = FotoCard(
                r,
                on_masalah=self._tandai_masalah,
                on_delete=self._hapus_foto
            )
            row = idx // COLS
            col = idx % COLS
            self.gallery_layout.addWidget(card, row, col, Qt.AlignTop)

        # Isi sisa grid agar alignment kiri
        total = len(data)
        remainder = total % COLS
        if remainder:
            for col in range(remainder, COLS):
                self.gallery_layout.setColumnStretch(col, 1)

    # ─── AKSI ────────────────────────────────────────────────

    def _tandai_masalah(self, reservasi: dict):
        rid  = reservasi.get("id")
        nama = (reservasi.get("ruangan") or {}).get("nama", str(rid))
        reply = QMessageBox.question(
            self, "Tandai Ada Masalah",
            f"Tandai reservasi ruangan {nama} sebagai 'Ada Masalah'?\n\n"
            f"Status akan diubah dan admin dapat menindaklanjuti.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            result = self.supabase.table("reservasi").update(
                {"status": "Ada Masalah"}, f"id=eq.{rid}"
            )
            if result is not None:
                QMessageBox.information(self, "Berhasil", "Reservasi ditandai 'Ada Masalah'.")
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Gagal", "Gagal mengubah status.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _hapus_foto(self, reservasi: dict):
        rid  = reservasi.get("id")
        nama = (reservasi.get("ruangan") or {}).get("nama", str(rid))
        reply = QMessageBox.question(
            self, "Hapus Foto",
            f"Hapus semua foto dokumentasi reservasi ruangan {nama}?\n\n"
            f"Data foto akan dihapus dari database (file di storage tidak terhapus).",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            result = self.supabase.table("reservasi").update(
                {"foto_sebelum": None, "foto_sesudah": None, "foto_laporan": None},
                f"id=eq.{rid}"
            )
            if result is not None:
                QMessageBox.information(self, "Berhasil", "Foto berhasil dihapus dari database.")
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Gagal", "Gagal menghapus foto.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ─── THEME ───────────────────────────────────────────────

    def apply_theme(self):
        self.setStyleSheet(theme_manager.get_stylesheet())
