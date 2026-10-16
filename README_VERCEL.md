# 🚀 Panduan Deploy Bot Absen E-Kinerja ke Vercel (JavaScript / Node.js)

Bot ini sekarang sudah dibuatkan versi **JavaScript (Node.js)** yang 100% kompatibel dengan **Vercel Serverless Functions & Cron Jobs**.

---

## 🌟 Keuntungan Deploy ke Vercel:
1. **Tidak Butuh Komputer Nyala**: Berjalan di Cloud 24/7 secara gratis.
2. **Dashboard Web dari HP**: Anda mendapatkan URL web (misal: `https://bot-absen-anda.vercel.app`) untuk memantau status atau absen 1-klik dari HP.
3. **Tanpa Install Dependency Rumit**: Menggunakan native fetch Node.js tanpa browser headless yang berat.

---

## 📋 Langkah-Langkah Deploy ke Vercel

### Metode 1: Menggunakan GitHub (Sangat Disarankan)

1. **Upload Folder Ini ke GitHub**:
   - Buat repositori baru di [GitHub](https://github.com/new) (Disarankan pilih **Private Repository** demi keamanan data kredensial).
   - Inisialisasi dan push folder ini ke GitHub:
     ```bash
     git init
     git add .
     git commit -m "Initial commit bot absen"
     git branch -M main
     git remote add origin https://github.com/USERNAME-ANDA/NAMA-REPO.git
     git push -u origin main
     ```

2. **Hubungkan ke Vercel**:
   - Buka dashboard [Vercel](https://vercel.com/) dan login.
   - Klik tombol **"Add New..."** -> **"Project"**.
   - Pilih repositori GitHub Anda tadi, lalu klik **Import**.

3. **Atur Environment Variables di Vercel**:
   Sebelum klik Deploy, buka menu **Environment Variables** di halaman pengaturan Vercel, lalu tambahkan variabel berikut:

   | Key / Nama Variabel | Value / Nilai |
   |---|---|
   | `EKINERJA_EMAIL` | `rahmatsiddiq946@gmail.com` |
   | `EKINERJA_PASSWORD` | `Rahmat2404!` |
   | `LATITUDE` | `4.919988968942603` |
   | `LONGITUDE` | `97.79774437307512` |
   | `WORK_DURATION_HOURS` | `9.0` |
   | `TELEGRAM_BOT_TOKEN` | *(Opsional)* Token Bot Telegram Anda |
   | `TELEGRAM_CHAT_ID` | *(Opsional)* Chat ID Telegram Anda |

4. **Deploy**:
   - Klik tombol **"Deploy"**.
   - Tunggu sekitar 30 detik hingga selesai. Vercel akan memberikan domain gratis seperti:
     `https://ekinerja-bot-absen.vercel.app`

---

## ⏰ Pengaturan Jadwal Otomatis (Cron)

File [`vercel.json`](file:///c:/Users/Rahmat%20Siddiqi/Desktop/bot_absen/vercel.json) sudah dikonfigurasi untuk menjalankan absensi otomatis:
- **Check-in Pagi**: Jam 08:00 WIB (01:00 UTC)
- **Check-out Sore**: Jam 17:00 WIB (10:00 UTC)

### 💡 Penanganan Jika Absen Terlambat (Contoh: Absen Jam 08:20 -> Checkout 17:20):
Vercel Hobby Plan (gratis) memiliki batasan frekuensi cron bawaan. Agar bot Anda **selalu presisi mengecek menit checkout** (misal jika check-in jam 08:20, checkout tepat jam 17:20):

Gunakan cron trigger gratis dari **[cron-job.org](https://cron-job.org/)**:
1. Buat akun gratis di [cron-job.org](https://cron-job.org/).
2. Buat Cronjob baru:
   - **Title**: `E-Kinerja Auto Checkout`
   - **URL**: `https://NAMA-PROJECT-ANDA.vercel.app/api/bot?action=checkout`
   - **Schedule**: Setiap 5 menit atau 10 menit antara jam 17:00 – 18:30 WIB (Senin – Jumat).
3. **Cara Kerja Cerdasnya**:
   - Jika bot dipanggil jam 17:00, bot mengecek: *"Oh, tadi pagi check-in jam 08:20, berarti belum saatnya checkout (+9 jam = 17:20)."* -> Bot menolak checkout sebelum waktunya.
   - Begitu cron terpanggil saat jam sudah melewati 17:20 -> Bot langsung mengeksekusi Check-Out secara sukses!

---

## 📱 Mengakses Web Dashboard
Buka domain Vercel Anda di browser HP atau PC:
- Lihat jam server real-time (WIB).
- Lihat nama pegawai & ID terverifikasi.
- Lihat apakah hari ini libur nasional / tanggal merah.
- Lihat jam check-in & hitung mundur jadwal check-out (+9 jam).
- Tersedia tombol **Check-In** dan **Check-Out** manual jika diperlukan sewaktu-waktu.
