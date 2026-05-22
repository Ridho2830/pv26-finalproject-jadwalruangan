from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QTableWidget, QTableWidgetItem, 
                                QHeaderView, QMessageBox, QDialog, QLineEdit, 
                                QComboBox, QFrame, QAbstractItemView)
from PySide6.QtGui import QIntValidator, QColor
from utils.mode import theme_manager
from api.supabase import get_supabase_client

class KelolaRuanganWidget(QWidget):
    """Widget untuk mengelola CRUD Ruangan Kuliah."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Nama Ruangan", "Gedung", "Lantai", "Kapasitas", "Status", "Fasilitas", "Aksi"
        ])
        
        # Table Custom Styling matching premium theme
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        
        # Setup Column stretching
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Nama
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Gedung
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Lantai
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Kapasitas
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Status
        header.setSectionResizeMode(5, QHeaderView.Stretch)          # Fasilitas
        header.setSectionResizeMode(6, QHeaderView.Fixed)            # Aksi
        self.table.setColumnWidth(6, 150) # Width for action buttons
        
        self.main_layout.addWidget(self.table)

    def refresh_data(self):
        """Memuat ulang semua data ruangan dari database Supabase dan memasukkannya ke tabel."""
        self.table.setRowCount(0)
        
        try:
            supabase = get_supabase_client()
            rooms_data = supabase.table('ruangan').select()
            
            if not rooms_data:
                rooms_data = []
                
            # Urutkan berdasarkan nama ruangan
            rooms_data = sorted(rooms_data, key=lambda x: x.get('nama', ''))
            
            for row_idx, room in enumerate(rooms_data):
                self.table.insertRow(row_idx)
                
                # Column data
                nama = QTableWidgetItem(str(room.get('nama', '-')))
                nama.setTextAlignment(Qt.AlignCenter)
                
                gedung = QTableWidgetItem(str(room.get('gedung', '-')))
                gedung.setTextAlignment(Qt.AlignCenter)
                
                lantai = QTableWidgetItem(str(room.get('lantai', '-')))
                lantai.setTextAlignment(Qt.AlignCenter)
                
                kapasitas = QTableWidgetItem(f"{room.get('kapasitas', '-')} orang")
                kapasitas.setTextAlignment(Qt.AlignCenter)
                
                status_val = str(room.get('status', 'Tersedia'))
                # Fallback mapping if database has legacy values
                if status_val == "Digunakan" or status_val in ("Tidak Tersedia", "Nonaktif", "Maintenance"):
                    status_val = "Terpakai"
                elif status_val == "Dosen":
                    status_val = "Terbooking"
                    
                status = QTableWidgetItem(status_val)
                status.setTextAlignment(Qt.AlignCenter)
                if status_val == "Tersedia":
                    status.setForeground(QColor("#10B981"))
                elif status_val == "Terbooking":
                    status.setForeground(QColor("#F59E0B"))
                else:
                    status.setForeground(QColor("#EF4444"))
                    
                fasilitas = QTableWidgetItem(str(room.get('fasilitas', '-')))
                
                self.table.setItem(row_idx, 0, nama)
                self.table.setItem(row_idx, 1, gedung)
                self.table.setItem(row_idx, 2, lantai)
                self.table.setItem(row_idx, 3, kapasitas)
                self.table.setItem(row_idx, 4, status)
                self.table.setItem(row_idx, 5, fasilitas)
                
                # Action Buttons
                self._add_action_buttons(row_idx, room)
                
        except Exception as e:
            print(f"Error loading admin data: {e}")
            QMessageBox.critical(self, "Database Error", "Gagal mengambil data dari database Supabase!")

    def _add_action_buttons(self, row_idx, room):
        # Widget container untuk tombol aksi
        actions_widget = QWidget()
        actions_widget.setStyleSheet("background-color: transparent;")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(6, 2, 6, 2)
        actions_layout.setSpacing(8)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setObjectName("edit_action_btn")
        edit_btn.setFixedHeight(24)
        edit_btn.clicked.connect(lambda _, r=room: self.edit_room(r))
        
        delete_btn = QPushButton("Hapus")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setObjectName("delete_action_btn")
        delete_btn.setFixedHeight(24)
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
        """Menghapus ruangan terpilih setelah konfirmasi."""
        room_name = room_data.get('nama', 'Ruangan')
        room_id = room_data.get('id')
        
        reply = QMessageBox.question(
            self, 'Konfirmasi Hapus',
            f"Apakah Anda yakin ingin menghapus ruangan '{room_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                supabase = get_supabase_client()
                # Delete dari Supabase
                res = supabase.table('ruangan').delete(f"id=eq.{room_id}")
                
                if res is not None:
                    QMessageBox.information(self, "Sukses", f"Ruangan '{room_name}' berhasil dihapus.")
                    self.refresh_data()
                else:
                    QMessageBox.warning(self, "Gagal", "Gagal menghapus ruangan. Silakan coba lagi.")
            except Exception as e:
                print(f"Error deleting room: {e}")
                QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat menghapus data: {e}")

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
            
        try:
            # Data payload
            payload = {
                "nama": nama,
                "gedung": gedung,
                "lantai": int(lantai_str),
                "kapasitas": int(kapasitas_str),
                "fasilitas": fasilitas,
                "status": status
            }
            
            supabase = get_supabase_client()
            
            if self.is_edit:
                # Update database
                room_id = self.room_data.get('id')
                res = supabase.table('ruangan').update(payload, f"id=eq.{room_id}")
            else:
                # Insert database
                res = supabase.table('ruangan').insert(payload)
                
            if res is not None:
                self.accept()
            else:
                self.warning_lbl.setText("Gagal menyimpan data ke Supabase.")
                self.warning_lbl.show()
        except Exception as e:
            print(f"Error saving room: {e}")
            self.warning_lbl.setText(f"Error database: {e}")
            self.warning_lbl.show()
