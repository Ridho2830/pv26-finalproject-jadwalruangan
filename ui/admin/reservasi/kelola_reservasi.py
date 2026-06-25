"""
Kelola Reservasi — Admin Dashboard ReservasiKampus
===================================================
Standalone widget: tabel reservasi dengan filter tabs,
form CRUD, dan quick actions (setujui / tolak).
"""

from datetime import date, datetime
from PySide6.QtCore import Qt, Signal, QUrl, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QLineEdit,
    QComboBox, QFrame, QAbstractItemView, QDateEdit,
    QTimeEdit, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QDesktopServices, QPixmap
from utils.mode import theme_manager
from api.supabase import get_supabase_client


# ──────────────────────────────────────────────
#  STATUS BADGE COLORS
# ──────────────────────────────────────────────
STATUS_COLORS = {
    "Pending":    ("#F59E0B", "rgba(245,158,11,0.12)", "#78350F"),
    "Disetujui":  ("#10B981", "rgba(16,185,129,0.12)", "#064E3B"),
    "Ditolak":    ("#EF4444", "rgba(239,68,68,0.12)",  "#7F1D1D"),
    "Dibatalkan": ("#6B7280", "rgba(107,114,128,0.12)","#1F2937"),
    "Selesai":    ("#3B82F6", "rgba(59,130,246,0.12)", "#1E3A8A"),
}

FILTER_TABS = ["Semua", "Mahasiswa", "Dosen", "Pending", "Riwayat"]


# ──────────────────────────────────────────────
#  FILTER TAB BUTTON
# ──────────────────────────────────────────────
class FilterTabButton(QPushButton):
    """Tombol tab filter yang bisa di-toggle aktif."""
    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        self._active = False
        self.setCheckable(False)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(34)
        self.setMinimumWidth(80)
        self._apply_style()

    def set_active(self, v: bool):
        self._active = v
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(
                "QPushButton{background:#4f46e5;color:white;border:none;"
                "border-radius:8px;padding:6px 16px;font-weight:700;font-size:12px;}"
                "QPushButton:hover{background:#4338ca;}"
            )
        else:
            self.setStyleSheet(
                "QPushButton{background:rgba(100,100,120,0.12);color:#94a3b8;border:none;"
                "border-radius:8px;padding:6px 16px;font-weight:600;font-size:12px;}"
                "QPushButton:hover{background:rgba(100,100,120,0.22);color:#e2e8f0;}"
            )


# ──────────────────────────────────────────────
#  KELOLA RESERVASI WIDGET
# ──────────────────────────────────────────────
class KelolaReservasiWidget(QWidget):
    """Widget utama untuk mengelola CRUD Reservasi."""

    # Signal supaya dashboard bisa refresh KPI setelah perubahan
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._current_filter = "Semua"

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 32, 32, 32)
        self.main_layout.setSpacing(20)

        self._build_header()
        self._build_filter_tabs()
        self._build_table()

        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    # ─── BUILD UI ────────────────────────────────
    def _build_header(self):
        header_bar = QHBoxLayout()

        header_title = QLabel("Kelola Reservasi")
        header_title.setStyleSheet(
            "font-size: 22px; font-weight: 800; background-color: transparent;"
        )

        self.add_btn = QPushButton("➕ Tambah Reservasi")
        self.add_btn.setObjectName("login_btn")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setFixedHeight(38)
        self.add_btn.clicked.connect(lambda: self.open_form_dialog())

        self.btn_export_csv = QPushButton("📄 Export CSV")
        self.btn_export_csv.setCursor(Qt.PointingHandCursor)
        self.btn_export_csv.setFixedHeight(38)
        self.btn_export_csv.setStyleSheet(
            "QPushButton{background:#0ea5e9;color:white;border:none;border-radius:8px;"
            "padding:0 14px;font-weight:700;font-size:12px;}"
            "QPushButton:hover{background:#0284c7;}"
        )
        self.btn_export_csv.clicked.connect(self._export_csv)

        self.btn_export_pdf = QPushButton("📑 Export PDF")
        self.btn_export_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_export_pdf.setFixedHeight(38)
        self.btn_export_pdf.setStyleSheet(
            "QPushButton{background:#ef4444;color:white;border:none;border-radius:8px;"
            "padding:0 14px;font-weight:700;font-size:12px;}"
            "QPushButton:hover{background:#dc2626;}"
        )
        self.btn_export_pdf.clicked.connect(self._export_pdf)

        header_bar.addWidget(header_title)
        header_bar.addStretch()
        header_bar.addWidget(self.btn_export_csv)
        header_bar.addWidget(self.btn_export_pdf)
        header_bar.addWidget(self.add_btn)
        self.main_layout.addLayout(header_bar)

    def _build_filter_tabs(self):
        tab_row = QHBoxLayout()
        tab_row.setSpacing(6)

        self.filter_buttons = []
        for i, label in enumerate(FILTER_TABS):
            btn = FilterTabButton(label)
            btn.set_active(i == 0)
            btn.clicked.connect(lambda checked=False, lbl=label: self._on_filter(lbl))
            tab_row.addWidget(btn)
            self.filter_buttons.append(btn)

        tab_row.addStretch()
        self.main_layout.addLayout(tab_row)

    def _build_table(self):
        self.table = QTableWidget()
        self.table.setStyleSheet("QTableWidget { border: none; background: transparent; }")
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Nama Peminjam", "Role", "Ruangan", "Tanggal",
            "Jam", "Keperluan", "Status", "Catatan Admin", "Aksi"
        ])

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)       # Nama
        header.setSectionResizeMode(1, QHeaderView.Interactive)       # Role
        header.setSectionResizeMode(2, QHeaderView.Interactive)       # Ruangan
        header.setSectionResizeMode(3, QHeaderView.Interactive)       # Tanggal
        header.setSectionResizeMode(4, QHeaderView.Interactive)       # Jam
        header.setSectionResizeMode(5, QHeaderView.Stretch)           # Keperluan
        header.setSectionResizeMode(6, QHeaderView.Interactive)       # Status
        header.setSectionResizeMode(7, QHeaderView.Interactive)       # Catatan
        header.setSectionResizeMode(8, QHeaderView.Fixed)             # Aksi

        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 160)
        self.table.setColumnWidth(8, 310)

        self.table.verticalHeader().setDefaultSectionSize(56)

        self.table_container = QFrame()

        container_layout = QVBoxLayout(self.table_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.table)

        self.main_layout.addWidget(self.table_container)

    # ─── FILTER LOGIC ────────────────────────────
    def _on_filter(self, label: str):
        self._current_filter = label
        for btn in self.filter_buttons:
            btn.set_active(btn.text() == label)
        self.load_data()

    # ─── DATA LOADING ────────────────────────────
    def load_data(self, filter_override=None):
        """Memuat data reservasi dari Supabase secara asinkron."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            return

        self.table.setRowCount(0)
        active_filter = filter_override or self._current_filter

        from utils.worker import Worker
        self.worker = Worker(self._fetch_reservasi_worker, active_filter)
        self.worker.finished.connect(self._on_reservasi_fetched)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _fetch_reservasi_worker(self, active_filter):
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        query = "*,pengguna(nama,role),ruangan(nama)"
        filters = ""
        if active_filter == "Pending":
            filters = "status=eq.Pending"
        elif active_filter == "Riwayat":
            filters = "status=in.(Selesai,Ditolak,Dibatalkan)"

        result = supabase.table("reservasi").select(query, filters)
        if not result:
            result = []

        if active_filter == "Mahasiswa":
            result = [r for r in result if r.get("pengguna", {}).get("role", "").lower() == "mahasiswa"]
        elif active_filter == "Dosen":
            result = [r for r in result if r.get("pengguna", {}).get("role", "").lower() == "dosen"]

        result.sort(key=lambda x: (x.get("tanggal", ""), x.get("jam_mulai", "")), reverse=True)
        return result

    def _on_error(self, err_msg):
        QMessageBox.critical(self, "Database Error", f"Gagal memproses data!\n{err_msg}")

    def _on_reservasi_fetched(self, result):
        self._last_reservasi_data = result  # simpan untuk export
        self._active_filter = self._current_filter
        self.table.setRowCount(0)
        for row_idx, reservasi in enumerate(result):
            self.table.insertRow(row_idx)
            for c in range(self.table.columnCount()):
                self.table.setItem(row_idx, c, QTableWidgetItem())
            self._populate_row(row_idx, reservasi)

    def _populate_row(self, row_idx: int, r: dict):
        """Mengisi satu baris tabel dengan data reservasi."""
        pengguna = r.get("pengguna") or {}
        ruangan = r.get("ruangan") or {}

        # Kolom 0: Nama Peminjam
        self._set_cell_widget(row_idx, 0, pengguna.get("nama", "-"),
                              bold=True, font_size=13)
        # Kolom 1: Role
        role = pengguna.get("role", "-")
        self._set_cell_widget(row_idx, 1, role, color="#6b6b80", font_size=12)

        # Kolom 2: Ruangan
        self._set_cell_widget(row_idx, 2, ruangan.get("nama", "-"),
                              bold=True, font_size=13)

        # Kolom 3: Tanggal
        tanggal = r.get("tanggal", "-")
        self._set_cell_widget(row_idx, 3, tanggal, color="#6b6b80", font_size=12)

        # Kolom 4: Jam
        jam = f"{r.get('jam_mulai', '?')} – {r.get('jam_selesai', '?')}"
        self._set_cell_widget(row_idx, 4, jam, font_size=12)

        # Kolom 5: Keperluan
        self._set_cell_widget(row_idx, 5, r.get("keperluan", "-"),
                              color="#6b6b80", font_size=12, word_wrap=True)

        # Kolom 6: Status Badge
        status = r.get("status", "Pending")
        accent, bg, txt = STATUS_COLORS.get(status, STATUS_COLORS["Pending"])
        badge_w = QWidget()
        badge_l = QHBoxLayout(badge_w)
        badge_l.setContentsMargins(4, 0, 4, 0)
        badge = QLabel(status)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"color:{txt}; background:{bg}; border-radius:8px;"
            f"padding:4px 12px; font-weight:700; font-size:11px;"
            f"border: 1px solid {accent}40;"
        )
        badge_l.addWidget(badge)
        badge_l.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_idx, 6, badge_w)

        # Kolom 7: Catatan Admin
        self._set_cell_widget(row_idx, 7, r.get("catatan_admin", "-") or "-",
                              color="#6b6b80", font_size=11)

        # Kolom 8: Aksi
        self._add_action_buttons(row_idx, r)

    def _set_cell_widget(self, row, col, text, bold=False, font_size=13,
                         color=None, word_wrap=False):
        """Helper untuk membuat cell widget dengan label."""
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(12, 0, 12, 0)
        lbl = QLabel(str(text))

        style = f"font-size: {font_size}px; background-color: transparent;"
        if bold:
            style += " font-weight: 800;"
        if color:
            style += f" color: {color};"
        lbl.setStyleSheet(style)
        if word_wrap:
            lbl.setWordWrap(True)

        layout.addWidget(lbl)
        self.table.setCellWidget(row, col, w)

    def _add_action_buttons(self, row_idx: int, reservasi: dict):
        """Membuat tombol aksi: Edit, Hapus, dan (Setujui/Tolak jika Pending)."""
        actions_w = QWidget()
        actions_w.setStyleSheet("QWidget { background-color: transparent; }")
        actions_l = QHBoxLayout(actions_w)
        actions_l.setContentsMargins(6, 2, 6, 2)
        actions_l.setSpacing(6)

        reservasi_id = reservasi.get("id")
        status = reservasi.get("status", "")

        # Tombol Setujui & Tolak hanya muncul kalau Pending
        if status == "Pending":
            btn_approve = QPushButton("✅ Setujui")
            btn_approve.setCursor(Qt.PointingHandCursor)
            btn_approve.setFixedHeight(26)
            btn_approve.setStyleSheet(
                "QPushButton{background:#10B981;color:white;border:none;"
                "border-radius:6px;padding:2px 10px;font-weight:700;font-size:11px;}"
                "QPushButton:hover{background:#059669;}"
            )
            btn_approve.clicked.connect(
                lambda _, rid=reservasi_id: self.quick_approve(rid))
            actions_l.addWidget(btn_approve)

            btn_reject = QPushButton("❌ Tolak")
            btn_reject.setCursor(Qt.PointingHandCursor)
            btn_reject.setFixedHeight(26)
            btn_reject.setStyleSheet(
                "QPushButton{background:#EF4444;color:white;border:none;"
                "border-radius:6px;padding:2px 10px;font-weight:700;font-size:11px;}"
                "QPushButton:hover{background:#DC2626;}"
            )
            btn_reject.clicked.connect(
                lambda _, rid=reservasi_id: self.quick_reject(rid))
            actions_l.addWidget(btn_reject)

        # Tombol Dokumentasi — muncul kalau status Selesai (ada foto atau tidak)
        if status == "Selesai":
            has_foto = (
                reservasi.get("foto_sebelum") or
                reservasi.get("foto_sesudah") or
                reservasi.get("foto_laporan")
            )
            btn_dok = QPushButton("📸 Dokumentasi")
            btn_dok.setCursor(Qt.PointingHandCursor)
            btn_dok.setFixedHeight(26)
            if has_foto:
                btn_dok.setStyleSheet(
                    "QPushButton{background:#6366f1;color:white;border:none;"
                    "border-radius:6px;padding:2px 10px;font-weight:700;font-size:11px;}"
                    "QPushButton:hover{background:#4f46e5;}"
                )
            else:
                # Abu-abu kalau belum ada foto
                btn_dok.setStyleSheet(
                    "QPushButton{background:#475569;color:#94a3b8;border:none;"
                    "border-radius:6px;padding:2px 10px;font-weight:700;font-size:11px;}"
                    "QPushButton:hover{background:#334155;}"
                )
                btn_dok.setToolTip("Belum ada foto dokumentasi")
            btn_dok.clicked.connect(
                lambda _, r=reservasi: self._show_dokumentasi(r))
            actions_l.addWidget(btn_dok)

        # Edit & Hapus selalu ada
        btn_edit = QPushButton("✏️ Edit")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet("QPushButton { background-color: #f59e0b; color: white; border-radius: 6px; font-weight: bold; padding: 2px 10px; font-size: 11px; } QPushButton:hover { background-color: #d97706; }")
        btn_edit.setFixedHeight(26)
        btn_edit.clicked.connect(
            lambda _, r=reservasi: self.edit_reservasi(r))
        actions_l.addWidget(btn_edit)

        btn_delete = QPushButton("🗑️ Hapus")
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet("QPushButton { background-color: #ef4444; color: white; border-radius: 6px; font-weight: bold; padding: 2px 10px; font-size: 11px; } QPushButton:hover { background-color: #dc2626; }")
        btn_delete.setFixedHeight(26)
        btn_delete.clicked.connect(
            lambda _, r=reservasi: self.delete_reservasi(r))
        actions_l.addWidget(btn_delete)

        self.table.setCellWidget(row_idx, 8, actions_w)

    # ─── QUICK ACTIONS ───────────────────────────
    def quick_approve(self, reservasi_id: int):
        """PATCH status → Disetujui setelah konfirmasi."""
        reply = QMessageBox.question(
            self, "Konfirmasi Setujui",
            "Apakah Anda yakin ingin menyetujui reservasi ini?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._update_status(reservasi_id, "Disetujui")

    def quick_reject(self, reservasi_id: int):
        """PATCH status → Ditolak setelah konfirmasi."""
        reply = QMessageBox.question(
            self, "Konfirmasi Tolak",
            "Apakah Anda yakin ingin menolak reservasi ini?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._update_status(reservasi_id, "Ditolak")

    def _update_status(self, reservasi_id: int, new_status: str):
        """Helper untuk update status reservasi secara asinkron."""
        if hasattr(self, 'status_worker') and self.status_worker.isRunning():
            return

        from utils.worker import Worker
        self.status_worker = Worker(self._update_status_worker, reservasi_id, new_status)
        self.status_worker.finished.connect(lambda res: self._on_status_finished(res, new_status))
        self.status_worker.error.connect(self._on_error)
        self.status_worker.start()

    def _update_status_worker(self, reservasi_id, new_status):
        from api.supabase import get_supabase_client
        return get_supabase_client().table("reservasi").update({"status": new_status}, f"id=eq.{reservasi_id}")

    def _on_status_finished(self, res, new_status):
        if res is not None:
            QMessageBox.information(
                self, "Sukses",
                f"Status reservasi berhasil diubah ke '{new_status}'."
            )
            self.load_data()
            self.data_changed.emit()
        else:
            QMessageBox.warning(self, "Gagal", "Gagal mengubah status reservasi.")

    # ─── CRUD ────────────────────────────────────
    def open_form_dialog(self, default_ruangan_id=None):
        """Buka form tambah reservasi baru."""
        dialog = ReservasiFormDialog(parent=self, default_ruangan_id=default_ruangan_id)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
            self.data_changed.emit()

    def edit_reservasi(self, reservasi: dict):
        """Buka form edit reservasi yang sudah ada."""
        dialog = ReservasiFormDialog(parent=self, reservasi_data=reservasi)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
            self.data_changed.emit()

    def delete_reservasi(self, reservasi: dict):
        """Hapus reservasi setelah konfirmasi secara asinkron."""
        reservasi_id = reservasi.get("id")
        reply = QMessageBox.question(
            self, "Konfirmasi Hapus",
            "Apakah Anda yakin ingin menghapus reservasi ini?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if hasattr(self, 'delete_worker') and self.delete_worker.isRunning():
                return
            from utils.worker import Worker
            self.delete_worker = Worker(self._delete_reservasi_worker, reservasi_id)
            self.delete_worker.finished.connect(self._on_delete_finished)
            self.delete_worker.error.connect(self._on_error)
            self.delete_worker.start()

    def _delete_reservasi_worker(self, reservasi_id):
        from api.supabase import get_supabase_client
        return get_supabase_client().table("reservasi").delete(f"id=eq.{reservasi_id}")

    def _on_delete_finished(self, res):
        if res is not None:
            QMessageBox.information(self, "Sukses", "Reservasi berhasil dihapus.")
            self.load_data()
            self.data_changed.emit()
        else:
            QMessageBox.warning(self, "Gagal", "Gagal menghapus reservasi.")

    # ─── EXPORT ─────────────────────────────────────────────

    def _get_current_data(self) -> list:
        """Ambil data yang sedang ditampilkan di tabel (sesuai filter aktif)."""
        return getattr(self, "_last_reservasi_data", [])

    def _export_csv(self):
        from utils.export import export_csv
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        data = self._get_current_data()
        if not data:
            QMessageBox.information(self, "Export CSV", "Tidak ada data untuk diekspor.")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Simpan CSV", "laporan_reservasi.csv",
            "CSV Files (*.csv)"
        )
        if not filepath:
            return
        try:
            saved = export_csv(data, filepath)
            QMessageBox.information(self, "Berhasil", f"File CSV berhasil disimpan:\n{saved}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal export CSV:\n{e}")

    def _export_pdf(self):
        from utils.export import export_pdf
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        data = self._get_current_data()
        if not data:
            QMessageBox.information(self, "Export PDF", "Tidak ada data untuk diekspor.")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Simpan PDF", "laporan_reservasi.pdf",
            "PDF Files (*.pdf)"
        )
        if not filepath:
            return
        try:
            filter_info = getattr(self, "_active_filter", "Semua")
            saved = export_pdf(data, filepath, filter_info=f"Status: {filter_info}")
            QMessageBox.information(self, "Berhasil", f"File PDF berhasil disimpan:\n{saved}")
        except ImportError as e:
            QMessageBox.critical(
                self, "Library Kurang",
                f"{e}\n\nJalankan: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal export PDF:\n{e}")

    def _show_dokumentasi(self, reservasi: dict):
        """Buka dialog foto dokumentasi dari tabel reservasi."""
        dialog = DialogDokumentasi(reservasi, parent=self)
        dialog.exec()

    def refresh_data(self):
        """Alias untuk load_data — dipanggil saat switch page."""
        self.load_data()

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)


# ──────────────────────────────────────────────
#  DIALOG DOKUMENTASI FOTO
# ──────────────────────────────────────────────
class DialogDokumentasi(QDialog):
    """
    Dialog popup untuk melihat foto dokumentasi reservasi.
    Mengambil data foto (foto_sebelum, foto_sesudah, foto_laporan)
    langsung dari tabel reservasi di Supabase.
    """

    def __init__(self, reservasi: dict, parent=None):
        super().__init__(parent)
        self.reservasi = reservasi
        self.setWindowTitle("📸 Foto Dokumentasi Reservasi")
        self.setModal(True)

        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

        self._build_ui()

        # Ukuran fixed — tidak bisa diperbesar maupun diperkecil
        FIXED_W = 385
        FIXED_H = 550
        self.setFixedSize(FIXED_W, FIXED_H)

    def showEvent(self, event):
        """Center ke tengah layar saat dialog muncul."""
        super().showEvent(event)
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        cx = screen.x() + (screen.width()  - self.width())  // 2
        cy = screen.y() + (screen.height() - self.height()) // 2
        self.move(cx, cy)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        # ── Margin luar diperkecil agar konten punya lebih banyak ruang ──
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(10)

        r = self.reservasi
        pengguna = r.get("pengguna") or {}
        ruangan  = r.get("ruangan") or {}

        # ── Info reservasi ──
        info_frame = QFrame()
        info_frame.setObjectName("form_card")
        info_frame.setProperty("class", "room_card")
        info_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        info_l = QVBoxLayout(info_frame)
        # ── Margin dalam diperkecil ──
        info_l.setContentsMargins(10, 10, 10, 10)
        info_l.setSpacing(8)

        lbl_judul = QLabel("📷  Detail Dokumentasi")
        lbl_judul.setAlignment(Qt.AlignCenter)
        lbl_judul.setStyleSheet(
            "font-size:16px; font-weight:800; background:transparent;"
        )
        info_l.addWidget(lbl_judul)

        # Baris 1: Nama, Ruangan, Tanggal, Jam — semua 1 baris
        row1 = QHBoxLayout()
        row1.setSpacing(0)

        def _meta(icon, text, stretch=1):
            w = QWidget()
            w.setStyleSheet("background:transparent;")
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(4)
            ic = QLabel(icon)
            ic.setStyleSheet("font-size:13px; background:transparent;")
            ic.setFixedWidth(18)
            tx = QLabel(str(text))
            # ── font lebih kecil + NO word wrap agar tetap 1 baris ──
            tx.setStyleSheet("font-size:11px; color:#94a3b8; background:transparent;")
            tx.setWordWrap(False)
            h.addWidget(ic)
            h.addWidget(tx, stretch)
            return w

        jam = f"{str(r.get('jam_mulai',''))[:5]} – {str(r.get('jam_selesai',''))[:5]}"

        row1.addWidget(_meta("👤", pengguna.get("nama", "-")), 1)
        row1.addWidget(_meta("🏢", ruangan.get("nama", "-")), 1)
        row1.addWidget(_meta("📅", r.get("tanggal", "-")), 1)
        row1.addWidget(_meta("🕒", jam), 1)
        info_l.addLayout(row1)
        layout.addWidget(info_frame)

        # ── Area foto (centered) ──
        foto_frame = QFrame()
        foto_frame.setObjectName("form_card")
        foto_frame.setProperty("class", "room_card")
        foto_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        foto_outer = QVBoxLayout(foto_frame)
        foto_outer.setContentsMargins(12, 12, 12, 12)
        foto_outer.setSpacing(0)

        url_sebelum = r.get("foto_sebelum")
        url_sesudah = r.get("foto_sesudah")
        url_laporan = r.get("foto_laporan")

        foto_row = QHBoxLayout()
        foto_row.setSpacing(12)
        foto_row.addLayout(self._foto_box("📸 Sebelum Pakai", url_sebelum), stretch=1)
        foto_row.addLayout(self._foto_box("📸 Sesudah Pakai", url_sesudah), stretch=1)
        if url_laporan:
            foto_row.addLayout(self._foto_box("📋 Laporan", url_laporan), stretch=1)

        foto_outer.addLayout(foto_row, stretch=1)

        layout.addWidget(foto_frame, stretch=1)

        # ── Catatan & Status ──
        status = r.get("status", "-")
        catatan = r.get("catatan_admin") or "-"

        STATUS_COLOR = {
            "Selesai":     ("background:#1e3a5f; color:#60a5fa; border:1px solid #3b82f6;"),
            "Disetujui":   ("background:#14532d; color:#4ade80; border:1px solid #22c55e;"),
            "Ada Masalah": ("background:#7f1d1d; color:#f87171; border:1px solid #ef4444;"),
            "Ditolak":     ("background:#7f1d1d; color:#f87171; border:1px solid #ef4444;"),
            "Menunggu":    ("background:#713f12; color:#fbbf24; border:1px solid #f59e0b;"),
        }
        status_style = STATUS_COLOR.get(
            status,
            "background:#1e293b; color:#94a3b8; border:1px solid #475569;"
        )

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        status_row.addStretch()

        lbl_status_text = QLabel("Status:")
        lbl_status_text.setStyleSheet("font-size:12px; color:#94a3b8; background:transparent;")
        status_row.addWidget(lbl_status_text)

        lbl_status_badge = QLabel(f" {status} ")
        lbl_status_badge.setStyleSheet(
            f"{status_style} font-size:12px; font-weight:700;"
            f"border-radius:6px; padding:2px 10px;"
        )
        status_row.addWidget(lbl_status_badge)

        lbl_sep = QLabel("|")
        lbl_sep.setStyleSheet("font-size:12px; color:#475569; background:transparent;")
        status_row.addWidget(lbl_sep)

        lbl_catatan = QLabel(f"Catatan Admin: {catatan}")
        lbl_catatan.setStyleSheet("font-size:12px; color:#94a3b8; background:transparent;")
        status_row.addWidget(lbl_catatan)
        status_row.addStretch()

        layout.addLayout(status_row)

        # ── Tombol tutup ──
        btn_tutup = QPushButton("Tutup")
        btn_tutup.setObjectName("cancel_btn")
        btn_tutup.setCursor(Qt.PointingHandCursor)
        btn_tutup.setFixedHeight(36)
        btn_tutup.setFixedWidth(120)
        btn_tutup.clicked.connect(self.accept)
        layout.addWidget(btn_tutup, alignment=Qt.AlignHCenter)

    def _foto_box(self, label: str, url: str | None) -> QVBoxLayout:
        box = QVBoxLayout()
        box.setSpacing(8)

        lbl_title = QLabel(label)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            "font-size:12px; font-weight:700; color:#94a3b8; background:transparent;"
        )
        box.addWidget(lbl_title)

        preview = QLabel()
        preview.setMinimumHeight(200)
        preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview.setAlignment(Qt.AlignCenter)

        if url:
            preview.setText("🔗 Klik untuk\nbuka foto")
            preview.setStyleSheet(
                "background:rgba(79,70,229,0.10); border:2px solid #a5b4fc;"
                "border-radius:12px; font-size:12px; color:#6366f1;"
            )
            preview.setCursor(Qt.PointingHandCursor)
            preview.mousePressEvent = lambda e, u=url: QDesktopServices.openUrl(QUrl(u))

            btn_buka = QPushButton("🌐 Buka di Browser")
            btn_buka.setCursor(Qt.PointingHandCursor)
            btn_buka.setFixedHeight(32)
            btn_buka.setStyleSheet(
                "QPushButton{background:#4f46e5;color:white;border:none;"
                "border-radius:8px;font-size:11px;font-weight:700;padding:0 10px;}"
                "QPushButton:hover{background:#4338ca;}"
            )
            btn_buka.clicked.connect(
                lambda checked=False, u=url: QDesktopServices.openUrl(QUrl(u))
            )
            box.addWidget(preview, stretch=1)
            box.addWidget(btn_buka, alignment=Qt.AlignCenter)
        else:
            preview.setText("—\nTidak ada\nfoto")
            preview.setStyleSheet(
                "background:rgba(100,116,139,0.07); border:2px dashed #475569;"
                "border-radius:12px; font-size:12px; color:#64748b;"
            )
            box.addWidget(preview, stretch=1)
            lbl_kosong = QLabel("Belum diupload")
            lbl_kosong.setAlignment(Qt.AlignCenter)
            lbl_kosong.setStyleSheet(
                "font-size:10px; color:#64748b; background:transparent;"
            )
            box.addWidget(lbl_kosong, alignment=Qt.AlignCenter)

        return box


# ──────────────────────────────────────────────
#  RESERVASI FORM DIALOG
# ──────────────────────────────────────────────
class ReservasiFormDialog(QDialog):
    """Dialog popup form untuk Tambah / Edit Reservasi."""

    def __init__(self, parent=None, reservasi_data=None, default_ruangan_id=None):
        super().__init__(parent)
        self.reservasi_data = reservasi_data
        self.is_edit = reservasi_data is not None
        self.default_ruangan_id = default_ruangan_id

        self.setWindowTitle("Edit Reservasi" if self.is_edit else "Tambah Reservasi Baru")
        self.setMinimumSize(460, 580)
        self.setModal(True)

        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

        self._build_ui()
        self._load_combo_data()

    def showEvent(self, event):
        """Center ke tengah layar saat dialog muncul."""
        super().showEvent(event)
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        cx = screen.x() + (screen.width()  - self.width())  // 2
        cy = screen.y() + (screen.height() - self.height()) // 2
        self.move(cx, cy)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_lbl = QLabel("FORM DATA RESERVASI")
        title_lbl.setObjectName("page_title_lbl")
        title_lbl.setStyleSheet("background-color: transparent;")
        layout.addWidget(title_lbl)

        form_frame = QFrame()
        form_frame.setObjectName("form_card")
        form_frame.setProperty("class", "room_card")
        form_frame.setStyleSheet("QFrame#form_card { padding: 16px; background-color: transparent; }")

        fl = QVBoxLayout(form_frame)
        fl.setSpacing(10)

        # Pengguna
        fl.addWidget(QLabel("Peminjam"))
        self.combo_pengguna = QComboBox()
        self.combo_pengguna.setMinimumHeight(32)
        fl.addWidget(self.combo_pengguna)

        # Ruangan
        fl.addWidget(QLabel("Ruangan"))
        self.combo_ruangan = QComboBox()
        self.combo_ruangan.setMinimumHeight(32)
        fl.addWidget(self.combo_ruangan)

        # Tanggal
        fl.addWidget(QLabel("Tanggal"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(date.today())
        self.date_edit.setMinimumHeight(32)
        fl.addWidget(self.date_edit)

        # Jam Mulai & Selesai
        jam_row = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Jam Mulai"))
        self.time_mulai = QTimeEdit()
        self.time_mulai.setDisplayFormat("HH:mm")
        self.time_mulai.setMinimumHeight(32)
        v1.addWidget(self.time_mulai)
        jam_row.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Jam Selesai"))
        self.time_selesai = QTimeEdit()
        self.time_selesai.setDisplayFormat("HH:mm")
        self.time_selesai.setMinimumHeight(32)
        v2.addWidget(self.time_selesai)
        jam_row.addLayout(v2)
        fl.addLayout(jam_row)

        # Keperluan
        fl.addWidget(QLabel("Keperluan"))
        self.input_keperluan = QLineEdit()
        self.input_keperluan.setPlaceholderText("Contoh: Kuliah Umum, Rapat Dosen, dll.")
        self.input_keperluan.setMinimumHeight(32)
        fl.addWidget(self.input_keperluan)

        # Status
        fl.addWidget(QLabel("Status"))
        self.combo_status = QComboBox()
        self.combo_status.addItems(["Pending", "Disetujui", "Ditolak", "Dibatalkan", "Selesai"])
        self.combo_status.setMinimumHeight(32)
        fl.addWidget(self.combo_status)

        # Catatan Admin
        fl.addWidget(QLabel("Catatan Admin (opsional)"))
        self.input_catatan = QLineEdit()
        self.input_catatan.setPlaceholderText("Catatan tambahan dari admin…")
        self.input_catatan.setMinimumHeight(32)
        fl.addWidget(self.input_catatan)

        layout.addWidget(form_frame)

        # Warning
        self.warning_lbl = QLabel("")
        self.warning_lbl.setStyleSheet(
            "color: #EF4444; font-size: 11px; font-weight: bold; background-color: transparent;"
        )
        self.warning_lbl.setAlignment(Qt.AlignCenter)
        self.warning_lbl.hide()
        layout.addWidget(self.warning_lbl)

        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Batal")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Simpan")
        self.save_btn.setObjectName("login_btn")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.handle_save)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _load_combo_data(self):
        """Muat list pengguna & ruangan dari DB ke combo box asinkron."""
        self.combo_pengguna.addItem("Memuat...")
        self.combo_ruangan.addItem("Memuat...")

        from utils.worker import Worker
        self.combo_worker = Worker(self._fetch_combo_worker)
        self.combo_worker.finished.connect(self._on_combo_fetched)
        self.combo_worker.start()

    def _fetch_combo_worker(self):
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        pengguna_list = supabase.table("pengguna").select("id,nama,role") or []
        ruangan_list = supabase.table("ruangan").select("id,nama") or []
        return {
            "pengguna": sorted(pengguna_list, key=lambda x: x.get("nama", "")),
            "ruangan": sorted(ruangan_list, key=lambda x: x.get("nama", ""))
        }

    def _on_combo_fetched(self, data):
        self.combo_pengguna.clear()
        self.combo_ruangan.clear()

        for p in data["pengguna"]:
            display = f"{p.get('nama', '?')} ({p.get('role', '?')})"
            self.combo_pengguna.addItem(display, p.get("id"))

        for r in data["ruangan"]:
            self.combo_ruangan.addItem(r.get("nama", "?"), r.get("id"))

        if self.is_edit:
            self._load_reservasi_data()
        elif self.default_ruangan_id:
            self._preselect_ruangan(self.default_ruangan_id)

    def _load_reservasi_data(self):
        """Pre-fill form untuk mode edit."""
        r = self.reservasi_data
        # Pengguna
        pengguna_id = r.get("pengguna_id")
        for i in range(self.combo_pengguna.count()):
            if self.combo_pengguna.itemData(i) == pengguna_id:
                self.combo_pengguna.setCurrentIndex(i)
                break

        # Ruangan
        ruangan_id = r.get("ruangan_id")
        for i in range(self.combo_ruangan.count()):
            if self.combo_ruangan.itemData(i) == ruangan_id:
                self.combo_ruangan.setCurrentIndex(i)
                break

        # Tanggal
        try:
            dt = datetime.strptime(r.get("tanggal", ""), "%Y-%m-%d").date()
            from PySide6.QtCore import QDate
            self.date_edit.setDate(QDate(dt.year, dt.month, dt.day))
        except Exception:
            pass

        # Jam
        try:
            from PySide6.QtCore import QTime
            hm = r.get("jam_mulai", "08:00").split(":")
            self.time_mulai.setTime(QTime(int(hm[0]), int(hm[1])))
            hs = r.get("jam_selesai", "09:00").split(":")
            self.time_selesai.setTime(QTime(int(hs[0]), int(hs[1])))
        except Exception:
            pass

        self.input_keperluan.setText(r.get("keperluan", ""))

        idx = self.combo_status.findText(r.get("status", "Pending"))
        if idx >= 0:
            self.combo_status.setCurrentIndex(idx)

        self.input_catatan.setText(r.get("catatan_admin", "") or "")

    def _preselect_ruangan(self, ruangan_id):
        """Pre-select ruangan di combo box (dari detail panel)."""
        for i in range(self.combo_ruangan.count()):
            if self.combo_ruangan.itemData(i) == ruangan_id:
                self.combo_ruangan.setCurrentIndex(i)
                break

    # ─── VALIDATION & SAVE ───────────────────────
    def handle_save(self):
        # Ambil values
        pengguna_id = self.combo_pengguna.currentData()
        ruangan_id = self.combo_ruangan.currentData()
        tanggal = self.date_edit.date().toString("yyyy-MM-dd")
        jam_mulai = self.time_mulai.time().toString("HH:mm")
        jam_selesai = self.time_selesai.time().toString("HH:mm")
        keperluan = self.input_keperluan.text().strip()
        status = self.combo_status.currentText()
        catatan = self.input_catatan.text().strip()

        # Validasi 1: field wajib
        if not pengguna_id:
            self._show_warning("Pilih peminjam terlebih dahulu!")
            return
        if not ruangan_id:
            self._show_warning("Pilih ruangan terlebih dahulu!")
            return
        if not keperluan:
            self._show_warning("Keperluan tidak boleh kosong!")
            return

        # Validasi 2: jam_mulai < jam_selesai
        if jam_mulai >= jam_selesai:
            self._show_warning("Jam mulai harus lebih awal dari jam selesai!")
            return

        if hasattr(self, 'save_worker') and self.save_worker.isRunning():
            return

        self.save_btn.setEnabled(False)
        self.save_btn.setText("Menyimpan...")

        payload = {
            "pengguna_id": pengguna_id,
            "ruangan_id": ruangan_id,
            "tanggal": tanggal,
            "jam_mulai": jam_mulai,
            "jam_selesai": jam_selesai,
            "keperluan": keperluan,
            "status": status,
            "catatan_admin": catatan
        }

        from utils.worker import Worker
        rid = self.reservasi_data.get("id") if self.is_edit else None
        self.save_worker = Worker(self._save_reservasi_worker, ruangan_id, tanggal, jam_mulai, jam_selesai, status, payload, rid)
        self.save_worker.finished.connect(self._on_save_finished)
        self.save_worker.error.connect(self._on_save_error)
        self.save_worker.start()

    def _save_reservasi_worker(self, ruangan_id, tanggal, jam_mulai, jam_selesai, status, payload, rid):
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()

        # Conflict check
        if status in ("Pending", "Disetujui"):
            existing = supabase.table("reservasi").select(
                "id,jam_mulai,jam_selesai",
                f"ruangan_id=eq.{ruangan_id}&tanggal=eq.{tanggal}&status=eq.Disetujui"
            )
            if existing:
                for ex in existing:
                    if rid and ex.get("id") == rid:
                        continue
                    ex_mulai = ex.get("jam_mulai", "00:00")
                    ex_selesai = ex.get("jam_selesai", "00:00")
                    if jam_mulai < ex_selesai and jam_selesai > ex_mulai:
                        return {"success": False, "conflict": True, "conflict_data": (ex_mulai, ex_selesai, tanggal)}

        if rid:
            res = supabase.table("reservasi").update(payload, f"id=eq.{rid}")
        else:
            res = supabase.table("reservasi").insert(payload)

        if res is not None:
            return {"success": True}
        else:
            return {"success": False, "conflict": False}

    def _on_save_finished(self, result):
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Simpan")

        if result["success"]:
            self.accept()
        elif result.get("conflict"):
            ex_mulai, ex_selesai, tanggal = result["conflict_data"]
            QMessageBox.warning(
                self, "Konflik Jadwal!",
                f"Jadwal bentrok dengan reservasi yang sudah disetujui:\n"
                f"Jam {ex_mulai} – {ex_selesai} pada {tanggal}.\n\n"
                f"Silakan pilih jam lain."
            )
        else:
            self._show_warning("Gagal menyimpan data ke database.")

    def _on_save_error(self, err_msg):
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Simpan")
        self._show_warning(f"Error database: {err_msg}")

    def _show_warning(self, msg: str):
        self.warning_lbl.setText(msg)
        self.warning_lbl.show()