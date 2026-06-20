from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QTableWidget, QTableWidgetItem, 
                                QHeaderView, QMessageBox, QDialog, QLineEdit, 
                                QComboBox, QFrame, QAbstractItemView)
from PySide6.QtGui import QIntValidator
from utils.mode import theme_manager
from api.supabase import get_supabase_client

class KelolaRuanganWidget(QWidget):
    """Widget untuk mengelola CRUD Ruangan Kuliah."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 32, 32, 32)
        self.main_layout.setSpacing(24)
        
        self._build_content_area()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _build_content_area(self):
        # Top Header Bar
        header_bar = QHBoxLayout()
        header_title = QLabel("Kelola Ruangan Kuliah")
        header_title.setStyleSheet("font-size: 22px; font-weight: 800; background-color: transparent;")
        
        self.add_room_btn = QPushButton("➕ Tambah Ruangan")
        self.add_room_btn.setObjectName("login_btn")
        self.add_room_btn.setCursor(Qt.PointingHandCursor)
        self.add_room_btn.setFixedHeight(38)
        self.add_room_btn.clicked.connect(self.add_room)
        
        header_bar.addWidget(header_title)
        header_bar.addStretch()
        header_bar.addWidget(self.add_room_btn)
        self.main_layout.addLayout(header_bar)
        
        # Room Data Table
        self.table = QTableWidget()
        self.table.setStyleSheet("QTableWidget { border: none; background: transparent; }")
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Nama Ruangan", "Gedung", "Lantai", "Kapasitas", "Status", "Fasilitas", "Aksi"
        ])
        
        # Table Custom Styling matching premium theme
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        
        # Setup Column stretching
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive) # Nama
        header.setSectionResizeMode(1, QHeaderView.Interactive) # Gedung
        header.setSectionResizeMode(2, QHeaderView.Interactive) # Lantai
        header.setSectionResizeMode(3, QHeaderView.Interactive) # Kapasitas
        header.setSectionResizeMode(4, QHeaderView.Interactive) # Status
        header.setSectionResizeMode(5, QHeaderView.Stretch)          # Fasilitas
        header.setSectionResizeMode(6, QHeaderView.Fixed)            # Aksi
        
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(6, 160) # Width for action buttons
        
        self.table.verticalHeader().setDefaultSectionSize(60) # Taller rows for premium feel

        self.table_container = QFrame()

        container_layout = QVBoxLayout(self.table_container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.addWidget(self.table)
        
        self.main_layout.addWidget(self.table_container)

    def refresh_data(self):
        """Memuat ulang semua data ruangan dari database Supabase secara asinkron."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            return
            
        self.table.setRowCount(0)
        from utils.worker import Worker
        self.worker = Worker(self._fetch_rooms_worker)
        self.worker.finished.connect(self._on_rooms_fetched)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _fetch_rooms_worker(self):
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        rooms_data = supabase.table('ruangan').select()
        if not rooms_data:
            rooms_data = []
        return sorted(rooms_data, key=lambda x: x.get('nama', ''))

    def _on_error(self, err_msg):
        QMessageBox.critical(self, "Database Error", f"Gagal memproses data!\n{err_msg}")

    def _on_rooms_fetched(self, rooms_data):
        self.table.setRowCount(0)
        for row_idx, room in enumerate(rooms_data):
            self.table.insertRow(row_idx)
            for c in range(self.table.columnCount()):
                self.table.setItem(row_idx, c, QTableWidgetItem())
            
            # Kolom 0: Nama Ruangan (Bold)
            nama_widget = QWidget()
            nama_layout = QHBoxLayout(nama_widget)
            nama_layout.setContentsMargins(16, 0, 16, 0)
            nama_lbl = QLabel(str(room.get('nama', '-')))
            nama_lbl.setStyleSheet("font-weight: 800; font-size: 14px; background-color: transparent;")
            nama_layout.addWidget(nama_lbl)
            nama_layout.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row_idx, 0, nama_widget)
            
            # Kolom 1: Gedung
            gedung_widget = QWidget()
            gedung_layout = QHBoxLayout(gedung_widget)
            gedung_layout.setContentsMargins(16, 0, 16, 0)
            gedung_lbl = QLabel(str(room.get('gedung', '-')))
            gedung_lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #6b6b80; background-color: transparent;")
            gedung_layout.addWidget(gedung_lbl)
            gedung_layout.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row_idx, 1, gedung_widget)
            
            # Kolom 2: Lantai
            lantai = QTableWidgetItem(str(room.get('lantai', '-')))
            lantai.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, lantai)
            
            # Kolom 3: Kapasitas
            kapasitas_widget = QWidget()
            kapasitas_layout = QHBoxLayout(kapasitas_widget)
            kapasitas_layout.setContentsMargins(16, 0, 16, 0)
            kapasitas_lbl = QLabel(f"{room.get('kapasitas', '-')} orang")
            kapasitas_lbl.setStyleSheet("font-size: 13px; color: #8888a0; background-color: transparent;")
            kapasitas_layout.addWidget(kapasitas_lbl)
            kapasitas_layout.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row_idx, 3, kapasitas_widget)
            
            # Kolom 4: Status (Badge)
            status_val = str(room.get('status', 'Tersedia'))
            if status_val in ("Digunakan", "Tidak Tersedia", "Nonaktif", "Maintenance"):
                status_val = "Terpakai"
            elif status_val == "Dosen":
                status_val = "Terbooking"
            
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(16, 0, 16, 0)
            status_badge = QLabel(status_val)
            
            badge_class = "badge badge_available"
            if status_val == "Terbooking":
                badge_class = "badge badge_booked"
            elif status_val == "Terpakai":
                badge_class = "badge badge_in_use"
                
            status_badge.setProperty("class", badge_class)
            status_badge.setAlignment(Qt.AlignCenter)
            status_layout.addWidget(status_badge)
            status_layout.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row_idx, 4, status_widget)
            
            # Kolom 5: Fasilitas (Bisa panjang)
            fasilitas_widget = QWidget()
            fasilitas_layout = QHBoxLayout(fasilitas_widget)
            fasilitas_layout.setContentsMargins(16, 0, 16, 0)
            fasilitas_lbl = QLabel(str(room.get('fasilitas', '-')))
            fasilitas_lbl.setStyleSheet("font-size: 12px; color: #6b6b80; background-color: transparent;")
            fasilitas_lbl.setWordWrap(True)
            fasilitas_layout.addWidget(fasilitas_lbl)
            self.table.setCellWidget(row_idx, 5, fasilitas_widget)
            
            # Action Buttons
            self._add_action_buttons(row_idx, room)

    def _add_action_buttons(self, row_idx, room):
        # Widget container untuk tombol aksi
        actions_widget = QWidget()
        actions_widget.setStyleSheet("QWidget { background-color: transparent; }")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(6, 2, 6, 2)
        actions_layout.setSpacing(8)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet("QPushButton { background-color: #f59e0b; color: white; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #d97706; }")
        edit_btn.setFixedHeight(28)
        edit_btn.clicked.connect(lambda _, r=room: self.edit_room(r))
        
        delete_btn = QPushButton("🗑️ Hapus")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet("QPushButton { background-color: #ef4444; color: white; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #dc2626; }")
        delete_btn.setFixedHeight(28)
        delete_btn.clicked.connect(lambda _, r=room: self.delete_room(r))
        
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        
        self.table.setCellWidget(row_idx, 6, actions_widget)

    def add_room(self):
        """Membuka dialog tambah ruangan."""
        dialog = RoomFormDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def edit_room(self, room_data):
        """Membuka dialog edit ruangan dengan data terpilih."""
        dialog = RoomFormDialog(room_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def delete_room(self, room_data):
        """Menghapus ruangan terpilih setelah konfirmasi secara asinkron."""
        room_name = room_data.get('nama', 'Ruangan')
        room_id = room_data.get('id')
        
        reply = QMessageBox.question(
            self, 'Konfirmasi Hapus',
            f"Apakah Anda yakin ingin menghapus ruangan '{room_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if hasattr(self, 'delete_worker') and self.delete_worker.isRunning():
                return
                
            from utils.worker import Worker
            self.delete_worker = Worker(self._delete_room_worker, room_id)
            self.delete_worker.finished.connect(lambda res: self._on_delete_finished(res, room_name))
            self.delete_worker.error.connect(self._on_error)
            self.delete_worker.start()

    def _delete_room_worker(self, room_id):
        from api.supabase import get_supabase_client
        return get_supabase_client().table('ruangan').delete(f"id=eq.{room_id}")

    def _on_delete_finished(self, res, room_name):
        if res is not None:
            QMessageBox.information(self, "Sukses", f"Ruangan '{room_name}' berhasil dihapus.")
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Gagal", "Gagal menghapus ruangan. Silakan coba lagi.")

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)


class RoomFormDialog(QDialog):
    """Dialog Popup Form untuk Tambah / Edit Ruangan."""
    
    def __init__(self, room_data=None, parent=None):
        super().__init__(parent)
        self.room_data = room_data
        self.is_edit = room_data is not None
        
        self.setWindowTitle("Edit Ruangan" if self.is_edit else "Tambah Ruangan Baru")
        self.setMinimumSize(400, 500)
        self.setModal(True)
        
        # Apply theme
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
            
        self._build_ui()
        if self.is_edit:
            self._load_room_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title Label
        title_lbl = QLabel("FORM DATA RUANGAN")
        title_lbl.setObjectName("page_title_lbl")
        title_lbl.setStyleSheet("background-color: transparent;")
        layout.addWidget(title_lbl)
        
        # Form Fields Container
        form_frame = QFrame()
        form_frame.setObjectName("form_card")
        form_frame.setProperty("class", "room_card")
        form_frame.setStyleSheet("QFrame#form_card { padding: 16px; }")
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(12)
        
        # Nama Ruangan
        form_layout.addWidget(QLabel("Nama Ruangan"))
        self.nama_input = QLineEdit()
        self.nama_input.setPlaceholderText("Contoh: A301")
        form_layout.addWidget(self.nama_input)
        
        # Gedung
        form_layout.addWidget(QLabel("Gedung"))
        self.gedung_input = QLineEdit()
        self.gedung_input.setPlaceholderText("Contoh: Gedung A")
        form_layout.addWidget(self.gedung_input)
        
        # Lantai
        form_layout.addWidget(QLabel("Lantai"))
        self.lantai_input = QLineEdit()
        self.lantai_input.setPlaceholderText("Contoh: 3")
        self.lantai_input.setValidator(QIntValidator(1, 100, self))
        form_layout.addWidget(self.lantai_input)
        
        # Kapasitas
        form_layout.addWidget(QLabel("Kapasitas (orang)"))
        self.kapasitas_input = QLineEdit()
        self.kapasitas_input.setPlaceholderText("Contoh: 40")
        self.kapasitas_input.setValidator(QIntValidator(1, 1000, self))
        form_layout.addWidget(self.kapasitas_input)
        
        # Fasilitas
        form_layout.addWidget(QLabel("Fasilitas (pisahkan dengan koma)"))
        self.fasilitas_input = QLineEdit()
        self.fasilitas_input.setPlaceholderText("AC, Proyektor, Whiteboard...")
        form_layout.addWidget(self.fasilitas_input)
        
        # Status
        form_layout.addWidget(QLabel("Status Ketersediaan"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Tersedia", "Terbooking", "Terpakai"])
        form_layout.addWidget(self.status_combo)
        
        layout.addWidget(form_frame)
        
        # Error / Validation Warning
        self.warning_lbl = QLabel("")
        self.warning_lbl.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: bold; background-color: transparent;")
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

    def _load_room_data(self):
        """Memuat data ruangan ke form input untuk mode edit."""
        r = self.room_data
        self.nama_input.setText(str(r.get('nama', '')))
        self.gedung_input.setText(str(r.get('gedung', '')))
        self.lantai_input.setText(str(r.get('lantai', '')))
        self.kapasitas_input.setText(str(r.get('kapasitas', '')))
        self.fasilitas_input.setText(str(r.get('fasilitas', '')))
        
        status_val = str(r.get('status', 'Tersedia'))
        idx = self.status_combo.findText(status_val)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

    def handle_save(self):
        # Get values
        nama = self.nama_input.text().strip()
        gedung = self.gedung_input.text().strip()
        lantai_str = self.lantai_input.text().strip()
        kapasitas_str = self.kapasitas_input.text().strip()
        fasilitas = self.fasilitas_input.text().strip()
        status = self.status_combo.currentText()
        
        # Validasi field kosong
        if not nama or not gedung or not lantai_str or not kapasitas_str:
            self.warning_lbl.setText("Mohon lengkapi semua field utama (Nama, Gedung, Lantai, Kapasitas)!")
            self.warning_lbl.show()
            return
            
        if hasattr(self, 'save_worker') and self.save_worker.isRunning():
            return
            
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Menyimpan...")
        
        # Data payload
        payload = {
            "nama": nama,
            "gedung": gedung,
            "lantai": int(lantai_str),
            "kapasitas": int(kapasitas_str),
            "fasilitas": fasilitas,
            "status": status
        }
        
        from utils.worker import Worker
        room_id = self.room_data.get('id') if self.is_edit else None
        self.save_worker = Worker(self._save_worker_func, payload, room_id)
        self.save_worker.finished.connect(self._on_save_finished)
        self.save_worker.error.connect(self._on_save_error)
        self.save_worker.start()

    def _save_worker_func(self, payload, room_id):
        from api.supabase import get_supabase_client
        supabase = get_supabase_client()
        if room_id:
            return supabase.table('ruangan').update(payload, f"id=eq.{room_id}")
        else:
            return supabase.table('ruangan').insert(payload)

    def _on_save_finished(self, res):
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Simpan")
        if res is not None:
            self.accept()
        else:
            self.warning_lbl.setText("Gagal menyimpan data ke Supabase.")
            self.warning_lbl.show()

    def _on_save_error(self, err_msg):
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Simpan")
        self.warning_lbl.setText(f"Error database: {err_msg}")
        self.warning_lbl.show()
