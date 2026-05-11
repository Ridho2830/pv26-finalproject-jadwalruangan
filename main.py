import sys
from PySide6.QtWidgets import QApplication
from ui.index import StatusRuanganView

def main():
    app = QApplication(sys.argv)
    
    # Inisialisasi window utama dari ui/index.py
    window = StatusRuanganView()
    # Setup ukuran default dan minimal di sini agar konsisten (Portrait 9:16)
    window.resize(412, 915)
    window.setMinimumSize(414, 896)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()