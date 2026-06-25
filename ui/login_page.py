import os
import bcrypt
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QScrollArea, 
                               QSizePolicy, QCheckBox, QToolButton)
from utils.mode import theme_manager
from api.supabase import get_supabase_client

def _make_eye_icon(visible: bool) -> QIcon:
    import os
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon')
    fname = "mata.png" if visible else "mata_garis.png"
    img_path = os.path.normpath(os.path.join(assets_dir, fname))
    pix = QPixmap(img_path).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return QIcon(pix)


def _make_checkmark_pixmap() -> QPixmap:
    import os
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon')
    img_path = os.path.normpath(os.path.join(assets_dir, "kotak_centang.png"))
    return QPixmap(img_path).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)


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
        self.left_panel.setAttribute(Qt.WA_StyledBackground, True)
        self.left_panel.setStyleSheet("QFrame#left_panel { background-color: #1a1625; } QFrame#left_panel * { background: transparent; }")
        
        layout = QVBoxLayout(self.left_panel)
        layout.setContentsMargins(60, 60, 60, 60)
        
        # Logo and brand
        brand_layout = QHBoxLayout()
        logo = QLabel()
        import os
        logo_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets','icon' ,'logo.png'))
        logo_pix = QPixmap(logo_path).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(logo_pix)
        logo.setStyleSheet("background: transparent;")
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
        illustration.setStyleSheet("background: transparent;")
        layout.addWidget(illustration)
        
        layout.addStretch()
        
        # Text
        title = QLabel("Sistem Reservasi Ruangan Kuliah Digital")
        title.setObjectName("left_title")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent; margin-top: 20px;")
        
        desc = QLabel("Kelola jadwal, pantau ketersediaan ruangan, dan optimalkan penggunaan fasilitas akademik dalam satu platform terintegrasi.")
        desc.setObjectName("left_desc")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a09eb0; font-size: 14px; background: transparent; margin-top: 10px;")
        
        layout.addWidget(title)
        layout.addWidget(desc)
        
        footer = QLabel("© 2024 Sistem Akademik Terpadu")
        footer.setStyleSheet("color: #6b7280; font-size: 12px; margin-top: 40px; background: transparent;")
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

        # Password field + tombol mata dalam satu container
        pass_container = QFrame()
        pass_container.setFixedHeight(45)
        pass_container.setStyleSheet("""
            QFrame {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #f9fafb;
            }
            QFrame:focus-within {
                border: 1px solid #00b8a9;
                background-color: #ffffff;
            }
        """)
        pass_h_layout = QHBoxLayout(pass_container)
        pass_h_layout.setContentsMargins(10, 0, 6, 0)
        pass_h_layout.setSpacing(0)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #111827;
                font-size: 14px;
                padding: 0px;
            }
        """)

        # Tombol mata
        self.toggle_pass_btn = QToolButton()
        self.toggle_pass_btn.setIcon(_make_eye_icon(False))
        self.toggle_pass_btn.setIconSize(QSize(20, 20))
        self.toggle_pass_btn.setFixedSize(32, 32)
        self.toggle_pass_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_pass_btn.setCheckable(True)
        self.toggle_pass_btn.setToolTip("Tampilkan / sembunyikan password")
        self.toggle_pass_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                border-radius: 4px;
            }
            QToolButton:hover { background: rgba(0,0,0,0.05); }
        """)
        self.toggle_pass_btn.clicked.connect(self._toggle_password_visibility)

        pass_h_layout.addWidget(self.password_input)
        pass_h_layout.addWidget(self.toggle_pass_btn)

        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Checkbox & Forgot Password
        options_layout = QHBoxLayout()
        remember_cb = QCheckBox("Ingat sesi saya")
        self._remember_cb = remember_cb

        import os
        assets_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon')
        )
        kotak_path      = os.path.join(assets_dir, "kotak.png").replace("\\", "/")
        kotak_centang_path = os.path.join(assets_dir, "kotak_centang.png").replace("\\", "/")

        kotak_ada         = os.path.exists(kotak_path)
        kotak_centang_ada = os.path.exists(kotak_centang_path)

        # unchecked state
        if kotak_ada:
            unchecked_style = f'image: url("{kotak_path}"); border: none; background: transparent;'
        else:
            unchecked_style = "border: 1.5px solid #d1d5db; border-radius: 4px; background: #ffffff;"

        # checked state
        if kotak_centang_ada:
            checked_style = f'image: url("{kotak_centang_path}"); border: none; background: transparent;'
        else:
            # fallback: gambar centang pakai QPainter, simpan ke temp
            import tempfile
            _tmp = os.path.join(tempfile.gettempdir(), "crsys_checkmark.png").replace("\\", "/")
            _make_checkmark_pixmap().save(_tmp)
            checked_style = f'image: url("{_tmp}"); border: none;'

        remember_cb.setStyleSheet(f"""
            QCheckBox {{
                color: #4b5563;
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                {unchecked_style}
            }}
            QCheckBox::indicator:checked {{
                width: 16px;
                height: 16px;
                {checked_style}
            }}
        """)
        
        forgot_btn = QPushButton("Lupa Password?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet("color: #00b8a9; font-size: 13px; background: transparent; border: none; text-align: right;")
        forgot_btn.clicked.connect(self._handle_forgot_password)
        
        options_layout.addWidget(remember_cb)
        options_layout.addStretch()
        options_layout.addWidget(forgot_btn)
        
        form_layout.addWidget(user_lbl)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(pass_lbl)
        form_layout.addWidget(pass_container)
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

    def _toggle_password_visibility(self, checked: bool):
        """Toggle antara tampilkan dan sembunyikan password."""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_pass_btn.setIcon(_make_eye_icon(True))   # mata terbuka
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_pass_btn.setIcon(_make_eye_icon(False))  # mata + garis coret

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        self.error_label.setText("")
        self.error_label.hide()
        
        if not username or not password:
            self.show_error("Username dan password tidak boleh kosong!")
            return
            
        if hasattr(self, 'worker') and self.worker.isRunning():
            return
            
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Memverifikasi...")
        
        from utils.worker import Worker
        self.worker = Worker(self._fetch_login_worker, username, password)
        self.worker.finished.connect(self._on_login_finished)
        self.worker.error.connect(self._on_login_error)
        self.worker.start()

    def _fetch_login_worker(self, username, password):
        from api.supabase import get_supabase_client
        import bcrypt
        supabase = get_supabase_client()
        user_data = supabase.table('pengguna').select(filters=f"or=(username.eq.{username},nim_nip.eq.{username})")
        
        if not user_data:
            return {"success": False, "error": "Username atau password salah!"}
            
        user = user_data[0]
        hashed_pw = user.get('password')
        is_active = user.get('is_active', True)
        
        if not is_active:
            return {"success": False, "error": "Akun Anda telah dinonaktifkan!"}
            
        if bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
            return {"success": True, "user": user}
        else:
            return {"success": False, "error": "Username atau password salah!"}

    def _on_login_error(self, err_msg):
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Masuk")
        self.show_error("Koneksi gagal! Periksa koneksi internet database Anda.")

    def _on_login_finished(self, result):
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Masuk")
        
        if not result["success"]:
            self.show_error(result["error"])
            return
            
        user = result["user"]
        role = user.get('role', 'Mahasiswa')
        
        self.username_input.clear()
        self.password_input.clear()
        
        parent_widget = self.parent()
        while parent_widget is not None:
            if role == 'Admin' and hasattr(parent_widget, 'switch_to_admin'):
                parent_widget.switch_to_admin(user)
                return
            elif role == 'Dosen' and hasattr(parent_widget, 'switch_to_dosen'):
                parent_widget.switch_to_dosen(user)
                return
            elif role not in ('Admin', 'Dosen') and hasattr(parent_widget, 'switch_to_mahasiswa'):
                parent_widget.switch_to_mahasiswa(user)
                return
            parent_widget = parent_widget.parent()

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()

    def handle_back(self):
        self.username_input.clear()
        self.password_input.clear()
        self.error_label.hide()
        
        parent_widget = self.parent()
        while parent_widget is not None:
            if hasattr(parent_widget, 'switch_to_public'):
                parent_widget.switch_to_public()
                return
            parent_widget = parent_widget.parent()

    def _handle_forgot_password(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Lupa Password",
            "Silakan hubungi administrator kampus untuk mereset password Anda.\n\n"
            "📧 admin@kampus.ac.id\n"
            "📞 (0370) 123-456"
        )

    def apply_theme(self):
        # We override the global theme for this specific page to keep its exact design
        pass