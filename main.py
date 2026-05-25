import sys
from PySide6.QtWidgets import QApplication, QStackedWidget
from ui.index import StatusRuanganView
from ui.loginPage import LoginPage
from ui.admin.dashboard import AdminDashboard
from ui.mahasiswa import MahasiswaPage

class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReservasiKampus - Sistem Reservasi Ruangan")
        self.setMinimumSize(800, 500)
        self.resize(1024, 768)
        
        # Inisialisasi views dengan meneruskan self sebagai parent/router
        self.public_view = StatusRuanganView(self)
        self.login_page = LoginPage(self)
        self.admin_dashboard = AdminDashboard(self)
        self.mahasiswa_page = MahasiswaPage(self)
        
        # Tambah ke stacked widget
        self.addWidget(self.public_view)      # Index 0
        self.addWidget(self.login_page)       # Index 1
        self.addWidget(self.admin_dashboard)  # Index 2
        self.addWidget(self.mahasiswa_page)   # Index 3
        
        # Tampilkan halaman utama (Public View)
        self.switch_to_public()

    def switch_to_public(self):
        """Berpindah ke halaman utama status ruangan (Landscape)."""
        self.setMinimumSize(800, 500)
        self.resize(1024, 768)
        self.setCurrentWidget(self.public_view)
        self.public_view.refresh_data()

    def switch_to_login(self):
        """Berpindah ke halaman login (Landscape)."""
        self.setMinimumSize(800, 500)
        self.resize(1024, 768)
        self.setCurrentWidget(self.login_page)

    def switch_to_admin(self):
        """Berpindah ke halaman admin dashboard (Landscape)."""
        self.setMinimumSize(800, 500)
        self.resize(1024, 768)
        self.setCurrentWidget(self.admin_dashboard)
        self.admin_dashboard.refresh_data()

    def switch_to_mahasiswa(self):
        """Berpindah ke halaman mahasiswa (Landscape)."""
        self.setMinimumSize(800, 500)
        self.resize(1024, 768)
        self.setCurrentWidget(self.mahasiswa_page)
        self.mahasiswa_page.refresh_data()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()