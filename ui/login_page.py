import os
import bcrypt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QScrollArea, 
                               QSizePolicy, QCheckBox)
from utils.mode import theme_manager
from api.supabase import get_supabase_client

class LoginPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("login_page")
        
        # Outer layout
        self.outer_layout = QHBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)
        
        self._build_left_panel()
        self._build_right_panel()
        
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
        
        # Base styles for this page (split screen colors)
        self.setStyleSheet("""
            QWidget#login_page { background-color: #ffffff; }
            QFrame#left_panel { background-color: #1a1625; }
            QLabel#left_title { color: white; font-size: 24px; font-weight: bold; margin-top: 20px;}
            QLabel#left_desc { color: #a09eb0; font-size: 14px; margin-top: 10px; }
            QLabel#right_title { color: #1a1625; font-size: 28px; font-weight: bold; }
            QLabel#right_subtitle { color: #6b7280; font-size: 14px; margin-bottom: 20px; }
            QLineEdit { 
                padding: 10px; 
                border: 1px solid #e5e7eb; 
                border-radius: 8px; 
                background-color: #f9fafb;
                color: #111827;
            }
            QLineEdit:focus { border: 1px solid #00b8a9; background-color: #ffffff; }
            QPushButton#public_btn { 
                background-color: white; 
                color: #4b5563; 
                border: 1px solid #d1d5db; 
                border-radius: 8px; 
                padding: 8px;
            }
            QPushButton#public_btn:hover { background-color: #f3f4f6; }
        """)

    def _build_left_panel(self):
        self.left_panel = QFrame()
        self.left_panel.setObjectName("left_panel")
        self.left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self.left_panel)
        layout.setContentsMargins(60, 60, 60, 60)
        
        # Logo and brand
        brand_layout = QHBoxLayout()
        logo = QLabel("🏢")
        logo.setStyleSheet("font-size: 24px; background: transparent;")
        brand_text = QLabel("ReservasiKampus")
        brand_text.setStyleSheet("color: white; font-size: 20px; font-weight: bold; background: transparent;")
        brand_layout.addWidget(logo)
        brand_layout.addWidget(brand_text)
        brand_layout.addStretch()
        
        layout.addLayout(brand_layout)
        layout.addStretch()
        
        # Illustration
        illustration = QLabel()
        img_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'login_illustration.png')
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            illustration.setPixmap(pixmap)
        else:
            illustration.setText("🖼️ [Ilustrasi Ruangan]")
            illustration.setStyleSheet("color: #4b5563; font-size: 24px;")
            
        illustration.setAlignment(Qt.AlignCenter)
        layout.addWidget(illustration)
        
        layout.addStretch()
        
        # Text
        title = QLabel("Sistem Reservasi Ruangan Kuliah Digital")
        title.setObjectName("left_title")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        
        desc = QLabel("Kelola jadwal, pantau ketersediaan ruangan, dan optimalkan penggunaan fasilitas akademik dalam satu platform terintegrasi.")
        desc.setObjectName("left_desc")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        
        layout.addWidget(title)
        layout.addWidget(desc)
        
        footer = QLabel("© 2024 Sistem Akademik Terpadu")
        footer.setStyleSheet("color: #6b7280; font-size: 12px; margin-top: 40px;")
        footer.setAlignment(Qt.AlignLeft)
        layout.addWidget(footer)
        
        self.outer_layout.addWidget(self.left_panel, stretch=1)

    def _build_right_panel(self):
        self.right_panel = QFrame()
        self.right_panel.setObjectName("right_panel")
        self.right_panel.setStyleSheet("background-color: white;")
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Use a scroll area for responsiveness on smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.right_panel)
        
        layout = QVBoxLayout(self.right_panel)
        layout.setAlignment(Qt.AlignCenter)
        
        # Container for form to keep it centered and max-width
        form_container = QWidget()
        form_container.setMaximumWidth(400)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)
        
        # Welcome text
        title = QLabel("Selamat Datang 👋")
        title.setObjectName("right_title")
        
        subtitle = QLabel("Masuk ke akun Anda untuk melanjutkan")
        subtitle.setObjectName("right_subtitle")
        
        form_layout.addWidget(title)
        form_layout.addWidget(subtitle)
        
        # Form fields
        user_lbl = QLabel("Username / NIP / NIM")
        user_lbl.setStyleSheet("color: #374151; font-size: 13px; font-weight: 500;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Masukkan username Anda")
        self.username_input.setFixedHeight(45)
        
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet("color: #374151; font-size: 13px; font-weight: 500;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(45)
        
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Checkbox & Forgot Password
        options_layout = QHBoxLayout()
        remember_cb = QCheckBox("Ingat sesi saya")
        remember_cb.setStyleSheet("color: #4b5563; font-size: 13px;")
        
        forgot_btn = QPushButton("Lupa Password?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet("color: #00b8a9; font-size: 13px; background: transparent; border: none; text-align: right;")
        
        options_layout.addWidget(remember_cb)
        options_layout.addStretch()
        options_layout.addWidget(forgot_btn)
        
        form_layout.addWidget(user_lbl)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(pass_lbl)
        form_layout.addWidget(self.password_input)
        form_layout.addLayout(options_layout)
        
        # Error Label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: bold; margin-top: 5px;")
        self.error_label.hide()
        form_layout.addWidget(self.error_label)
        
        # Submit Button
        self.submit_btn = QPushButton("Masuk")
        self.submit_btn.setObjectName("login_submit_btn_xyz")
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setFixedHeight(45)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b8a9; 
                color: white; 
                border: none;
                border-radius: 8px; 
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #009f92; }
        """)
        self.submit_btn.clicked.connect(self.handle_login)
        form_layout.addWidget(self.submit_btn)
        
        # Divider
        divider_layout = QHBoxLayout()
        divider_line1 = QFrame()
        divider_line1.setFrameShape(QFrame.HLine)
        divider_line1.setStyleSheet("color: #e5e7eb; border: 1px solid #e5e7eb;")
        divider_line2 = QFrame()
        divider_line2.setFrameShape(QFrame.HLine)
        divider_line2.setStyleSheet("color: #e5e7eb; border: 1px solid #e5e7eb;")
        
        divider_layout.addWidget(divider_line1)
        divider_layout.addWidget(divider_line2)
        
        form_layout.addSpacing(20)
        form_layout.addLayout(divider_layout)
        form_layout.addSpacing(10)
        
        # Public Dashboard Link
        public_info = QLabel("Hanya ingin melihat ketersediaan ruangan?")
        public_info.setStyleSheet("color: #6b7280; font-size: 13px;")
        public_info.setAlignment(Qt.AlignCenter)
        
        self.back_btn = QPushButton("📅 Lihat Dashboard Publik")
        self.back_btn.setObjectName("public_btn")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedHeight(40)
        self.back_btn.clicked.connect(self.handle_back)
        
        form_layout.addWidget(public_info)
        form_layout.addWidget(self.back_btn)
        
        layout.addWidget(form_container)
        
        self.outer_layout.addWidget(scroll, stretch=1)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        self.error_label.setText("")
        self.error_label.hide()
        
        if not username or not password:
            self.show_error("Username dan password tidak boleh kosong!")
            return
            
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Memverifikasi...")
        
        try:
            supabase = get_supabase_client()
            user_data = supabase.table('pengguna').select(filters=f"or=(username.eq.{username},nim_nip.eq.{username})")
            
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
                
            if bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
                # Sukses Login -> Bersihkan form & Switch screen
                self.username_input.clear()
                self.password_input.clear()
                parent_widget = self.parent()
                
                if parent_widget:
                    if role == 'Admin':
                        if hasattr(parent_widget, 'switch_to_admin'):
                            parent_widget.switch_to_admin(user)
                    else:
                        # Mahasiswa dan Dosen
                        if hasattr(parent_widget, 'switch_to_mahasiswa'):
                            parent_widget.switch_to_mahasiswa(user)
            else:
                self.show_error("Username atau password salah!")
        except Exception as e:
            print(f"Login error: {e}")
            self.show_error("Koneksi gagal! Periksa koneksi internet database Anda.")
        finally:
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Masuk")

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()

    def handle_back(self):
        self.username_input.clear()
        self.password_input.clear()
        self.error_label.hide()
        
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'switch_to_public'):
            parent_widget.switch_to_public()

    def apply_theme(self):
        # We override the global theme for this specific page to keep its exact design
        pass
