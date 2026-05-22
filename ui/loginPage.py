import bcrypt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QScrollArea, 
                               QGridLayout)
from utils.mode import theme_manager
from api.supabase import get_supabase_client

class LoginPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Outer layout containing the scroll area
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)
        
        # Scroll Area for responsiveness on small screens/windows
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.viewport().setStyleSheet("background: transparent; border: none;")
        
        # Scroll Content Widget
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("login_scroll_content")
        self.scroll_content.setStyleSheet("background: transparent;")
        
        # Grid layout to center the login container
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(24, 24, 24, 24)
        
        # Centered login container widget
        self.login_container = QWidget()
        self.login_container.setObjectName("login_container")
        self.login_container.setStyleSheet("background: transparent;")
        self.login_container.setMinimumWidth(280)
        self.login_container.setMaximumWidth(380)
        
        # Inner layout for the login widgets
        self.main_layout = QVBoxLayout(self.login_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)
        
        self._build_ui()
        
        # Add login container to grid layout (aligned to center)
        self.grid_layout.addWidget(self.login_container, 0, 0, Qt.AlignCenter)
        
        # Set scroll content and add scroll area to outer layout
        self.scroll_area.setWidget(self.scroll_content)
        self.outer_layout.addWidget(self.scroll_area)
        
        # Load style
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _build_ui(self):
        # 1. Logo & Judul Aplikasi
        logo_label = QLabel("🏢")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 56px; background-color: transparent;")
        self.main_layout.addWidget(logo_label)
        
        app_title = QLabel("ReservasiKampus")
        app_title.setObjectName("login_app_title")
        app_title.setAlignment(Qt.AlignCenter)
        app_title.setStyleSheet("background-color: transparent;")
        self.main_layout.addWidget(app_title)
        
        page_title = QLabel("Login Administrator")
        page_title.setObjectName("page_title_lbl")
        page_title.setAlignment(Qt.AlignCenter)
        page_title.setStyleSheet("background-color: transparent; margin-bottom: 10px;")
        self.main_layout.addWidget(page_title)
        
        # 2. Form Container
        self.form_card = QFrame()
        self.form_card.setObjectName("form_card")
        self.form_card.setProperty("class", "room_card")
        self.form_card.setStyleSheet("QFrame#form_card { padding: 24px; }")
        
        form_layout = QVBoxLayout(self.form_card)
        form_layout.setSpacing(16)
        
        # Field Username
        username_label = QLabel("Username")
        username_label.setObjectName("username_lbl")
        username_label.setStyleSheet("background-color: transparent;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Masukkan username...")
        self.username_input.setFixedHeight(40)
        
        # Field Password
        password_label = QLabel("Password")
        password_label.setObjectName("password_lbl")
        password_label.setStyleSheet("background-color: transparent;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Masukkan password...")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        
        # Tombol Enter untuk login
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        self.main_layout.addWidget(self.form_card)
        
        # 3. Error Label (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: bold; background-color: transparent;")
        self.error_label.hide()
        self.main_layout.addWidget(self.error_label)
        
        # 4. Buttons Layout
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)
        
        self.submit_btn = QPushButton("Masuk Ke Sistem")
        self.submit_btn.setObjectName("login_btn")
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setFixedHeight(42)
        self.submit_btn.clicked.connect(self.handle_login)
        
        self.back_btn = QPushButton("Kembali ke Beranda")
        self.back_btn.setObjectName("back_btn")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedHeight(40)
        self.back_btn.clicked.connect(self.handle_back)
        
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.back_btn)
        
        self.main_layout.addLayout(btn_layout)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Reset errors
        self.error_label.setText("")
        self.error_label.hide()
        
        if not username or not password:
            self.show_error("Username dan password tidak boleh kosong!")
            return
            
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Memverifikasi...")
        
        try:
            # Query pengguna dari Supabase
            supabase = get_supabase_client()
            user_data = supabase.table('pengguna').select(filters=f"username=eq.{username}")
            
            if not user_data:
                self.show_error("Username atau password salah!")
                return
                
            user = user_data[0]
            hashed_pw = user.get('password')
            role = user.get('role', 'Mahasiswa')
            is_active = user.get('is_active', True)
            
            if not is_active:
                self.show_error("Akun Anda telah dinonaktifkan!")
                return
                
            # Verifikasi password bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
                if role != 'Admin':
                    self.show_error("Akses ditolak! Hanya Administrator yang dapat masuk.")
                    return
                
                # Sukses Login -> Bersihkan form & Switch screen
                self.username_input.clear()
                self.password_input.clear()
                parent_widget = self.parent()
                if parent_widget and hasattr(parent_widget, 'switch_to_admin'):
                    parent_widget.switch_to_admin()
            else:
                self.show_error("Username atau password salah!")
        except Exception as e:
            print(f"Login error: {e}")
            self.show_error("Koneksi gagal! Periksa koneksi internet database Anda.")
        finally:
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Masuk Ke Sistem")

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()

    def handle_back(self):
        # Bersihkan form
        self.username_input.clear()
        self.password_input.clear()
        self.error_label.hide()
        
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'switch_to_public'):
            parent_widget.switch_to_public()

    def apply_theme(self):
        stylesheet = theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
