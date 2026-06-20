# Laporan Proyek: Aplikasi Jadwal Ruangan (Komprehensif)

## 1. Informasi Umum Proyek
Aplikasi **Jadwal Ruangan** merupakan sistem terpadu berbasis *desktop* yang dirancang untuk memodernisasi proses pengelolaan dan peminjaman ruangan. Aplikasi ini mengatasi masalah bentrok jadwal, ketidakteraturan pendataan fasilitas, dan lamanya proses persetujuan administratif.

- **Platform:** Aplikasi Desktop (Windows/Linux/macOS)
- **Bahasa Pemrograman:** Python 3
- **Framework Antarmuka (GUI):** PySide6 (Qt for Python)
- **Database & Backend:** Supabase (PostgreSQL Cloud) + REST API
- **Sistem Autentikasi:** Enkripsi Hash dengan Bcrypt

---

## 2. Struktur Database (Supabase)
Sistem ini menggunakan Supabase sebagai pusat data. Secara arsitektur, sistem ini minimal mengelola tabel-tabel berikut beserta layanan penyimpanannya (Storage):

1. **Tabel `pengguna`**
   - Menyimpan data akun pengguna (Admin & Mahasiswa).
   - Kolom utama: `id`, `username`, `password` (hashed dengan bcrypt), `role` (admin/mahasiswa), `nama_lengkap`.
2. **Tabel `ruangan`**
   - Menyimpan daftar aset ruangan fisik yang tersedia.
   - Kolom utama: `id`, `nama_ruangan`, `kapasitas`, `fasilitas`, `status` (aktif/non-aktif/perbaikan).
3. **Tabel `reservasi`**
   - Menyimpan data transaksi permohonan peminjaman ruangan.
   - Kolom utama: `id`, `ruangan_id` (foreign key), `pengguna_id` (foreign key), `tanggal`, `jam_mulai`, `jam_selesai`, `keperluan`, `status` (Pending/Disetujui/Ditolak), `catatan_admin`.
4. **Supabase Storage Bucket**
   - Digunakan untuk mengunggah dokumen bukti peminjaman ruangan (misal: surat pengantar/proposal kegiatan dalam format PDF/Gambar) langsung ke *cloud*.

---

## 3. Rincian Fitur Berdasarkan Role

### A. Hak Akses: Admin
Admin adalah supervisor sistem. Mereka bertanggung jawab menjaga integritas data operasional dan menentukan disetujui atau tidaknya sebuah kegiatan.

* **Modul Dashboard (`ui/admin/dashboard.py`)**
  * Memberikan _bird's-eye view_ terkait total ruangan yang ada, jumlah mahasiswa yang terdaftar, serta antrean reservasi yang butuh persetujuan (Pending).
  * Menampilkan jadwal ruangan terisi pada hari yang sedang berjalan.

* **Modul Kelola Ruangan (`ui/admin/ruangan/kelola_ruangan.py`)**
  * Memungkinkan admin mendaftarkan ruangan baru lengkap dengan atributnya (misalnya kapasitas 50 orang, fasilitas AC & Proyektor).
  * Memperbarui status ruangan apabila sedang tidak bisa digunakan (maintenance).

* **Modul Kelola Pengguna (`ui/admin/pengguna/kelola_pengguna.py`)**
  * Admin dapat membuat akun baru bagi mahasiswa atau staf tata usaha lainnya.
  * Reset password atau mengubah peran (role) dari akun yang ada.

* **Modul Kelola Reservasi & Validasi Konflik (`ui/admin/reservasi/kelola_reservasi.py`)**
  * **Fitur Utama:** Menampilkan tabel antrean permohonan peminjaman.
  * **Conflict Handling (Pencegah Bentrok):** Saat Admin mencoba mengubah status reservasi menjadi **Disetujui**, sistem (melalui Background Worker) akan mengecek di database apakah di ruangan yang sama, pada tanggal tersebut, dan rentang *jam_mulai - jam_selesai* yang beririsan sudah ada jadwal yang disetujui. Jika ada, sistem menolak proses simpan dan memunculkan *Warning*.
  * Admin dapat memberikan `catatan_admin` (alasan penolakan).

* **Modul Statistik (`ui/admin/statistik/statistik_widget.py`)**
  * Terintegrasi dengan **Matplotlib** untuk menggambar grafik batang/garis.
  * Mengilustrasikan tren penggunaan ruangan (misalnya ruangan mana yang paling laris dipinjam bulan ini).

### B. Hak Akses: Mahasiswa (Peminjam)
Mahasiswa berinteraksi sebagai pemohon. Interface dirancang intuitif agar proses "cari ruangan -> pinjam" bisa dilakukan kurang dari 2 menit.

* **Modul Dashboard Mahasiswa (`ui/mahasiswa/dashboard.py`)**
  * Tampilan kalender interaktif. Jika sebuah tanggal diklik, akan muncul popup detail jadwal (`utils/detail_hari.py`) yang menjabarkan ruangan apa saja yang sedang terpakai pada hari itu beserta rentang waktunya.
  * **Integrasi Chatbot (`utils/chatbot.py`)**: Terdapat widget asisten AI pintar. Mahasiswa bisa bertanya seputar tata cara peminjaman atau aturan gedung. Chatbot ini berjalan asinkron memanggil HTTP Requests (API eksternal) untuk memproses teks balasan.

* **Modul Pembuatan Reservasi (`ui/mahasiswa/peminjaman/dialog_reservasi.py`)**
  * Form terpadu di mana mahasiswa memilih Ruangan, Tanggal (menggunakan _Date Picker_), Jam Mulai, dan Jam Selesai.
  * Di form ini, terdapat fitur upload dokumen (menggunakan library `uuid` untuk _naming_ file dan diunggah via REST API Supabase).
  
* **Modul Riwayat Transaksi (`ui/mahasiswa/riwayat/riwayat_peminjaman.py`)**
  * Menampilkan tabel *Read-Only* dari semua riwayat pengajuan milik akun mahasiswa tersebut.
  * Kolom status akan diwarnai berbeda (Kuning = Pending, Hijau = Disetujui, Merah = Ditolak) sehingga mahasiswa bisa memonitor persetujuan tanpa perlu bertanya ke Admin.

---

## 4. Sorotan Implementasi Teknis (Technical Detail)

1. **Komunikasi Database Non-Blocking (`utils/worker.py`)**
   Sistem dioperasikan menggunakan arsitektur GUI PySide6. Proses pemanggilan database (REST API ke Supabase) memakan waktu (I/O Bound). Untuk mencegah tampilan aplikasi macet/freeze, proyek ini mengimplementasikan kelas `Worker` yang merupakan turunan dari `QThread`. Semua perintah Insert, Update, Select Supabase dijalankan di thread terpisah, lalu hasilnya dikirim kembali ke _Main GUI Thread_ menggunakan mekanisme `Signal` & `Slot` bawaan Qt.

2. **Supabase REST Client (`api/supabase.py`)**
   Tidak memakai library Supabase standar, proyek ini membungkus panggilan REST API Supabase secara native menggunakan modul `requests`. Ini membuat arsitektur aplikasi lebih tangguh karena developer memiliki kontrol penuh terhadap HTTP Headers, preferensi response, dan format unggah _Storage_.

3. **Autentikasi Aman**
   Password tidak pernah beredar dalam bentuk *Plain Text*. Pada saat registrasi pengguna, password di-hash dengan library `bcrypt`. Pada halaman `ui/login_page.py`, sistem akan mencocokkan hash password tanpa meng-ekstrak kata sandi aslinya.

4. **Kustomisasi Tema Dinamis (Theme Manager)**
   Terdapat implementasi pergantian tema otomatis (`utils/mode.py`) dengan mengimpor stylesheet berextensi `.qss` (Light & Dark Mode) agar aplikasi mengikuti preferensi warna pengguna secara global.
