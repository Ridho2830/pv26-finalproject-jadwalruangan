# ui/mahasiswa/peminjaman/dialog_update_reservasi.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QDialog,
	QWidget,
	QLabel,
	QVBoxLayout,
	QHBoxLayout,
	QFrame,
	QPushButton,
	QComboBox,
	QTextEdit,
	QMessageBox,
	QDateEdit,
	QTimeEdit,
)

from PySide6.QtGui import QFont
from PySide6.QtCore import QDate, QTime

from api.supabase import get_supabase_client


class DialogUpdateReservasi(QDialog):
	def __init__(
		self,
		reservasi_data: dict,
		pengguna_id: int,
		parent=None
	):
		super().__init__(parent)

		self.reservasi_data = reservasi_data
		self.pengguna_id = pengguna_id

		self.supabase = get_supabase_client()

		self.setWindowTitle("Update Reservasi")
		self.resize(720, 560)
		self.setModal(True)

		self.build_ui()
		self.load_styles()

	# ==========================================================
	# UI
	# ==========================================================

	def build_ui(self):
		root = QVBoxLayout(self)
		root.setContentsMargins(24, 24, 24, 24)
		root.setSpacing(18)

		# ======================================================
		# HEADER
		# ======================================================

		title = QLabel("Update Reservasi")
		title.setObjectName("dialog_title")

		subtitle = QLabel(
			"Ubah jadwal dan keperluan penggunaan ruangan."
		)
		subtitle.setObjectName("dialog_subtitle")

		root.addWidget(title)
		root.addWidget(subtitle)

		# ======================================================
		# WARNING
		# ======================================================

		warning = QFrame()
		warning.setObjectName("warning_card")

		warning_layout = QHBoxLayout(warning)
		warning_layout.setContentsMargins(14, 12, 14, 12)

		warning_text = QLabel(
			"Perubahan reservasi akan menunggu persetujuan ulang admin."
		)

		warning_text.setObjectName("warning_text")

		warning_layout.addWidget(warning_text)

		root.addWidget(warning)

		# ======================================================
		# PILIH RUANGAN
		# ======================================================

		room_card = QFrame()
		room_card.setObjectName("section_card")

		room_layout = QVBoxLayout(room_card)

		room_title = QLabel("1. Pilih Ruangan")
		room_title.setObjectName("section_title")

		self.room_combo = QComboBox()

		current_room = (
			self.reservasi_data.get("ruangan") or {}
		).get("nama", "-")

		self.room_combo.addItem(current_room)

		room_layout.addWidget(room_title)
		room_layout.addWidget(self.room_combo)

		root.addWidget(room_card)

		# ======================================================
		# WAKTU
		# ======================================================

		time_card = QFrame()
		time_card.setObjectName("section_card")

		time_layout = QVBoxLayout(time_card)

		time_title = QLabel("2. Pilih Waktu")
		time_title.setObjectName("section_title")

		row = QHBoxLayout()

		self.date_edit = QDateEdit()
		self.date_edit.setCalendarPopup(True)

		tanggal = self.reservasi_data.get("tanggal")

		if tanggal:
			y, m, d = map(int, tanggal.split("-"))
			self.date_edit.setDate(QDate(y, m, d))

		self.start_time = QTimeEdit()

		mulai = self.reservasi_data.get("jam_mulai", "08:00")
		jam1, menit1 = map(int, mulai.split(":")[:2])

		self.start_time.setTime(QTime(jam1, menit1))

		self.end_time = QTimeEdit()

		selesai = self.reservasi_data.get("jam_selesai", "10:00")
		jam2, menit2 = map(int, selesai.split(":")[:2])

		self.end_time.setTime(QTime(jam2, menit2))

		row.addWidget(self.date_edit)
		row.addWidget(self.start_time)
		row.addWidget(self.end_time)

		time_layout.addWidget(time_title)
		time_layout.addLayout(row)

		root.addWidget(time_card)

		# ======================================================
		# KEPERLUAN
		# ======================================================

		purpose_card = QFrame()
		purpose_card.setObjectName("section_card")

		purpose_layout = QVBoxLayout(purpose_card)

		purpose_title = QLabel("3. Keperluan")
		purpose_title.setObjectName("section_title")

		self.keperluan_input = QTextEdit()

		self.keperluan_input.setPlaceholderText(
			"Tuliskan tujuan penggunaan ruangan..."
		)

		self.keperluan_input.setText(
			self.reservasi_data.get("keperluan", "")
		)

		purpose_layout.addWidget(purpose_title)
		purpose_layout.addWidget(self.keperluan_input)

		root.addWidget(purpose_card)

		# ======================================================
		# BUTTON
		# ======================================================

		btn_row = QHBoxLayout()

		btn_row.addStretch()

		cancel_btn = QPushButton("Batal")
		cancel_btn.setObjectName("btn_cancel")
		cancel_btn.clicked.connect(self.reject)

		save_btn = QPushButton("Simpan Perubahan")
		save_btn.setObjectName("btn_save")
		save_btn.clicked.connect(self.update_reservasi)

		btn_row.addWidget(cancel_btn)
		btn_row.addWidget(save_btn)

		root.addLayout(btn_row)

	# ==========================================================
	# UPDATE RESERVASI
	# ==========================================================

	def update_reservasi(self):
		tanggal = self.date_edit.date().toString("yyyy-MM-dd")

		jam_mulai = (
			self.start_time
			.time()
			.toString("HH:mm")
		)

		jam_selesai = (
			self.end_time
			.time()
			.toString("HH:mm")
		)

		keperluan = (
			self.keperluan_input
			.toPlainText()
			.strip()
		)

		if not keperluan:
			QMessageBox.warning(
				self,
				"Validasi",
				"Keperluan wajib diisi."
			)
			return

		try:
			reservasi_id = self.reservasi_data.get("id")

			(
				self.supabase
				.table("reservasi")
				.update({
					"tanggal": tanggal,
					"jam_mulai": jam_mulai,
					"jam_selesai": jam_selesai,
					"keperluan": keperluan,
					"status": "Pending"
				})
				.eq("id", reservasi_id)
				.execute()
			)

			QMessageBox.information(
				self,
				"Berhasil",
				"Reservasi berhasil diperbarui."
			)

			self.accept()

		except Exception as e:
			QMessageBox.critical(
				self,
				"Error",
				str(e)
			)

	# ==========================================================
	# STYLE
	# ==========================================================

	def load_styles(self):
		self.setStyleSheet("""
			QDialog {
				background: #f7f7fb;
				font-family: 'DM Sans';
				color: #1f2937;
			}

			#dialog_title {
				font-size: 28px;
				font-weight: 700;
				color: #111827;
			}

			#dialog_subtitle {
				font-size: 14px;
				color: #6b7280;
				margin-bottom: 8px;
			}

			#warning_card {
				background: #fff7ed;
				border: 1px solid #fdba74;
				border-radius: 12px;
			}

			#warning_text {
				color: #c2410c;
				font-size: 13px;
				font-weight: 600;
			}

			#section_card {
				background: white;
				border: 1px solid #ece6ee;
				border-radius: 16px;
				padding: 8px;
			}

			#section_title {
				font-size: 16px;
				font-weight: 700;
				margin-bottom: 10px;
			}

			QComboBox,
			QDateEdit,
			QTimeEdit,
			QTextEdit {
				border: 1px solid #d1d5db;
				border-radius: 10px;
				padding: 10px;
				background: white;
				font-size: 13px;
			}

			QTextEdit {
				min-height: 100px;
			}

			#btn_cancel {
				background: white;
				border: 1px solid #d1d5db;
				border-radius: 10px;
				padding: 10px 18px;
				font-weight: 700;
			}

			#btn_cancel:hover {
				background: #f3f4f6;
			}

			#btn_save {
				background: #f97316;
				color: white;
				border: none;
				border-radius: 10px;
				padding: 10px 18px;
				font-weight: 700;
			}

			#btn_save:hover {
				background: #ea580c;
			}
		""")