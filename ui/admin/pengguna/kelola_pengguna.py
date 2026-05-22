from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QTableWidget, QTableWidgetItem, 
                                QHeaderView, QMessageBox, QDialog, QLineEdit, 
                                QComboBox, QFrame, QAbstractItemView, QCheckBox)
from PySide6.QtGui import QColor
from utils.mode import theme_manager
from api.supabase import get_supabase_client
import bcrypt

class KelolaPenggunaWidget(QWidget):
    """Widget untuk mengelola CRUD Pengguna (Admin, Dosen, Mahasiswa)."""
    
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
        header_title = QLabel("Kelola Pengguna")
        header_title.setStyleSheet("font-size: 22px; font-weight: 800; background-color: transparent;")
        
        self.add_user_btn = QPushButton("➕ Tambah Pengguna")
        self.add_user_btn.setObjectName("login_btn")
        self.add_user_btn.setCursor(Qt.PointingHandCursor)
        self.add_user_btn.setFixedHeight(38)
        self.add_user_btn.clicked.connect(self.add_user)
        
        header_bar.addWidget(header_title)
        header_bar.addStretch()
        header_bar.addWidget(self.add_user_btn)
        self.main_layout.addLayout(header_bar)
        
        # User Data Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Nama Lengkap", "Username", "Role", "NIM/NIP", "Status", "Aksi"
        ])
        
        # Table Custom Styling matching premium theme
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        
        # Setup Column stretching
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)          # Nama
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Username
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Role
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # NIM/NIP
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Status
        header.setSectionResizeMode(5, QHeaderView.Fixed)            # Aksi
        self.table.setColumnWidth(5, 160) # Width for action buttons
        
        self.table.verticalHeader().setDefaultSectionSize(60) # Taller rows for premium feel
        
        self.main_layout.addWidget(self.table)

    def refresh_data(self):
        """Memuat ulang semua data pengguna dari database Supabase dan memasukkannya ke tabel."""
        self.table.setRowCount(0)
        
        try:
            supabase = get_supabase_client()
            users_data = supabase.table('pengguna').select()
            
            if not users_data:
                users_data = []
                
            # Urutkan berdasarkan nama pengguna
            users_data = sorted(users_data, key=lambda x: x.get('nama', '').lower())
            
            for row_idx, user in enumerate(users_data):
                self.table.insertRow(row_idx)
                
                # Column data
                # Kolom 0: Nama (Bold)
                nama_widget = QWidget()
                nama_layout = QHBoxLayout(nama_widget)
                nama_layout.setContentsMargins(16, 0, 16, 0)
                nama_lbl = QLabel(str(user.get('nama', '-')))
                nama_lbl.setStyleSheet("font-weight: 800; font-size: 14px; background-color: transparent;")
                nama_layout.addWidget(nama_lbl)
                nama_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setCellWidget(row_idx, 0, nama_widget)
                
                # Kolom 1: Username
                username_widget = QWidget()
                username_layout = QHBoxLayout(username_widget)
                username_layout.setContentsMargins(16, 0, 16, 0)
                username_lbl = QLabel(str(user.get('username', '-')))
                username_lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #6b6b80; background-color: transparent;")
                username_layout.addWidget(username_lbl)
                username_layout.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row_idx, 1, username_widget)
                
                # Kolom 2: Role
                role_widget = QWidget()
                role_layout = QHBoxLayout(role_widget)
                role_layout.setContentsMargins(16, 0, 16, 0)
                role_lbl = QLabel(str(user.get('role', '-')))
                role_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #8888a0; background-color: transparent;")
                role_layout.addWidget(role_lbl)
                role_layout.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row_idx, 2, role_widget)
                
                # Kolom 3: NIM/NIP
                nim_widget = QWidget()
                nim_layout = QHBoxLayout(nim_widget)
                nim_layout.setContentsMargins(16, 0, 16, 0)
                nim_lbl = QLabel(str(user.get('nim_nip', '-')))
                nim_lbl.setStyleSheet("font-size: 13px; color: #6b6b80; background-color: transparent;")
                nim_layout.addWidget(nim_lbl)
                nim_layout.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row_idx, 3, nim_widget)
                
                # Kolom 4: Status (Aktif/Nonaktif)
                is_active = user.get('is_active', True)
                status_val = "Aktif" if is_active else "Nonaktif"
                
                status_widget = QWidget()
                status_layout = QHBoxLayout(status_widget)
                status_layout.setContentsMargins(16, 0, 16, 0)
                status_badge = QLabel(status_val)
                
                badge_class = "badge badge_available" if is_active else "badge badge_in_use"
                    
                status_badge.setProperty("class", badge_class)
                status_badge.setAlignment(Qt.AlignCenter)
                status_layout.addWidget(status_badge)
                status_layout.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row_idx, 4, status_widget)
                
                # Action Buttons
                self._add_action_buttons(row_idx, user)
                
        except Exception as e:
            print(f"Error loading users data: {e}")
            QMessageBox.critical(self, "Database Error", "Gagal mengambil data pengguna dari database Supabase!")

    def _add_action_buttons(self, row_idx, user):
        actions_widget = QWidget()
        actions_widget.setStyleSheet("QWidget { background-color: transparent; }")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(6, 2, 6, 2)
        actions_layout.setSpacing(8)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setObjectName("edit_action_btn")
        edit_btn.setFixedHeight(24)
        edit_btn.clicked.connect(lambda _, u=user: self.edit_user(u))
        
        delete_btn = QPushButton("Hapus")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setObjectName("delete_action_btn")
        delete_btn.setFixedHeight(24)
        delete_btn.clicked.connect(lambda _, u=user: self.delete_user(u))
        
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        
        self.table.setCellWidget(row_idx, 5, actions_widget)

    def add_user(self):
        """Membuka dialog tambah pengguna."""
        dialog = PenggunaFormDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def edit_user(self, user_data):
        """Membuka dialog edit pengguna dengan data terpilih."""
        dialog = PenggunaFormDialog(user_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def delete_user(self, user_data):
        """Menghapus pengguna terpilih setelah konfirmasi."""
        user_name = user_data.get('nama', 'Pengguna')
        user_id = user_data.get('id')
        
        # Cegah hapus diri sendiri jika id kita sama (Opsional, tapi praktik bagus)
        # Saat ini kita tidak track active admin ID di module ini secara eksplisit
        
        reply = QMessageBox.question(
            self, 'Konfirmasi Hapus',
            f"Apakah Anda yakin ingin menghapus pengguna '{user_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                supabase = get_supabase_client()
                # Delete dari Supabase
                res = supabase.table('pengguna').delete(f"id=eq.{user_id}")
                
                # Di versi postgrest terbaru, hapus berhasil tidak throw error.
                QMessageBox.information(self, "Sukses", f"Pengguna '{user_name}' berhasil dihapus.")
                self.refresh_data()
            except Exception as e:
                print(f"Error deleting user: {e}")
                QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat menghapus data: {e}")

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)


class PenggunaFormDialog(QDialog):
    """Dialog Popup Form untuk Tambah / Edit Pengguna."""
    
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.is_edit = user_data is not None
        
        self.setWindowTitle("Edit Pengguna" if self.is_edit else "Tambah Pengguna Baru")
        self.setMinimumSize(400, 600)
        self.setModal(True)
        
        # Apply theme
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
            
        self._build_ui()
        if self.is_edit:
            self._load_user_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title Label
        title_lbl = QLabel("FORM DATA PENGGUNA")
        title_lbl.setObjectName("page_title_lbl")
        title_lbl.setStyleSheet("background-color: transparent;")
        layout.addWidget(title_lbl)
        
        # Form Fields Container
        form_frame = QFrame()
        form_frame.setObjectName("form_card")
        form_frame.setProperty("class", "room_card") # Reusing same style class
        form_frame.setStyleSheet("QFrame#form_card { padding: 16px; }")
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(12)
        
        # Nama Lengkap
        form_layout.addWidget(QLabel("Nama Lengkap"))
        self.nama_input = QLineEdit()
        self.nama_input.setPlaceholderText("Contoh: Budi Santoso")
        form_layout.addWidget(self.nama_input)
        
        # Username
        form_layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Contoh: budi123")
        form_layout.addWidget(self.username_input)
        
        # Password
        pwd_lbl_text = "Password (kosongkan jika tidak ingin diubah)" if self.is_edit else "Password"
        form_layout.addWidget(QLabel(pwd_lbl_text))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.password_input)
        
        # Role
        form_layout.addWidget(QLabel("Role"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Mahasiswa", "Dosen", "Admin"])
        form_layout.addWidget(self.role_combo)
        
        # NIM/NIP
        form_layout.addWidget(QLabel("NIM / NIP"))
        self.nim_nip_input = QLineEdit()
        self.nim_nip_input.setPlaceholderText("Contoh: 19123456")
        form_layout.addWidget(self.nim_nip_input)
        
        # Status Aktif
        self.active_check = QCheckBox("Akun Aktif")
        self.active_check.setChecked(True)
        form_layout.addWidget(self.active_check)
        
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

    def _load_user_data(self):
        """Memuat data pengguna ke form input untuk mode edit."""
        u = self.user_data
        self.nama_input.setText(str(u.get('nama', '')))
        self.username_input.setText(str(u.get('username', '')))
        
        # Set role
        role_val = str(u.get('role', 'Mahasiswa'))
        idx = self.role_combo.findText(role_val)
        if idx >= 0:
            self.role_combo.setCurrentIndex(idx)
            
        self.nim_nip_input.setText(str(u.get('nim_nip', '')))
        self.active_check.setChecked(bool(u.get('is_active', True)))

    def handle_save(self):
        nama = self.nama_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()
        nim_nip = self.nim_nip_input.text().strip()
        is_active = self.active_check.isChecked()
        
        # Validasi
        if not nama or not username or not role:
            self.warning_lbl.setText("Mohon lengkapi Nama, Username, dan Role!")
            self.warning_lbl.show()
            return
            
        if not self.is_edit and not password:
            self.warning_lbl.setText("Password wajib diisi untuk pengguna baru!")
            self.warning_lbl.show()
            return
            
        try:
            payload = {
                "nama": nama,
                "username": username,
                "role": role,
                "nim_nip": nim_nip if nim_nip else "-",
                "is_active": is_active
            }
            
            # Jika ada password baru, hash passwordnya
            if password:
                # Generate salt and hash
                salt = bcrypt.gensalt(rounds=12)
                hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), salt)
                payload["password"] = hashed_pwd.decode('utf-8')
            
            supabase = get_supabase_client()
            
            if self.is_edit:
                # Update database
                user_id = self.user_data.get('id')
                res = supabase.table('pengguna').update(payload, f"id=eq.{user_id}")
            else:
                # Insert database
                res = supabase.table('pengguna').insert(payload)
                
            self.accept()
            
        except Exception as e:
            # Pengecekan username duplicate dll
            err_msg = str(e)
            if "duplicate key" in err_msg.lower() or "unique constraint" in err_msg.lower():
                self.warning_lbl.setText("Error: Username sudah digunakan!")
            else:
                self.warning_lbl.setText(f"Error database: {err_msg}")
            self.warning_lbl.show()
