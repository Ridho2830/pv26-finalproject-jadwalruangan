# ui/mahasiswa/peminjaman/dialog_update_reservasi.py

import os
import uuid
import mimetypes

from PySide6.QtCore import Qt, QDate, QTime
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
	QFileDialog,
	QScrollArea,
	QSizePolicy,
)

from PySide6.QtGui import QFont, QPixmap

from api.supabase import get_supabase_client


# ==============================================================
# DIALOG UPDATE RESERVASI (dengan upload foto laporan)
# ==============================================================

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

		# Menyimpan path file foto yang dipilih
		self.foto_path: str | None = None

		self.setWindowTitle("Edit Reservasi")
		self.resize(720, 560)
		self.setModal(True)

		self.build_ui()
		self.load_styles()

	# ==========================================================
	# UI
	# ==========================================================

	def build_ui(self):
		# Layout utama dialog: scroll area + tombol di luar scroll
		outer = QVBoxLayout(self)
		outer.setContentsMargins(0, 0, 0, 16)
		outer.setSpacing(0)

		# Scroll area untuk semua konten
		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setFrameShape(QFrame.NoFrame)
		scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

		content_widget = QWidget()
		root = QVBoxLayout(content_widget)
		root.setContentsMargins(24, 24, 24, 8)
		root.setSpacing(14)

		scroll.setWidget(content_widget)
		outer.addWidget(scroll)

		# ======================================================
		# HEADER
		# ======================================================

		title = QLabel("✏️ Edit Reservasi")
		title.setObjectName("dialog_title")

		subtitle = QLabel(
			"Ubah jadwal, keperluan, dan unggah foto laporan penggunaan ruangan."
		)
		subtitle.setObjectName("dialog_subtitle")
		subtitle.setWordWrap(True)

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
			"⚠️  Perubahan reservasi akan menunggu persetujuan ulang admin."
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
		# UPLOAD FOTO LAPORAN (hanya di edit)
		# ======================================================

		foto_card = QFrame()
		foto_card.setObjectName("section_card")

		foto_layout = QVBoxLayout(foto_card)
		foto_layout.setSpacing(10)

		foto_title = QLabel("4. Foto Laporan (Opsional)")
		foto_title.setObjectName("section_title")

		foto_desc = QLabel(
			"Unggah foto kondisi ruangan setelah digunakan sebagai laporan."
		)
		foto_desc.setObjectName("foto_desc")
		foto_desc.setWordWrap(True)

		# Area preview foto
		self.foto_preview = QLabel()
		self.foto_preview.setObjectName("foto_preview")
		self.foto_preview.setAlignment(Qt.AlignCenter)
		self.foto_preview.setFixedHeight(120)
		self.foto_preview.setWordWrap(True)
		self.foto_preview.setSizePolicy(
			QSizePolicy.Expanding, QSizePolicy.Fixed
		)

		# Cek apakah sudah ada foto sebelumnya
		existing_foto = self.reservasi_data.get("foto_laporan")
		if existing_foto:
			self.foto_preview.setText("📷 Foto laporan sebelumnya sudah ada.\nPilih file baru untuk mengganti.")
		else:
			self.foto_preview.setText("📷 Belum ada foto.\nKlik tombol di bawah untuk memilih foto.")

		# Baris tombol pilih / hapus
		foto_btn_row = QHBoxLayout()

		self.btn_pilih_foto = QPushButton("📁 Pilih Foto")
		self.btn_pilih_foto.setObjectName("btn_foto")
		self.btn_pilih_foto.clicked.connect(self._pilih_foto)

		self.btn_hapus_foto = QPushButton("🗑 Hapus")
		self.btn_hapus_foto.setObjectName("btn_hapus_foto")
		self.btn_hapus_foto.clicked.connect(self._hapus_foto)
		self.btn_hapus_foto.setVisible(False)

		foto_btn_row.addWidget(self.btn_pilih_foto)
		foto_btn_row.addWidget(self.btn_hapus_foto)
		foto_btn_row.addStretch()

		# Label nama file
		self.foto_nama_lbl = QLabel("")
		self.foto_nama_lbl.setObjectName("foto_nama")
		self.foto_nama_lbl.setWordWrap(True)

		foto_layout.addWidget(foto_title)
		foto_layout.addWidget(foto_desc)
		foto_layout.addWidget(self.foto_preview)
		foto_layout.addLayout(foto_btn_row)
		foto_layout.addWidget(self.foto_nama_lbl)

		root.addWidget(foto_card)
		root.addStretch()

		# ======================================================
		# BUTTON (di luar scroll area)
		# ======================================================

		btn_frame = QFrame()
		btn_frame.setObjectName("btn_bar")
		btn_layout = QHBoxLayout(btn_frame)
		btn_layout.setContentsMargins(24, 8, 24, 0)

		btn_layout.addStretch()

		cancel_btn = QPushButton("Batal")
		cancel_btn.setObjectName("btn_cancel")
		cancel_btn.clicked.connect(self.reject)

		save_btn = QPushButton("💾 Simpan Perubahan")
		save_btn.setObjectName("btn_save")
		save_btn.clicked.connect(self.update_reservasi)

		btn_layout.addWidget(cancel_btn)
		btn_layout.addWidget(save_btn)

		outer.addWidget(btn_frame)

	# ==========================================================
	# PILIH FOTO
	# ==========================================================

	def _pilih_foto(self):
		file_path, _ = QFileDialog.getOpenFileName(
			self,
			"Pilih Foto Laporan",
			"",
			"Gambar (*.png *.jpg *.jpeg *.webp *.bmp)"
		)

		if not file_path:
			return

		self.foto_path = file_path
		nama_file = os.path.basename(file_path)

		# Tampilkan preview
		pixmap = QPixmap(file_path)
		if not pixmap.isNull():
			pixmap = pixmap.scaled(
				self.foto_preview.width(),
				self.foto_preview.height(),
				Qt.KeepAspectRatio,
				Qt.SmoothTransformation,
			)
			self.foto_preview.setPixmap(pixmap)
		else:
			self.foto_preview.setText("⚠️ File tidak dapat ditampilkan.")

		self.foto_nama_lbl.setText(f"📄 {nama_file}")
		self.btn_hapus_foto.setVisible(True)

	def _hapus_foto(self):
		self.foto_path = None
		self.foto_preview.setText("📷 Belum ada foto.\nKlik tombol di bawah untuk memilih foto.")
		self.foto_preview.setPixmap(QPixmap())
		self.foto_nama_lbl.setText("")
		self.btn_hapus_foto.setVisible(False)

	# ==========================================================
	# UPLOAD FOTO KE SUPABASE STORAGE
	# ==========================================================

	def _upload_foto(self) -> str | None:
		"""Upload foto ke Supabase Storage dan kembalikan URL publik-nya."""
		if not self.foto_path:
			return None

		try:
			ext = os.path.splitext(self.foto_path)[1].lower()
			filename = f"laporan/{uuid.uuid4().hex}{ext}"
			mime_type = mimetypes.guess_type(self.foto_path)[0] or "image/jpeg"

			with open(self.foto_path, "rb") as f:
				foto_bytes = f.read()

			# Upload ke bucket "reservasi-foto" (sesuaikan nama bucket di Supabase)
			result = self.supabase.storage.from_("reservasi-foto").upload(
				filename,
				foto_bytes,
				{"content-type": mime_type, "upsert": "true"}
			)

			# Ambil public URL
			public_url = self.supabase.storage.from_("reservasi-foto").get_public_url(filename)
			return public_url

		except Exception as e:
			print(f"[Upload Foto] Error: {e}")
			QMessageBox.warning(
				self,
				"Peringatan Upload",
				f"Foto gagal diunggah, reservasi tetap disimpan tanpa foto.\n\nDetail: {e}"
			)
			return None

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

		# Upload foto jika ada
		foto_url = None
		if self.foto_path:
			foto_url = self._upload_foto()

		try:
			reservasi_id = self.reservasi_data.get("id")

			payload = {
				"tanggal": tanggal,
				"jam_mulai": jam_mulai,
				"jam_selesai": jam_selesai,
				"keperluan": keperluan,
				"status": "Pending",
			}

			# Tambahkan URL foto jika berhasil diupload
			if foto_url:
				payload["foto_laporan"] = foto_url

			self.supabase.table("reservasi").update(
				payload,
				f"id=eq.{reservasi_id}"
			)

			QMessageBox.information(
				self,
				"Berhasil",
				"Reservasi berhasil diperbarui."
				+ ("\nFoto laporan berhasil diunggah." if foto_url else "")
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
				margin-bottom: 4px;
			}

			#foto_desc {
				font-size: 12px;
				color: #6b7280;
				margin-bottom: 6px;
			}

			#foto_preview {
				background: #f3f4f6;
				border: 2px dashed #d1d5db;
				border-radius: 12px;
				color: #9ca3af;
				font-size: 13px;
				padding: 8px;
			}

			#foto_nombre {
				font-size: 12px;
				color: #374151;
			}

			#btn_foto {
				background: #ede9fe;
				color: #6d28d9;
				border: 1px solid #c4b5fd;
				border-radius: 10px;
				padding: 8px 16px;
				font-weight: 700;
				font-size: 13px;
			}

			#btn_foto:hover {
				background: #ddd6fe;
			}

			#btn_hapus_foto {
				background: #fee2e2;
				color: #991b1b;
				border: 1px solid #fca5a5;
				border-radius: 10px;
				padding: 8px 16px;
				font-weight: 700;
				font-size: 13px;
			}

			#btn_hapus_foto:hover {
				background: #fecaca;
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


# ==============================================================
# DIALOG BUAT RESERVASI (tanpa upload foto)
# ==============================================================

class DialogBuatReservasi(QDialog):
	"""Dialog untuk membuat reservasi baru dari sisi mahasiswa."""

	def __init__(self, pengguna_id: int, ruangan_preselect: dict = None, parent=None):
		super().__init__(parent)

		self.pengguna_id = pengguna_id
		self.ruangan_preselect = ruangan_preselect
		self.supabase = get_supabase_client()
		self.room_list = []

		self.setWindowTitle("Buat Reservasi Baru")
		self.resize(680, 560)
		self.setModal(True)

		self._load_rooms()
		self._build_ui()
		self._load_styles()

	# ==========================================================
	# LOAD DATA
	# ==========================================================

	def _load_rooms(self):
		try:
			data = self.supabase.table("ruangan").select()
			if isinstance(data, list):
				seen = set()
				for r in data:
					nama = r.get("nama", "")
					if nama not in seen:
						seen.add(nama)
						self.room_list.append(r)
		except Exception as e:
			print(f"[DialogBuatReservasi] Error load ruangan: {e}")

	# ==========================================================
	# UI
	# ==========================================================

	def _build_ui(self):
		root = QVBoxLayout(self)
		root.setContentsMargins(24, 24, 24, 24)
		root.setSpacing(18)

		# HEADER
		title = QLabel("📅 Buat Reservasi Baru")
		title.setObjectName("dialog_title")

		subtitle = QLabel(
			"Pilih ruangan, waktu, dan keperluan untuk membuat reservasi."
		)
		subtitle.setObjectName("dialog_subtitle")

		root.addWidget(title)
		root.addWidget(subtitle)

		# INFO
		info_card = QFrame()
		info_card.setObjectName("warning_card")

		info_layout = QHBoxLayout(info_card)
		info_layout.setContentsMargins(14, 12, 14, 12)

		info_text = QLabel(
			"Reservasi akan berstatus Pending hingga disetujui oleh admin."
		)
		info_text.setObjectName("warning_text")
		info_text.setWordWrap(True)

		info_layout.addWidget(info_text)

		root.addWidget(info_card)

		# 1. PILIH RUANGAN
		room_card = QFrame()
		room_card.setObjectName("section_card")

		room_layout = QVBoxLayout(room_card)

		room_title = QLabel("1. Pilih Ruangan")
		room_title.setObjectName("section_title")

		self.room_combo = QComboBox()
		self.room_combo.setFixedHeight(40)

		preselect_idx = 0
		for i, r in enumerate(self.room_list):
			nama = r.get("nama", "Unknown")
			gedung = r.get("gedung", "-")
			lantai = r.get("lantai", "-")
			kap = r.get("kapasitas", 0)
			label = f"{nama}  —  Gedung {gedung}, Lt. {lantai} ({kap} orang)"
			self.room_combo.addItem(label, r)

			if (self.ruangan_preselect
					and r.get("id") == self.ruangan_preselect.get("id")):
				preselect_idx = i

		if self.room_list:
			self.room_combo.setCurrentIndex(preselect_idx)

		room_layout.addWidget(room_title)
		room_layout.addWidget(self.room_combo)

		root.addWidget(room_card)

		# 2. PILIH WAKTU
		time_card = QFrame()
		time_card.setObjectName("section_card")

		time_layout = QVBoxLayout(time_card)

		time_title = QLabel("2. Pilih Waktu")
		time_title.setObjectName("section_title")

		row = QHBoxLayout()

		self.date_edit = QDateEdit()
		self.date_edit.setCalendarPopup(True)
		self.date_edit.setDate(QDate.currentDate())
		self.date_edit.setMinimumDate(QDate.currentDate())

		self.start_time = QTimeEdit()
		self.start_time.setTime(QTime(8, 0))
		self.start_time.setDisplayFormat("HH:mm")

		self.end_time = QTimeEdit()
		self.end_time.setTime(QTime(10, 0))
		self.end_time.setDisplayFormat("HH:mm")

		row.addWidget(self.date_edit)
		row.addWidget(self.start_time)
		row.addWidget(self.end_time)

		time_layout.addWidget(time_title)
		time_layout.addLayout(row)

		root.addWidget(time_card)

		# 3. KEPERLUAN
		purpose_card = QFrame()
		purpose_card.setObjectName("section_card")

		purpose_layout = QVBoxLayout(purpose_card)

		purpose_title = QLabel("3. Keperluan")
		purpose_title.setObjectName("section_title")

		self.keperluan_input = QTextEdit()
		self.keperluan_input.setPlaceholderText(
			"Tuliskan tujuan penggunaan ruangan, contoh: "
			"Rapat organisasi, Kelas pengganti, dll..."
		)

		purpose_layout.addWidget(purpose_title)
		purpose_layout.addWidget(self.keperluan_input)

		root.addWidget(purpose_card)

		# BUTTONS
		btn_row = QHBoxLayout()
		btn_row.addStretch()

		cancel_btn = QPushButton("Batal")
		cancel_btn.setObjectName("btn_cancel")
		cancel_btn.clicked.connect(self.reject)

		submit_btn = QPushButton("📨 Ajukan Reservasi")
		submit_btn.setObjectName("btn_save")
		submit_btn.clicked.connect(self._submit_reservasi)

		btn_row.addWidget(cancel_btn)
		btn_row.addWidget(submit_btn)

		root.addLayout(btn_row)

	# ==========================================================
	# SUBMIT
	# ==========================================================

	def _submit_reservasi(self):
		if not self.room_list:
			QMessageBox.warning(self, "Validasi", "Tidak ada ruangan tersedia.")
			return

		selected_room = self.room_combo.currentData()
		if not selected_room:
			QMessageBox.warning(self, "Validasi", "Pilih ruangan terlebih dahulu.")
			return

		ruangan_id = selected_room.get("id")
		tanggal = self.date_edit.date().toString("yyyy-MM-dd")
		jam_mulai = self.start_time.time().toString("HH:mm")
		jam_selesai = self.end_time.time().toString("HH:mm")

		if self.start_time.time() >= self.end_time.time():
			QMessageBox.warning(
				self, "Validasi",
				"Jam selesai harus lebih besar dari jam mulai."
			)
			return

		keperluan = self.keperluan_input.toPlainText().strip()
		if not keperluan:
			QMessageBox.warning(self, "Validasi", "Keperluan wajib diisi.")
			return

		nama_ruangan = selected_room.get("nama", "Unknown")
		reply = QMessageBox.question(
			self,
			"Konfirmasi Reservasi",
			f"Ajukan reservasi ruangan {nama_ruangan}?\n\n"
			f"Tanggal: {tanggal}\n"
			f"Waktu: {jam_mulai} - {jam_selesai}\n"
			f"Keperluan: {keperluan}",
			QMessageBox.Yes | QMessageBox.No,
			QMessageBox.No,
		)

		if reply != QMessageBox.Yes:
			return

		try:
			result = self.supabase.table("reservasi").insert({
				"ruangan_id": ruangan_id,
				"pengguna_id": self.pengguna_id,
				"tanggal": tanggal,
				"jam_mulai": jam_mulai,
				"jam_selesai": jam_selesai,
				"keperluan": keperluan,
				"status": "Pending",
			})

			if result is not None:
				QMessageBox.information(
					self,
					"Berhasil",
					f"Reservasi ruangan {nama_ruangan} berhasil diajukan.\n"
					f"Status: Pending (menunggu persetujuan admin).",
				)
				self.accept()
			else:
				QMessageBox.critical(
					self, "Gagal",
					"Gagal menyimpan reservasi. Silakan coba lagi."
				)

		except Exception as e:
			QMessageBox.critical(self, "Error", f"Terjadi kesalahan:\n{e}")

	# ==========================================================
	# STYLE
	# ==========================================================

	def _load_styles(self):
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
				background: #22c55e;
				color: white;
				border: none;
				border-radius: 10px;
				padding: 10px 18px;
				font-weight: 700;
			}

			#btn_save:hover {
				background: #16a34a;
			}
		""")
