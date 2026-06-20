# Dokumentasi Library Aplikasi Jadwal Ruangan

Dokumen ini berisi penjelasan lengkap mengenai setiap library (baik eksternal maupun bawaan Python) yang digunakan di dalam proyek aplikasi Jadwal Ruangan.

## Library Eksternal (dari `requirements.txt`)

### 1. PySide6
- **Fungsi:** Merupakan antarmuka (binding) resmi Python untuk framework Qt. Library ini adalah tulang punggung dari aplikasi ini, digunakan untuk membangun seluruh antarmuka pengguna (Graphical User Interface / GUI) desktop, mengatur layout, menangani event (klik tombol, input teks), serta arsitektur _Signal & Slot_ untuk komunikasi antar komponen.
- **Lokasi Penggunaan:** Digunakan di hampir seluruh file proyek, khususnya di folder `ui/` dan `utils/`, serta `main.py`. Modul yang sering diimpor antara lain `PySide6.QtWidgets`, `PySide6.QtCore`, dan `PySide6.QtGui`.

### 2. Supabase (`supabase`)
- **Fungsi:** Merupakan *client* Python untuk layanan database dan backend-as-a-service Supabase (berbasis PostgreSQL). Digunakan untuk melakukan operasi CRUD (Create, Read, Update, Delete) ke database cloud, seperti mengambil data jadwal ruangan, menyimpan riwayat peminjaman, serta menangani sesi data secara online.
- **Lokasi Penggunaan:** 
  - `api/supabase.py` (sebagai modul utama koneksi)
  - Modul antarmuka yang membutuhkan akses data langsung, seperti:
    - `ui/mahasiswa/peminjaman/dialog_reservasi.py`
    - `ui/mahasiswa/riwayat/riwayat_peminjaman.py`
    - `ui/mahasiswa/dashboard.py`
    - Berbagai modul di dalam folder `ui/admin/`.

### 3. Matplotlib (`matplotlib`)
- **Fungsi:** Library yang populer untuk membuat visualisasi data, grafik, dan plotting. Dalam aplikasi ini digunakan untuk menampilkan statistik peminjaman, grafik penggunaan ruangan, atau laporan data lainnya ke dalam bentuk visual yang mudah dibaca oleh admin.
- **Lokasi Penggunaan:** Digunakan terutama pada modul statistik admin, seperti di `ui/admin/statistik/statistik_widget.py`.

### 4. Bcrypt (`bcrypt`)
- **Fungsi:** Library ini digunakan untuk melakukan *hashing* password secara aman. Alih-alih menyimpan password dalam bentuk teks mentah (plain text), aplikasi menggunakan algoritma bcrypt untuk memverifikasi password pengguna (admin/mahasiswa) saat melakukan proses login.
- **Lokasi Penggunaan:** 
  - `ui/login_page.py`

### 5. Requests (`requests`)
- **Fungsi:** Library HTTP client yang sangat serbaguna untuk mengirim permintaan HTTP (GET, POST, dll). Dalam aplikasi ini, `requests` digunakan untuk berkomunikasi dengan API eksternal (pihak ketiga), contohnya untuk mengirim pesan dan menerima balasan dari layanan API Chatbot.
- **Lokasi Penggunaan:**
  - `utils/chatbot.py`

---

## Library Bawaan Python (Standard Library)

### 1. `os`
- **Fungsi:** Menyediakan cara untuk menggunakan fungsionalitas yang bergantung pada sistem operasi, seperti membaca variabel lingkungan (environment variables) atau memanipulasi path direktori.
- **Lokasi Penggunaan:** `main.py`, `utils/mode.py`, `ui/login_page.py`, `ui/mahasiswa/peminjaman/dialog_reservasi.py`.

### 2. `sys`
- **Fungsi:** Menyediakan akses ke beberapa variabel dan fungsi yang berinteraksi erat dengan interpreter Python, seperti argumen baris perintah (`sys.argv`) dan fungsi keluar dari aplikasi (`sys.exit()`).
- **Lokasi Penggunaan:** `main.py`.

### 3. `datetime` (dan submodulnya: `datetime`, `date`, `time`)
- **Fungsi:** Digunakan untuk memanipulasi tanggal dan waktu. Sangat krusial dalam aplikasi penjadwalan untuk memvalidasi tanggal reservasi ruangan, mencatat waktu peminjaman, dan mengatur urutan riwayat.
- **Lokasi Penggunaan:** Tersebar luas, contohnya di `utils/chatbot.py`, `ui/mahasiswa/peminjaman/reservasi_mahasiswa.py`, dan modul pengelolaan kalender/waktu lainnya.

### 4. `uuid`
- **Fungsi:** Menghasilkan _Universally Unique Identifier_ (UUID). Biasanya digunakan untuk meng-generate nama file yang unik saat pengguna mengunggah dokumen bukti peminjaman, atau membuat ID unik untuk suatu transaksi/reservasi sebelum dikirim ke database.
- **Lokasi Penggunaan:** `ui/mahasiswa/peminjaman/dialog_reservasi.py`.

### 5. `mimetypes`
- **Fungsi:** Digunakan untuk menebak tipe media (MIME type) dari ekstensi file, berguna saat mengunggah atau mendownload file, seperti dokumen proposal atau foto identitas agar sistem tahu jenis file tersebut.
- **Lokasi Penggunaan:** `ui/mahasiswa/peminjaman/dialog_reservasi.py`.

### 6. `functools` (`partial`)
- **Fungsi:** Digunakan untuk melakukan *partial function application*. Dalam GUI PySide6, sering digunakan saat menyambungkan (connect) sinyal ke sebuah fungsi yang membutuhkan parameter tambahan tanpa mengeksekusinya secara langsung.
- **Lokasi Penggunaan:** `ui/mahasiswa/peminjaman/reservasi_mahasiswa.py` dan berbagai file UI yang melooping pembuatan tombol secara dinamis.

### 7. `traceback`
- **Fungsi:** Membantu mengekstrak, memformat, dan mencetak urutan (stack traces) dari sebuah error atau exception. Biasanya digunakan untuk keperluan *debugging*, terutama jika error terjadi pada *background process* (thread).
- **Lokasi Penggunaan:** `utils/worker.py` (biasanya untuk menangani log error dari worker thread yang berjalan asinkron).
