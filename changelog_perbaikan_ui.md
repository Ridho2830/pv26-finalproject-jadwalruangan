# 🚀 Comprehensive Changelog: Pengembangan Fitur & Perombakan UI
*(Laporan Lengkap Seluruh Perbaikan Sistem)*

Dokumen ini mencatat **seluruh** perubahan, perbaikan *bug*, dan penambahan fitur baru yang dilakukan pada aplikasi **ReservasiKampus** dari awal. Semua pembaruan berfokus pada penyelesaian masalah fungsionalitas serta memberikan desain antarmuka (UI) yang jauh lebih modern, mulus (*smooth*), dan tidak kaku.

---

## 🚀 1. Optimasi Performa & Perbaikan Lag
Masalah utama yang dilaporkan di awal adalah performa aplikasi yang patah-patah (*laggy*).
* **Perbaikan *Lag* saat *Scroll***: Seluruh area yang dapat digulir (*scrollable areas*), khususnya pada halaman Dasbor Utama (Kalender Ketersediaan Ruangan), sebelumnya terasa berat saat di-*scroll*. Hal ini telah dioptimalkan secara teknis (mengaktifkan *smooth scrolling* dan perbaikan render) sehingga pengguliran layar sekarang terasa sangat mulus dan ringan.

## 🤖 2. Pembaruan Fitur Chatbot (AI Assistant)
Fitur *chatbot* sebelumnya mengalami beberapa masalah teknis dan desain yang kurang memanjakan mata.
* **Desain Chat Bubble Modern**: Tampilan pesan dirombak total menyerupai aplikasi *chatting* modern (seperti WhatsApp/Telegram). Pesan pengguna berada di sisi kanan dengan warna latar aksen (biru/ungu), sedangkan balasan sistem berada di sisi kiri dengan warna abu-abu yang elegan. Sudut *bubble* kini dibuat membulat (*rounded*).
* **Efisiensi Layout**: Merapikan *margin* dan ruang kosong sehingga *chatbot* terlihat lebih menyatu dengan keseluruhan tema aplikasi.

## 📊 2. Pembuatan Modul Statistik Admin Baru
Sebelumnya, Admin tidak memiliki halaman untuk memonitor ringkasan data reservasi. Fitur ini dibangun dari nol.
* **Integrasi Matplotlib**: Mengintegrasikan pustaka visualisasi `Matplotlib` (dengan `FigureCanvasQTAgg`) langsung ke dalam *dashboard* PySide6.
* **Bar Chart (Diagram Batang)**: Menampilkan data analitik "5 Ruangan Terpopuler" yang paling sering dipesan oleh mahasiswa/dosen secara akurat dari basis data Supabase.
* **Pie Chart (Diagram Lingkaran)**: Memvisualisasikan persentase status dari semua reservasi (Berapa persen yang Disetujui, Ditolak, Pending, atau Dibatalkan).
* **Desain Grafik Premium**: Grafik tidak dibiarkan polos; warna, sumbu (*axes*), dan latar belakang grafik dirancang agar tembus pandang (*transparent*) dan menggunakan palet warna estetik yang secara otomatis beradaptasi dengan mode gelap/terang (*Dark/Light Mode*).

## 💳 3. Perombakan Kartu Angka (KPI Cards)
Di bagian atas halaman Statistik, dibuat tiga kartu ringkasan (Total Reservasi, Disetujui, Ditolak).
* **Perbaikan *Bug* Hilang (*Garbage Collection*)**: Memperbaiki *error* sistem kritis (C++ Object Deleted) di mana kartu tiba-tiba hilang dari layar sesaat setelah dirender.
* **Efek Tiga Dimensi (3D)**: Kartu kini dilengkapi efek `QGraphicsDropShadowEffect` sehingga terlihat mengambang di atas latar belakang aplikasi.
* **Garis Aksen Bawah**: Menambahkan sentuhan desain berkelas berupa garis batas bawah berukuran 3px dengan warna dinamis (Ungu, Hijau, Merah).
* **Ikon Dekoratif Premium**: Disematkan ikon besar semi-transparan sebagai *watermark* di sudut kanan dalam kartu untuk menonjolkan kesan *Dashboard* web modern.

## 🗓️ 4. Perbaikan Pop-Up Detail Jadwal Ruangan
Jendela *pop-up* yang muncul saat tanggal di kalender diklik memiliki beberapa masalah sinkronisasi dan pewarnaan.
* **Perbaikan Sinkronisasi Data**: Memperbaiki *bug* di mana detail ruangan yang ditampilkan tidak sinkron secara akurat dengan status ketersediaan pada hari tersebut.
* **Perbaikan *Bug* Kotak Hitam**: Menghilangkan warna hitam solid yang merusak estetika di bagian teks judul (*header*) pada mode gelap dengan menerapkan `background: transparent;`.
* **Perbaikan Kebocoran CSS pada Kartu**: Memperbaiki *bug* selektor CSS (`QFrame#RoomCard`) yang sebelumnya tanpa sengaja mewarnai semua tulisan di dalamnya menjadi abu-abu.
* **Badge Ketersediaan & Timeline**: Status "Tersedia Seharian" tidak lagi sekadar teks, melainkan diubah menjadi wujud *badge/pill* berwarna hijau cerah. Riwayat jam pemakaian dan nama peminjam dirapikan dengan warna *bullet point* penanda (biru untuk dosen, merah untuk mahasiswa).

## 🗃️ 5. Perombakan UI Seluruh Tabel Pengelola Data
Halaman **Kelola Ruangan**, **Kelola Pengguna**, dan **Kelola Reservasi** dirombak secara menyeluruh untuk menghilangkan nuansa "tabel Excel kaku" khas aplikasi *desktop* lawas.
* **Container Glassmorphism**: Area daftar/tabel kini dibungkus dalam wadah dengan tepian membulat 16px dan bayangan (*shadow*) lembut yang menyatu dengan latar belakang layar.
* **Tabel Bersih Tanpa Kisi (Grid)**: *Grid lines* tabel telah dihilangkan total.
* **Penghapusan Warna Selang-Seling**: Menerapkan permintaan khusus untuk menghapus warna baris selang-seling (*alternating row colors*) demi menciptakan ruang baca yang sangat bersih, minimalis, dan konsisten. Tiap baris hanya dipisahkan oleh satu garis halus di bawahnya.
* **Penyempurnaan Tombol Aksi (Edit/Hapus)**: 
  - Ditambahkan dukungan Emoji / Ikon visual (✏️ dan 🗑️).
  - Warna abu-abu diganti dengan warna solid (Kuning/Oranye untuk *Edit*, Merah untuk *Hapus*).
  - Menambahkan animasi perubahan warna (*hover effect*) yang sangat halus saat disentuh *kursor* *mouse*.
* **Perbaikan *Bug Render* Latar Belakang Sel**: Menulis ulang logika tabel dengan menginjeksi `QTableWidgetItem` kosong di setiap sel yang menampung tombol aksi, sehingga tabel dapat melukis (*render*) warna latar baris dengan sempurna tanpa menyisakan kotak gelap di belakang tombol.

## 🛡️ 6. Peningkatan Keamanan Chatbot (RBAC)
Diterapkan sistem *Role-Based Access Control* (RBAC) atau pembatasan hak akses berbasis *role* langsung ke dalam otak Asisten AI.
* **Deteksi Role Otomatis**: Chatbot sekarang mendeteksi sesi pengguna saat *login* (Admin, Dosen, atau Mahasiswa) secara otomatis.
* **Prompt Guard (Anti-Injection)**: Asisten AI kini kebal terhadap instruksi manipulatif. Jika pengguna berstatus **Mahasiswa** atau **Dosen**, AI telah diinstruksikan dengan tegas untuk menolak segala bentuk permintaan penyetujuan reservasi palsu, pengambilan data internal sistem, atau upaya mengubah parameter aplikasi.
* **Akses Penuh Admin**: Hanya pengguna dengan *role* **Admin** yang akan dilayani secara transparan tanpa sensor untuk keperluan manajerial.

## 🧹 7. Pembersihan Kode & File Usang (Clean Up)
Membersihkan ruang kerja dari *file* dan direktori yang tidak berguna.
* **Hapus Backup**: Menghapus `utils/chatbot_backup.py` yang sudah tergantikan dengan versi terbaru.
* **Hapus Folder Typo**: Menghapus direktori salah ketik `ui/mahasisw` beserta *cache* yang berisiko membuat program bentrok.
* **Hapus Cache Lama**: Menghapus sisa *compile* dari *file* yang sudah diubah namanya (`dialog_buat_reservasi.pyc`).

---

*Laporan ini secara komprehensif mendeskripsikan transisi aplikasi dari wujud purwarupa (kaku) menjadi perangkat lunak berkualitas produksi dengan Standar Antarmuka Pengguna Modern serta Sistem Keamanan Tahan Banting.*
