import sys
from PySide6.QtWidgets import QApplication, QStackedWidget
from ui.index import StatusRuanganView
from ui.login_page import LoginPage
from ui.admin.dashboard import AdminDashboard
from ui.mahasiswa.dashboard import MahasiswaPage
from ui.dosen.dashboard import DosenPage

class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReservasiKampus - Sistem Reservasi Ruangan")
        
        # Hitung ukuran 16:9 berdasarkan layar pengguna
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        
        # Ambil lebar penuh layar, lalu hitung tinggi sesuai rasio 16:9
        max_w = screen_geo.width()
        max_h = int(max_w * 9 / 16)
        
        # Jika tinggi hasil hitung melebihi layar, sesuaikan dari tinggi layar
        if max_h > screen_geo.height():
            max_h = screen_geo.height()
            max_w = int(max_h * 16 / 9)
        
        self.setMinimumSize(1024, 576)  # Minimum 16:9
        self.resize(max_w, max_h)
        
        # Inisialisasi views dengan meneruskan self sebagai parent/router
        self.public_view = StatusRuanganView(self)
        self.login_page = LoginPage(self)
        self.admin_dashboard = AdminDashboard(self)
        self.mahasiswa_page = None
        self.dosen_page = None
        
        # Tambah ke stacked widget
        self.addWidget(self.public_view)      # Index 0
        self.addWidget(self.login_page)       # Index 1
        self.addWidget(self.admin_dashboard)  # Index 2
        
        # Tampilkan halaman utama (Public View)
        self.switch_to_public()

    def switch_to_public(self):
        """Berpindah ke halaman utama status ruangan (Landscape)."""
        self.setCurrentWidget(self.public_view)
        self.public_view.refresh_data()

    def switch_to_login(self):
        """Berpindah ke halaman login (Landscape)."""
        self.setCurrentWidget(self.login_page)

    def switch_to_admin(self, user=None):
        """Berpindah ke halaman admin dashboard (Landscape)."""
        if user and hasattr(self.admin_dashboard, 'set_user_profile'):
            self.admin_dashboard.set_user_profile(user)
        self.setCurrentWidget(self.admin_dashboard)
        self.admin_dashboard.refresh_data()

    def switch_to_mahasiswa(self, user: dict):

        pengguna_id   = user.get('id')
        # Coba ambil 'nama', fallback ke 'username' jika kolom nama tidak ada
        pengguna_nama = user.get('nama') or user.get('username', 'Pengguna')

        # Hapus halaman lama dari stack jika sudah pernah dibuat
        if self.mahasiswa_page is not None:
            self.removeWidget(self.mahasiswa_page)
            self.mahasiswa_page.deleteLater()

        # Buat halaman baru dengan data user yang baru login
        self.mahasiswa_page = MahasiswaPage(
            pengguna_id=pengguna_id,
            pengguna_nama=pengguna_nama,
            parent=self
        )
        self.addWidget(self.mahasiswa_page)
        self.setCurrentWidget(self.mahasiswa_page)

    def switch_to_dosen(self, user: dict):
        pengguna_id   = user.get('id')
        pengguna_nama = user.get('nama') or user.get('username', 'Pengguna')

        if self.dosen_page is not None:
            self.removeWidget(self.dosen_page)
            self.dosen_page.deleteLater()

        self.dosen_page = DosenPage(
            pengguna_id=pengguna_id,
            pengguna_nama=pengguna_nama,
            parent=self
        )
        self.addWidget(self.dosen_page)
        self.setCurrentWidget(self.dosen_page)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()  # Langsung fullscreen / maximized
    sys.exit(app.exec())

if __name__ == "__main__":
    main()