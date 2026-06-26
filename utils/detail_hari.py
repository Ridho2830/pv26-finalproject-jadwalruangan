from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt


# Warna per status reservasi
STATUS_COLOR = {
    "Disetujui":  ("#22c55e", "rgba(34,197,94,0.15)"),
    "Pending":    ("#f59e0b", "rgba(245,158,11,0.15)"),
    "Ditolak":    ("#ef4444", "rgba(239,68,68,0.15)"),
    "Dibatalkan": ("#6b7280", "rgba(107,114,128,0.15)"),
    "Selesai":    ("#3b82f6", "rgba(59,130,246,0.15)"),
}

# Warna dot per role peminjam
ROLE_COLOR = {
    "dosen":     "#3b82f6",
    "mahasiswa": "#f97316",
}


class DayDetailPopup(QDialog):
    def __init__(self, date_obj, all_rooms, day_reservations, is_dark=False, parent=None):
        super().__init__(parent)
        self.date_obj = date_obj
        self.all_rooms = all_rooms
        self.day_reservations = day_reservations
        self.is_dark = is_dark

        self.setWindowTitle(f"Jadwal Ruangan - {self.date_obj.strftime('%d %B %Y')}")
        self.setMinimumSize(520, 600)
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

        # ── Header ──
        lbl_header = QLabel(f"Detail Jadwal: {nama_hari}, {self.date_obj.strftime('%d-%m-%Y')}")
        color = "#f8fafc" if self.is_dark else "#0f172a"
        lbl_header.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {color}; background: transparent;"
        )
        layout.addWidget(lbl_header)

        # ── Legenda ──
        legend_row = QHBoxLayout()
        legend_row.setSpacing(16)
        for role_label, dot_col in [("Dosen", ROLE_COLOR["dosen"]), ("Mahasiswa", ROLE_COLOR["mahasiswa"])]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {dot_col}; font-size: 11px; background: transparent;")
            lbl = QLabel(role_label)
            sub = "#94a3b8" if self.is_dark else "#64748b"
            lbl.setStyleSheet(f"font-size: 11px; color: {sub}; background: transparent;")
            legend_row.addWidget(dot)
            legend_row.addWidget(lbl)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        # Map reservasi per ruangan_id
        res_by_room = {}
        for res in self.day_reservations:
            r_id = str(res.get("ruangan_id"))
            if r_id not in res_by_room:
                res_by_room[r_id] = []
            res_by_room[r_id].append(res)

        # ── Kartu per ruangan ──
        for room in self.all_rooms:
            r_id = str(room.get("id"))
            r_name = room.get("nama", "Unknown")
            reservations = res_by_room.get(r_id, [])

            card = QFrame()
            card_bg     = "rgba(255,255,255,0.05)" if self.is_dark else "white"
            card_border = "rgba(255,255,255,0.1)"  if self.is_dark else "#e2e8f0"
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {card_bg};
                    border: 1px solid {card_border};
                    border-radius: 10px;
                }}
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(10)

            # Nama ruangan
            lbl_rname = QLabel(r_name)
            text_col = "#f1f5f9" if self.is_dark else "#1e293b"
            lbl_rname.setStyleSheet(
                f"font-size: 14px; font-weight: bold; color: {text_col}; border: none;"
            )
            card_layout.addWidget(lbl_rname)

            if not reservations:
                # ── Tersedia seharian ──
                lbl_kosong = QLabel("● TERSEDIA SEHARIAN")
                lbl_kosong.setStyleSheet("""
                    background-color: rgba(34, 197, 94, 0.15);
                    color: #22c55e;
                    border-radius: 8px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: 800;
                    border: none;
                """)
                lbl_kosong.setAlignment(Qt.AlignCenter)
                wrapper = QWidget()
                wrapper.setStyleSheet("background: transparent;")
                wh = QHBoxLayout(wrapper)
                wh.setContentsMargins(0, 0, 0, 0)
                wh.addWidget(lbl_kosong)
                wh.addStretch()
                card_layout.addWidget(wrapper)

            else:
                reservations.sort(key=lambda x: x.get("jam_mulai", "00:00"))
                for res in reservations:
                    jam       = f"{res.get('jam_mulai', '')[:5]} – {res.get('jam_selesai', '')[:5]}"
                    role      = (res.get("pengguna") or {}).get("role", "").lower()
                    peminjam  = (res.get("pengguna") or {}).get("nama", "Unknown")
                    keperluan = res.get("keperluan", "-") or "-"
                    status    = res.get("status", "Pending")

                    dot_col              = ROLE_COLOR.get(role, "#94a3b8")
                    status_fg, status_bg = STATUS_COLOR.get(status, ("#94a3b8", "rgba(100,116,139,0.15)"))
                    sub_col              = "#94a3b8" if self.is_dark else "#64748b"

                    # ── Baris reservasi ──
                    res_frame = QFrame()
                    res_frame.setStyleSheet(
                        f"background: {'rgba(255,255,255,0.03)' if self.is_dark else '#f8fafc'};"
                        f"border: 1px solid {'rgba(255,255,255,0.07)' if self.is_dark else '#e2e8f0'};"
                        f"border-radius: 8px;"
                    )
                    res_layout = QVBoxLayout(res_frame)
                    res_layout.setContentsMargins(12, 10, 12, 10)
                    res_layout.setSpacing(4)

                    # Baris atas: dot role + nama + badge status
                    top_row = QHBoxLayout()
                    top_row.setSpacing(6)

                    lbl_dot = QLabel("●")
                    lbl_dot.setStyleSheet(
                        f"color: {dot_col}; font-size: 10px; border: none; background: transparent;"
                    )

                    role_label = role.capitalize() if role else "?"
                    lbl_peminjam = QLabel(f"{peminjam} ({role_label})")
                    lbl_peminjam.setStyleSheet(
                        f"color: {text_col}; font-size: 13px; font-weight: 700; "
                        f"border: none; background: transparent;"
                    )

                    lbl_status = QLabel(f" {status} ")
                    lbl_status.setStyleSheet(
                        f"color: {status_fg}; background: {status_bg}; "
                        f"border-radius: 6px; padding: 2px 8px; "
                        f"font-size: 10px; font-weight: 800; border: none;"
                    )

                    top_row.addWidget(lbl_dot)
                    top_row.addWidget(lbl_peminjam)
                    top_row.addStretch()
                    top_row.addWidget(lbl_status)
                    res_layout.addLayout(top_row)

                    # Baris jam
                    lbl_jam = QLabel(f"🕒  {jam}")
                    lbl_jam.setStyleSheet(
                        f"color: {sub_col}; font-size: 12px; "
                        f"font-family: monospace; border: none; background: transparent;"
                    )
                    res_layout.addWidget(lbl_jam)

                    # Baris keperluan
                    lbl_keperluan = QLabel(f"📝  {keperluan}")
                    lbl_keperluan.setWordWrap(True)
                    lbl_keperluan.setStyleSheet(
                        f"color: {sub_col}; font-size: 12px; border: none; background: transparent;"
                    )
                    res_layout.addWidget(lbl_keperluan)

                    card_layout.addWidget(res_frame)

            container_layout.addWidget(card)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)