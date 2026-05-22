from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QPolygon, QColor, QBrush, QLinearGradient, QRadialGradient

class CubeWidget(QWidget):
    def __init__(self, color_hex, should_animate=False, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self._bounce_y = 0.0
        
        # Membatasi ukuran widget agar pas dengan desain kartu (100x100 px)
        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        
        self.anim = None
        if should_animate:
            self.start_floating_animation()

    def get_bounce_y(self) -> float:
        return self._bounce_y

    def set_bounce_y(self, val: float):
        self._bounce_y = val
        self.update()

    # Definisikan property untuk Qt Animation
    bounce_y = Property(float, get_bounce_y, set_bounce_y)

    def start_floating_animation(self):
        """Memulai animasi melayang naik-turun secara halus."""
        self.anim = QPropertyAnimation(self, b"bounce_y")
        self.anim.setDuration(2000)  # 2 detik per siklus
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.5, -8.0)  # Melayang naik 8px di tengah siklus
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)  # Loop selamanya
        self.anim.start()

    def paintEvent(self, event):
        """Fungsi bawaan Qt yang dipanggil saat widget perlu digambar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        base_color = QColor(self.color_hex)
        by = self._bounce_y  # Ambil offset vertical untuk animasi
        
        # 1. Gambar Bayangan di Bawah (Drop Shadow) - Berada di lantai tetap (tidak ikut memantul)
        # Ukuran & intensitas bayangan mengecil saat kubus melayang ke atas
        shadow_opacity = max(10, int(60 - abs(by) * 4))
        shadow_rx = max(15.0, 30.0 - abs(by) * 0.6)
        shadow_ry = max(5.0, 10.0 - abs(by) * 0.2)
        
        shadow_gradient = QRadialGradient(50, 85, shadow_rx)
        shadow_gradient.setColorAt(0, QColor(0, 0, 0, shadow_opacity))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_gradient))
        painter.drawEllipse(QPoint(50, 85), shadow_rx, shadow_ry)
        
        # Fungsi pembantu untuk koordinat titik kubus dengan offset animasi
        def pt(x, y):
            return QPoint(int(x), int(y + by))
            
        # 2. Menggambar Sisi Atas (Top Face) - Terang (Lighting dari atas)
        top_poly = QPolygon([
            pt(50, 15),
            pt(88, 32),
            pt(50, 49),
            pt(12, 32)
        ])
        top_grad = QLinearGradient(pt(50, 15), pt(50, 49))
        c_top1 = QColor(base_color).lighter(125)
        c_top2 = QColor(base_color).lighter(105)
        c_top1.setAlphaF(0.7)
        c_top2.setAlphaF(0.7)
        top_grad.setColorAt(0.0, c_top1)
        top_grad.setColorAt(1.0, c_top2)
        
        painter.setBrush(QBrush(top_grad))
        painter.drawPolygon(top_poly)
        
        # 3. Menggambar Sisi Kiri (Left Face) - Medium (Lighting samping)
        left_poly = QPolygon([
            pt(12, 32),
            pt(50, 49),
            pt(50, 84),
            pt(12, 67)
        ])
        left_grad = QLinearGradient(pt(12, 32), pt(50, 84))
        c_left1 = QColor(base_color).darker(105)
        c_left2 = QColor(base_color).darker(120)
        c_left1.setAlphaF(0.85)
        c_left2.setAlphaF(0.85)
        left_grad.setColorAt(0.0, c_left1)
        left_grad.setColorAt(1.0, c_left2)
        
        painter.setBrush(QBrush(left_grad))
        painter.drawPolygon(left_poly)
        
        # 4. Menggambar Sisi Kanan (Right Face) - Paling gelap (Bayangan samping)
        right_poly = QPolygon([
            pt(50, 49),
            pt(88, 32),
            pt(88, 67),
            pt(50, 84)
        ])
        right_grad = QLinearGradient(pt(50, 49), pt(88, 67))
        c_right1 = QColor(base_color).darker(125)
        c_right2 = QColor(base_color).darker(145)
        c_right1.setAlphaF(1.0)
        c_right2.setAlphaF(1.0)
        right_grad.setColorAt(0.0, c_right1)
        right_grad.setColorAt(1.0, c_right2)
        
        painter.setBrush(QBrush(right_grad))
        painter.drawPolygon(right_poly)
        
        # Explicitly end painting to release resources immediately
        painter.end()

