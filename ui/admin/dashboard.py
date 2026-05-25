from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal, Slot
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QFrame, QStackedWidget,
                                QScrollArea, QGridLayout, QSizePolicy, QLayout, QLayoutItem, QLineEdit)
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QCursor
from utils.components import CubeWidget
from api.supabase import get_supabase_client
from ui.chatbot import ChatbotDialog
from datetime import datetime

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, hSpacing=-1, vSpacing=-1):
        super().__init__(parent)
        if margin != -1: self.setContentsMargins(margin, margin, margin, margin)
        self._hSpace = hSpacing
        self._vSpace = vSpacing
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item: item = self.takeAt(0)

    def addItem(self, item): self.itemList.append(item)
    def horizontalSpacing(self): return self._hSpace if self._hSpace >= 0 else self.spacing()
    def verticalSpacing(self): return self._vSpace if self._vSpace >= 0 else self.spacing()
    def count(self): return len(self.itemList)
    def itemAt(self, index): return self.itemList[index] if 0 <= index < len(self.itemList) else None
    def takeAt(self, index): return self.itemList.pop(index) if 0 <= index < len(self.itemList) else None
    def expandingDirections(self): return Qt.Orientations(0)
    def hasHeightForWidth(self): return True
    def heightForWidth(self, width): return self.doLayout(QRect(0, 0, width, 0), True)
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)
    def sizeHint(self): return self.minimumSize()
    def minimumSize(self):
        size = QSize()
        for item in self.itemList: size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size
    def doLayout(self, rect, testOnly):
        m = self.contentsMargins()
        effectiveRect = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y, lineHeight = effectiveRect.x(), effectiveRect.y(), 0
        for item in self.itemList:
            wid = item.widget()
            spaceX = self.horizontalSpacing()
            if spaceX == -1: spaceX = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.verticalSpacing()
            if spaceY == -1: spaceY = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > effectiveRect.right() and lineHeight > 0:
                x, y = effectiveRect.x(), y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            if not testOnly: item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        return y + lineHeight - rect.y() + m.bottom()


class RoomCard(QFrame):
    clicked = Signal(dict)
    
    def __init__(self, room_data, parent=None):
        super().__init__(parent)
        self.room_data = room_data
        self.setObjectName("room_card")
        self.setFixedSize(220, 280)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        status = room_data.get('status', 'Tersedia')
        if status in ("Digunakan", "Terpakai"): status = "Digunakan"
        elif status in ("Dosen", "Terbooking"): status = "Dosen"
        elif status == "Konflik": status = "Konflik"
        else: status = "Tersedia"
        
        colors = {
            "Tersedia": ("#4ade80", "#f0fdf4", "#166534"),
            "Digunakan": ("#ef4444", "#fef2f2", "#991b1b"),
            "Dosen": ("#60a5fa", "#eff6ff", "#1e3a8a"),
            "Konflik": ("#f97316", "#fff7ed", "#9a3412")
        }
        
        self.hex_color, self.bg_light, self.text_color = colors.get(status, colors["Tersedia"])
        
        self.setStyleSheet(f"""
            QFrame#room_card {{
                background-color: white;
                border: 2px solid {'#f97316' if status == 'Konflik' else '#e2e8f0'};
                border-radius: 12px;
            }}
            QFrame#room_card:hover {{
                border-color: {self.hex_color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header (Name + Cube)
        header_layout = QHBoxLayout()
        v_header = QVBoxLayout()
        name_lbl = QLabel(room_data.get('nama', 'Unknown'))
        name_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        
        status_lbl = QLabel(status + (" Prioritas" if status == "Konflik" else " Booked" if status=="Dosen" else ""))
        status_lbl.setStyleSheet(f"color: {self.text_color}; background-color: {self.bg_light}; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;")
        
        v_header.addWidget(name_lbl)
        v_header.addWidget(status_lbl)
        v_header.addStretch()
        
        self.cube = CubeWidget(self.hex_color, should_animate=False)
        self.cube.setFixedSize(60, 60)
        
        header_layout.addLayout(v_header)
        header_layout.addWidget(self.cube)
        layout.addLayout(header_layout)
        
        # Details
        if status == "Konflik":
            det_frame = QFrame()
            det_frame.setStyleSheet("background-color: #f1f5f9; border-radius: 8px; padding: 8px;")
            det_layout = QVBoxLayout(det_frame)
            det_layout.setContentsMargins(8,8,8,8)
            det_layout.addWidget(QLabel("Mahasiswa: Rizki", styleSheet="color: #475569; font-size: 11px;"))
            det_layout.addWidget(QLabel("vs", styleSheet="color: #ef4444; font-size: 11px; font-weight: bold;"))
            det_layout.addWidget(QLabel("Dosen: Siti", styleSheet="color: #475569; font-size: 11px;"))
            layout.addWidget(det_frame)
            
            btn = QPushButton("Selesaikan Konflik")
            btn.setStyleSheet("""
                QPushButton { background-color: #f97316; color: white; border-radius: 6px; padding: 8px; font-weight: bold; border:none;}
                QPushButton:hover { background-color: #ea580c; }
            """)
            layout.addWidget(btn)
        else:
            layout.addStretch()
            lbl_kap = QLabel(f"Kapasitas: {room_data.get('kapasitas', 0)} Kursi")
            lbl_fas = QLabel(f"Fasilitas: {room_data.get('fasilitas', '-')}")
            lbl_kap.setStyleSheet("color: #64748b; font-size: 11px;")
            lbl_fas.setStyleSheet("color: #64748b; font-size: 11px;")
            lbl_fas.setWordWrap(True)
            layout.addWidget(lbl_kap)
            layout.addWidget(lbl_fas)
            layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self.room_data)
        super().mousePressEvent(event)

class AdminDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("admin_dashboard_v2")
        self.setStyleSheet("background-color: #f8fafc;")
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self._build_sidebar()
        self._build_content()
        self.refresh_data()
        
    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("""
            QFrame { background-color: #1e1b4b; color: white; }
            QPushButton { 
                text-align: left; padding: 12px 16px; border: none; 
                background: transparent; color: #cbd5e1; font-weight: 500; font-size: 13px;
                border-radius: 8px; margin: 4px 16px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); color: white; }
            QPushButton[active="true"] { background-color: #e0e7ff; color: #4338ca; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 24, 0, 24)
        
        # User Profile
        prof_layout = QHBoxLayout()
        prof_layout.setContentsMargins(16, 0, 16, 0)
        ava = QLabel("👨‍🏫")
        ava.setStyleSheet("font-size: 24px; background-color: rgba(255,255,255,0.1); border-radius: 16px; padding: 4px;")
        v_prof = QVBoxLayout()
        v_prof.addWidget(QLabel("Budi Santoso", styleSheet="color: white; font-weight: bold; font-size: 14px; background: transparent;"))
        v_prof.addWidget(QLabel("Admin / Dosen", styleSheet="color: #818cf8; font-size: 11px; background: transparent;"))
        prof_layout.addWidget(ava)
        prof_layout.addLayout(v_prof)
        prof_layout.addStretch()
        layout.addLayout(prof_layout)
        
        layout.addSpacing(24)
        
        btn_new = QPushButton("+ Reservasi Baru")
        btn_new.setStyleSheet("background-color: #4f46e5; color: white; font-weight: bold; text-align: center;")
        layout.addWidget(btn_new)
        
        btn_ai = QPushButton("🤖 Tanya Asisten AI")
        btn_ai.setStyleSheet("background-color: #0ea5e9; color: white; font-weight: bold; text-align: center;")
        btn_ai.clicked.connect(self.show_chatbot)
        layout.addWidget(btn_ai)
        
        layout.addSpacing(16)
        
        # Nav
        self.btn_dash = QPushButton("Dashboard")
        self.btn_dash.setProperty("active", "true")
        layout.addWidget(self.btn_dash)
        
        layout.addWidget(QPushButton("Jadwal Ruangan"))
        layout.addWidget(QPushButton("Peminjaman Saya"))
        layout.addWidget(QPushButton("Riwayat"))
        layout.addWidget(QPushButton("Pengaturan"))
        
        layout.addStretch()
        
        btn_out = QPushButton("Keluar")
        btn_out.clicked.connect(self.handle_logout)
        layout.addWidget(btn_out)
        
        self.main_layout.addWidget(self.sidebar)
        
    def _build_content(self):
        self.content = QFrame()
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)
        
        # Top Header
        top_bar = QHBoxLayout()
        title = QLabel("ReservasiKampus")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #334155;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("🕒 13:45", styleSheet="color: #64748b; font-weight: bold;"))
        top_bar.addWidget(QLabel("🔔", styleSheet="font-size: 16px;"))
        top_bar.addWidget(QLabel("👤", styleSheet="font-size: 16px;"))
        layout.addLayout(top_bar)
        
        # KPI Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)
        self.lbl_tot_ruangan = self._make_kpi(kpi_layout, "Total Ruangan", "0", "🏢")
        self.lbl_res_aktif = self._make_kpi(kpi_layout, "Reservasi Aktif", "0", "📅")
        self.lbl_konflik = self._make_kpi(kpi_layout, "Konflik Menunggu", "0", "⚠️", color="#f97316")
        self.lbl_tot_pengguna = self._make_kpi(kpi_layout, "Total Pengguna", "0", "👥")
        layout.addLayout(kpi_layout)
        
        # Warning Banner
        self.warning_banner = QFrame()
        self.warning_banner.setStyleSheet("background-color: #fff7ed; border-radius: 8px; padding: 12px;")
        warn_layout = QHBoxLayout(self.warning_banner)
        self.lbl_warn_text = QLabel("! 0 konflik prioritas membutuhkan perhatian Anda")
        self.lbl_warn_text.setStyleSheet("color: #ea580c; font-weight: bold;")
        btn_warn = QPushButton("Lihat Konflik")
        btn_warn.setStyleSheet("background-color: #f97316; color: white; font-weight: bold; border-radius: 6px; padding: 6px 16px; border:none;")
        warn_layout.addWidget(self.lbl_warn_text)
        warn_layout.addStretch()
        warn_layout.addWidget(btn_warn)
        layout.addWidget(self.warning_banner)
        self.warning_banner.hide()
        
        # Main area (Rooms List + Detail Panel)
        main_area = QHBoxLayout()
        
        # Rooms List
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0,0,0,0)
        
        list_header = QHBoxLayout()
        lbl_status = QLabel("Status Ruangan Hari Ini")
        lbl_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        search = QLineEdit()
        search.setPlaceholderText("Cari ruangan...")
        search.setFixedWidth(200)
        search.setStyleSheet("background-color: white; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px; color:#1e293b;")
        
        list_header.addWidget(lbl_status)
        list_header.addWidget(search)
        list_header.addStretch()
        
        # Legend
        list_header.addWidget(QLabel("🟢 Tersedia  🔴 Digunakan  🔵 Dosen  🟠 Konflik", styleSheet="font-size: 11px; color: #64748b;"))
        list_layout.addLayout(list_header)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        
        self.flow_container = QWidget()
        self.flow_container.setStyleSheet("background-color: transparent;")
        self.flow_layout = FlowLayout(self.flow_container)
        self.scroll_area.setWidget(self.flow_container)
        list_layout.addWidget(self.scroll_area)
        
        main_area.addWidget(list_container, stretch=3)
        
        # Detail Panel
        self.detail_panel = QFrame()
        self.detail_panel.setFixedWidth(300)
        self.detail_panel.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        self.detail_layout = QVBoxLayout(self.detail_panel)
        self.detail_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_det_title = QLabel("Detail Ruangan")
        self.lbl_det_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b; background:transparent;")
        self.detail_layout.addWidget(self.lbl_det_title)
        
        self.cube_container = QHBoxLayout()
        self.detail_layout.addLayout(self.cube_container)
        
        self.lbl_det_name = QLabel("-")
        self.lbl_det_name.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e293b; background:transparent;")
        self.lbl_det_name.setAlignment(Qt.AlignCenter)
        self.detail_layout.addWidget(self.lbl_det_name)
        
        self.lbl_det_status = QLabel("-")
        self.lbl_det_status.setStyleSheet("color: white; background-color: #94a3b8; padding: 6px 12px; border-radius: 12px; font-weight: bold;")
        self.lbl_det_status.setAlignment(Qt.AlignCenter)
        self.detail_layout.addWidget(self.lbl_det_status, alignment=Qt.AlignCenter)
        
        self.detail_layout.addSpacing(20)
        
        info_box = QFrame()
        info_box.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; background:transparent;")
        v_info = QVBoxLayout(info_box)
        v_info.addWidget(QLabel("Penghuni Saat Ini", styleSheet="color: #64748b; font-size: 11px; background:transparent;"))
        self.lbl_det_user = QLabel("-")
        self.lbl_det_user.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 13px; background:transparent;")
        v_info.addWidget(self.lbl_det_user)
        self.detail_layout.addWidget(info_box)
        
        self.detail_layout.addStretch()
        
        main_area.addWidget(self.detail_panel)
        
        layout.addLayout(main_area)
        self.main_layout.addWidget(self.content)

    def _make_kpi(self, layout, title, val, icon, color="#1e293b"):
        card = QFrame()
        card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        card.setFixedHeight(90)
        v = QVBoxLayout(card)
        
        h = QHBoxLayout()
        h.addWidget(QLabel(title, styleSheet="color: #64748b; font-size: 12px; font-weight: 500; background:transparent;"))
        h.addStretch()
        h.addWidget(QLabel(icon, styleSheet="background:transparent;"))
        v.addLayout(h)
        
        lbl_val = QLabel(val)
        lbl_val.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color}; background:transparent;")
        v.addWidget(lbl_val)
        
        layout.addWidget(card)
        return lbl_val
        
    def refresh_data(self):
        # Clear flow
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        try:
            supabase = get_supabase_client()
            rooms = supabase.table('ruangan').select() or []
            users = supabase.table('pengguna').select() or []
            
            konflik_count = 0
            
            # Simulasi konflik
            if len(rooms) > 0 and len(rooms) >= 3:
                rooms[0]['status'] = "Konflik"
                rooms[0]['nama'] = "LAB-AI-01"
            
            for room in rooms:
                card = RoomCard(room)
                card.clicked.connect(self.show_room_detail)
                self.flow_layout.addWidget(card)
                
                if room.get('status') == "Konflik":
                    konflik_count += 1
                    
            self.lbl_tot_ruangan.setText(str(len(rooms)))
            self.lbl_tot_pengguna.setText(str(len(users)))
            
            # Simulasi active res
            self.lbl_res_aktif.setText("87")
            
            if konflik_count > 0:
                self.warning_banner.show()
                self.lbl_warn_text.setText(f"! {konflik_count} konflik prioritas membutuhkan perhatian Anda")
                self.lbl_konflik.setText(str(konflik_count))
            else:
                self.warning_banner.hide()
                self.lbl_konflik.setText("0")
                
            if rooms:
                self.show_room_detail(rooms[0])
                
        except Exception as e:
            print("Error loading dashboard data:", e)

    def show_room_detail(self, data):
        self.lbl_det_name.setText(data.get('nama', 'Unknown'))
        
        status = data.get('status', 'Tersedia')
        if status in ("Digunakan", "Terpakai"): status = "Digunakan"
        elif status in ("Dosen", "Terbooking"): status = "Dosen"
        elif status == "Konflik": status = "Konflik"
        else: status = "Tersedia"
        
        colors = {
            "Tersedia": ("#4ade80", "#166534", "rgba(74, 222, 128, 0.2)"),
            "Digunakan": ("#ef4444", "#991b1b", "rgba(239, 68, 68, 0.2)"),
            "Dosen": ("#60a5fa", "#1e3a8a", "rgba(96, 165, 250, 0.2)"),
            "Konflik": ("#f97316", "#9a3412", "rgba(249, 115, 22, 0.2)")
        }
        
        hex_color, text_color, bg_color = colors.get(status, colors["Tersedia"])
        
        self.lbl_det_status.setText(status)
        self.lbl_det_status.setStyleSheet(f"color: {text_color}; background-color: {bg_color}; padding: 6px 12px; border-radius: 12px; font-weight: bold;")
        
        # Dummy data untuk User saat ini (bisa dimapping kalau ada)
        self.lbl_det_user.setText("Ahmad Gunawan\nKegiatan Mahasiswa (HIMA)" if status != "Tersedia" else "-")
        
        # Update cube
        for i in reversed(range(self.cube_container.count())): 
            self.cube_container.itemAt(i).widget().deleteLater()
        
        big_cube = CubeWidget(hex_color, should_animate=True)
        big_cube.setFixedSize(140, 140)
        self.cube_container.addWidget(big_cube, alignment=Qt.AlignCenter)
        
    def show_chatbot(self):
        if not hasattr(self, 'chatbot_dialog') or self.chatbot_dialog is None:
            self.chatbot_dialog = ChatbotDialog(self)
        self.chatbot_dialog.show()
        self.chatbot_dialog.raise_()
        self.chatbot_dialog.activateWindow()
        
    def handle_logout(self):
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'switch_to_public'):
            parent_widget.switch_to_public()
