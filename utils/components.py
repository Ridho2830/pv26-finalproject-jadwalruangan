from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QPolygon, QColor, QBrush

class CubeWidget(QWidget):

    """
    Widget kustom untuk menggambar kubus 3D Isometrik.
    Digunakan pada kartu ruangan untuk indikasi status visual.
    """
    def __init__(self, color_hex, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        # Membatasi ukuran widget agar pas dengan desain kartu (100x100 px)
        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)

    def paintEvent(self, event):
        """Fungsi bawaan Qt yang dipanggil saat widget perlu digambar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # Agar garis halus
        
        base_color = QColor(self.color_hex)
        
        # Fungsi pembantu untuk menskalakan titik (tetap 100x100)
        def scale_pt(x, y):
            return QPoint(int(x * 1.0), int(y * 1.0))

            
        # 1. Menggambar Sisi Atas (Top Face)
        top_poly = QPolygon([
            scale_pt(50, 10),
            scale_pt(90, 30),
            scale_pt(50, 50),
            scale_pt(10, 30)
        ])
        top_color = QColor(base_color)
        top_color.setAlphaF(0.4) # Transparansi 40%
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(top_color))
        painter.drawPolygon(top_poly)
        
        # 2. Menggambar Sisi Kiri (Left Face)
        left_poly = QPolygon([
            scale_pt(10, 30),
            scale_pt(50, 50),
            scale_pt(50, 90),
            scale_pt(10, 70)
        ])
        left_color = QColor(base_color)
        left_color.setAlphaF(0.7) # Transparansi 70%
        painter.setBrush(QBrush(left_color))
        painter.drawPolygon(left_poly)
        
        # 3. Menggambar Sisi Kanan (Right Face)
        right_poly = QPolygon([
            scale_pt(50, 50),
            scale_pt(90, 30),
            scale_pt(90, 70),
            scale_pt(50, 90)
        ])
        right_color = QColor(base_color)
        right_color.setAlphaF(1.0) # Warna penuh tanpa transparansi
        painter.setBrush(QBrush(right_color))
        painter.drawPolygon(right_poly)
