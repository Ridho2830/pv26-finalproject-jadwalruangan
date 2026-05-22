from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                                QTableWidget, QTableWidgetItem, 
                                QHeaderView, QFrame)
from PySide6.QtGui import QColor
from utils.mode import theme_manager
from api.supabase import get_supabase_client


class AktivitasTerbaruWidget(QWidget):
    """Widget untuk menampilkan tabel 5 reservasi terbaru dari database."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        recent_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #6b5e8a; background-color: transparent;")
        recent_layout.addWidget(recent_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Nama Pemohon", "Ruangan", "Tanggal", "Durasi Waktu", "Status"
        ])
        
        # Styling table
        self.table.setFixedHeight(200)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Transparent background and item styling to blend with the card
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
            }
            QTableWidget::item {
                border-bottom: 1px solid rgba(147, 90, 255, 0.08);
                padding: 6px;
            }
        """)
        
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
                item_user = QTableWidgetItem(user_name)
                item_user.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                item_room = QTableWidgetItem(room_name)
                item_room.setTextAlignment(Qt.AlignCenter)
                
                item_date = QTableWidgetItem(tanggal)
                item_date.setTextAlignment(Qt.AlignCenter)
                
                item_time = QTableWidgetItem(durasi)
                item_time.setTextAlignment(Qt.AlignCenter)
                
                item_status = QTableWidgetItem(status_val)
                item_status.setTextAlignment(Qt.AlignCenter)
                
                # Color status
                if status_val == "Disetujui":
                    item_status.setForeground(QColor("#10B981"))
                elif status_val == "Pending":
                    item_status.setForeground(QColor("#F59E0B"))
                else:
                    item_status.setForeground(QColor("#EF4444"))
                    
                self.table.setItem(row_idx, 0, item_user)
                self.table.setItem(row_idx, 1, item_room)
                self.table.setItem(row_idx, 2, item_date)
                self.table.setItem(row_idx, 3, item_time)
                self.table.setItem(row_idx, 4, item_status)
                
        except Exception as e:
            print(f"Error loading aktivitas terbaru: {e}")
