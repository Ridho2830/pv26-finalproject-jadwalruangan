from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                                QTableWidget, QTableWidgetItem, 
                                QHeaderView, QFrame, QHBoxLayout)
from PySide6.QtGui import QColor
from utils.mode import theme_manager
from api.supabase import get_supabase_client


class AktivitasTerbaruWidget(QWidget):
    """Widget untuk menampilkan tabel 5 reservasi terbaru dari database."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self._build_ui()
    
    def _build_ui(self):
        self.recent_card = QFrame()
        self.recent_card.setProperty("class", "dashboard_card")
        recent_layout = QVBoxLayout(self.recent_card)
        recent_layout.setContentsMargins(20, 20, 20, 20)
        recent_layout.setSpacing(12)
        
        recent_title = QLabel("📅 AKTIVITAS RESERVASI TERBARU")
        recent_title.setProperty("class", "dashboard_section_title")
        recent_layout.addWidget(recent_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Nama Pemohon", "Ruangan", "Tanggal", "Durasi Waktu", "Status"
        ])
        
        # Styling table
        self.table.setFixedHeight(240)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.table.setObjectName("aktivitas_table")
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        recent_layout.addWidget(self.table)
        self.main_layout.addWidget(self.recent_card)
    
    def refresh_data(self, reservations=None, room_map=None, user_map=None):
        """Memuat data 5 reservasi terbaru ke tabel.
        
        Args:
            reservations: List of reservation dicts. If None, fetches from DB.
            room_map: Dict mapping room id -> room dict.
            user_map: Dict mapping user id -> user dict.
        """
        self.table.setRowCount(0)
        
        try:
            # Jika data belum dipass, fetch sendiri dari database
            if reservations is None or room_map is None or user_map is None:
                supabase = get_supabase_client()
                reservations = supabase.table('reservasi').select() or []
                rooms = supabase.table('ruangan').select() or []
                users = supabase.table('pengguna').select() or []
                room_map = {r['id']: r for r in rooms}
                user_map = {u['id']: u for u in users}
            
            # Urutkan reservasi dari yang terbaru (id terbesar)
            sorted_reservations = sorted(reservations, key=lambda x: x.get('id', 0), reverse=True)[:5]
            
            for row_idx, res in enumerate(sorted_reservations):
                self.table.insertRow(row_idx)
                
                # Resolusi User Name
                u_id = res.get('pengguna_id')
                user_obj = user_map.get(u_id, {})
                user_name = user_obj.get('nama', 'Unknown User')
                
                # Resolusi Room Name
                r_id = res.get('ruangan_id')
                room_obj = room_map.get(r_id, {})
                room_name = room_obj.get('nama', 'Unknown Room')
                
                # Tanggal & Waktu
                tanggal = res.get('tanggal', '-')
                jam_mulai = res.get('jam_mulai', '00:00')
                jam_selesai = res.get('jam_selesai', '00:00')
                durasi = f"{jam_mulai[:5]} - {jam_selesai[:5]}"
                
                # Status
                status_val = res.get('status', 'Pending')
                
                # Widgets
                user_widget = QWidget()
                user_layout = QHBoxLayout(user_widget)
                user_layout.setContentsMargins(12, 0, 12, 0)
                user_lbl = QLabel(user_name)
                user_lbl.setStyleSheet("font-weight: 700; font-size: 13px; background-color: transparent;")
                user_layout.addWidget(user_lbl)
                self.table.setCellWidget(row_idx, 0, user_widget)
                
                room_widget = QWidget()
                room_layout = QHBoxLayout(room_widget)
                room_layout.setContentsMargins(12, 0, 12, 0)
                room_lbl = QLabel(room_name)
                room_lbl.setStyleSheet("font-weight: 600; font-size: 12px; color: #6b6b80; background-color: transparent;")
                room_layout.addWidget(room_lbl)
                room_layout.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row_idx, 1, room_widget)
                
                item_date = QTableWidgetItem(tanggal)
                item_date.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 2, item_date)
                
                item_time = QTableWidgetItem(durasi)
                item_time.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 3, item_time)
                
                status_widget = QWidget()
                status_layout = QHBoxLayout(status_widget)
                status_layout.setContentsMargins(12, 0, 12, 0)
                status_badge = QLabel(status_val)
                
                # Color status
                badge_class = "badge badge_available" # using available style for approved
                if status_val == "Disetujui":
                    badge_class = "badge badge_available"
                elif status_val == "Pending":
                    badge_class = "badge badge_booked"
                else:
                    badge_class = "badge badge_in_use"
                    
                status_badge.setProperty("class", badge_class)
                status_badge.setAlignment(Qt.AlignCenter)
                status_layout.addWidget(status_badge)
                status_layout.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row_idx, 4, status_widget)
                
        except Exception as e:
            print(f"Error loading aktivitas terbaru: {e}")
