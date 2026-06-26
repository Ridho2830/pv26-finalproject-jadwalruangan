from PySide6.QtWidgets import QWidget, QFrame
from PySide6.QtCore import Qt, QPoint, QRect, Signal
from PySide6.QtGui import QPainter, QPolygon, QColor, QBrush, QLinearGradient, QRadialGradient, QPixmap, QFont


def make_initial_avatar(initials: str, size: int, bg_color: str = "#22c55e") -> QPixmap:
    """Buat avatar lingkaran dengan inisial nama. Digunakan oleh semua role dashboard."""
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(QBrush(QColor(bg_color)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    font = QFont("Arial", int(size * 0.38), QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("white"))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter, initials.upper()[:2])
    painter.end()
    return result


class CubeWidget(QWidget):
    def __init__(self, color_hex, should_animate=False, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self._bounce_y = 0.0
        
        # Membatasi ukuran widget agar pas dengan desain kartu (100x100 px)
        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        
        self.anim = None

    def paintEvent(self, event):
        """Fungsi bawaan Qt yang dipanggil saat widget perlu digambar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        base_color = QColor(self.color_hex)
        by = 0.0  # Tidak ada animasi
        
        shadow_opacity = max(10, int(60 - abs(by) * 4))
        shadow_rx = max(15.0, 30.0 - abs(by) * 0.6)
        shadow_ry = max(5.0, 10.0 - abs(by) * 0.2)
        
        shadow_gradient = QRadialGradient(50, 85, shadow_rx)
        shadow_gradient.setColorAt(0, QColor(0, 0, 0, shadow_opacity))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_gradient))
        painter.drawEllipse(QPoint(50, 85), shadow_rx, shadow_ry)
        
        def pt(x, y):
            return QPoint(int(x), int(y + by))
            
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
        
        painter.end()



class ClickableFrame(QFrame):
    """QFrame yang memancarkan sinyal clicked saat diklik. Digunakan di semua dashboard kalender."""
    clicked = Signal()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit()