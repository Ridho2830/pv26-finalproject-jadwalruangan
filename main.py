import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QLabel   
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt                           
from ui.index import StatusRuanganView
from ui.login_page import LoginPage
from ui.admin.dashboard import AdminDashboard
from ui.mahasiswa.dashboard import MahasiswaPage
from ui.dosen.dashboard import DosenPage


def _make_app_icon() -> QIcon:
    import os
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "icon", "logo.png")
    if os.path.exists(logo_path):
        return QIcon(logo_path)
    return QIcon()


ANGGOTA = [
    ("Rafly Ridho' Sukardi", "F1D02310134"),
    ("Muhammad Tegar Bijanta", "F1D02410081"),
    ("Yurian Fathur Fajar", "F1D02310097"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReservasiKampus - Sistem Reservasi Ruangan")

        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        max_w = screen_geo.width()
        max_h = int(max_w * 9 / 16)

        if max_h > screen_geo.height():
            max_h = screen_geo.height()
            max_w = int(max_h * 16 / 9)

        self.setMinimumSize(1024, 576)
        self.resize(max_w, max_h)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.public_view = StatusRuanganView(self)
        self.login_page = LoginPage(self)
        self.admin_dashboard = AdminDashboard(self)
        self.mahasiswa_page = None
        self.dosen_page = None

        self.stack.addWidget(self.public_view)      # 0
        self.stack.addWidget(self.login_page)       # 1
        self.stack.addWidget(self.admin_dashboard)  # 2

        self._build_menu_bar()
        self._build_status_bar()

        self.switch_to_public()

    def _build_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        act_home = QAction("🏠 Beranda", self)
        act_home.setShortcut("Ctrl+H")
        act_home.triggered.connect(self.switch_to_public)
        file_menu.addAction(act_home)

        act_login = QAction("🔑 Login", self)
        act_login.setShortcut("Ctrl+L")
        act_login.triggered.connect(self.switch_to_login)
        file_menu.addAction(act_login)

        file_menu.addSeparator()

        act_exit = QAction("⎋ Keluar", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        help_menu = menubar.addMenu("&Help")

        act_about = QAction("ℹ️ Tentang Aplikasi", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _build_status_bar(self):
        sb = self.statusBar()          
        sb.setFixedHeight(26)
        anggota_str = "   |   ".join(f"{nama} ({nim})" for nama, nim in ANGGOTA)
        self._status_label = QLabel(anggota_str)
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #8888a8; font-size: 11px; background: transparent;")
        sb.addWidget(self._status_label, 1)

    def _show_about(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Tentang ReservasiKampus",
            "ReservasiKampus — Sistem Reservasi Ruangan Kuliah\n\n"
            "Dibangun dengan Python + PySide6 & Supabase\n\n"
            "Anggota Kelompok:\n" +
            "\n".join(f"  • {n} ({nim})" for n, nim in ANGGOTA)
        )

    def switch_to_public(self):
        self.stack.setCurrentWidget(self.public_view)
        self.public_view.refresh_data()

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_page)

    def switch_to_admin(self, user=None):
        if user and hasattr(self.admin_dashboard, 'set_user_profile'):
            self.admin_dashboard.set_user_profile(user)
        self.stack.setCurrentWidget(self.admin_dashboard)
        self.admin_dashboard.refresh_data()

    def switch_to_mahasiswa(self, user: dict):
        pengguna_id   = user.get('id')
        pengguna_nama = user.get('nama') or user.get('username', 'Pengguna')

        if self.mahasiswa_page is not None:
            self.stack.removeWidget(self.mahasiswa_page)
            self.mahasiswa_page.deleteLater()

        self.mahasiswa_page = MahasiswaPage(
            pengguna_id=pengguna_id,
            pengguna_nama=pengguna_nama,
            parent=self
        )
        self.stack.addWidget(self.mahasiswa_page)
        self.stack.setCurrentWidget(self.mahasiswa_page)

    def switch_to_dosen(self, user: dict):
        pengguna_id   = user.get('id')
        pengguna_nama = user.get('nama') or user.get('username', 'Pengguna')

        if self.dosen_page is not None:
            self.stack.removeWidget(self.dosen_page)
            self.dosen_page.deleteLater()

        self.dosen_page = DosenPage(
            pengguna_id=pengguna_id,
            pengguna_nama=pengguna_nama,
            parent=self
        )
        self.stack.addWidget(self.dosen_page)
        self.stack.setCurrentWidget(self.dosen_page)


def main():
    app = QApplication(sys.argv)
    icon = _make_app_icon()
    app.setWindowIcon(icon)

    from utils.mode import theme_manager
    app.setStyleSheet(theme_manager.get_stylesheet())
    theme_manager.theme_changed.connect(app.setStyleSheet)

    window = MainWindow()
    window.setWindowIcon(icon)
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()