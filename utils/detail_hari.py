from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

class DayDetailPopup(QDialog):
    def __init__(self, date_obj, all_rooms, day_reservations, is_dark=False, parent=None):
        super().__init__(parent)
        self.date_obj = date_obj
        self.all_rooms = all_rooms
        self.day_reservations = day_reservations
        self.is_dark = is_dark
        
        self.setWindowTitle(f"Jadwal Ruangan - {self.date_obj.strftime('%d %B %Y')}")
        self.setMinimumSize(450, 600)
        self.setModal(True)
        
        if self.is_dark:
            self.setStyleSheet("QDialog { background-color: #0f172a; }")
        else:
            self.setStyleSheet("QDialog { background-color: #f8fafc; }")
            
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        nama_hari = hari_indo[self.date_obj.weekday()]
        
        # Header
        lbl_header = QLabel(f"Detail Jadwal: {nama_hari}, {self.date_obj.strftime('%d-%m-%Y')}")
        color = "#f8fafc" if self.is_dark else "#0f172a"
        lbl_header.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {color};")
        layout.addWidget(lbl_header)
        
        # Scroll Area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        
        # Map reservations by room_id
        res_by_room = {}
        for res in self.day_reservations:
            r_id = str(res.get("ruangan_id"))
            if r_id not in res_by_room:
                res_by_room[r_id] = []
            res_by_room[r_id].append(res)
            
        # Create cards for each room
        for room in self.all_rooms:
            r_id = str(room.get("id"))
            r_name = room.get("nama", "Unknown")
            reservations = res_by_room.get(r_id, [])
            
            card = QFrame()
            
            card_bg = "rgba(255,255,255,0.05)" if self.is_dark else "white"
            card_border = "rgba(255,255,255,0.1)" if self.is_dark else "#e2e8f0"
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {card_bg};
                    border: 1px solid {card_border};
                    border-radius: 8px;
                }}
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            card_layout.setSpacing(8)
            
            lbl_rname = QLabel(r_name)
            text_col = "#f1f5f9" if self.is_dark else "#1e293b"
            lbl_rname.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {text_col}; border: none;")
            card_layout.addWidget(lbl_rname)
            
            if not reservations:
                lbl_status = QLabel("● Tersedia Seharian")
                lbl_status.setStyleSheet("color: #22c55e; font-size: 12px; font-weight: bold; border: none;")
                card_layout.addWidget(lbl_status)
            else:
                reservations.sort(key=lambda x: x.get("jam_mulai", "00:00"))
                for res in reservations:
                    jam = f"{res.get('jam_mulai', '')[:5]} - {res.get('jam_selesai', '')[:5]}"
                    role = res.get("pengguna", {}).get("role", "").lower()
                    peminjam = res.get("pengguna", {}).get("nama", "Unknown")
                    
                    if role == "dosen":
                        status_text = "Dosen"
                        col = "#3b82f6"
                    else:
                        status_text = "Mahasiswa"
                        col = "#ef4444"
                        
                    res_row = QHBoxLayout()
                    lbl_jam = QLabel(jam)
                    lbl_jam.setStyleSheet(f"color: {text_col}; font-size: 12px; font-family: monospace; border: none;")
                    
                    lbl_dot = QLabel("●")
                    lbl_dot.setStyleSheet(f"color: {col}; font-size: 10px; border: none;")
                    
                    lbl_info = QLabel(f"{peminjam} ({status_text})")
                    lbl_info.setStyleSheet(f"color: #64748b; font-size: 12px; border: none;")
                    
                    res_row.addWidget(lbl_jam)
                    res_row.addSpacing(8)
                    res_row.addWidget(lbl_dot)
                    res_row.addWidget(lbl_info)
                    res_row.addStretch()
                    
                    card_layout.addLayout(res_row)
                    
            container_layout.addWidget(card)
            
        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

