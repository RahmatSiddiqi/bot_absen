# 🤖 Bot Absensi Otomatis E-Kinerja (24/7)

Bot otomatisasi absensi check-in dan check-out untuk portal **E-Kinerja** ([https://ekinerja.paperlesshospital.id](https://ekinerja.paperlesshospital.id)) yang dirancang khusus untuk berjalan di komputer yang selalu hidup (*always-on PC*).

---

## 🌟 Fitur Utama

1. **Jadwal Absen Otomatis (Senin – Jumat)**:
   - **Check-in**: Dijadwalkan otomatis mulai jam **08:00 WIB**.
   - **Check-out Fleksibel (9 Jam Kerja)**: Dihitung secara dinamis dari waktu sukses check-in.
     - Contoh: Jika check-in jam **08:00**, maka check-out jam **17:00**.
     - Contoh: Jika ada kendala internet dan baru sukses check-in jam **08:20**, maka checkout otomatis dijadwalkan pada jam **17:20**.
2. **Auto-Retry Cerdas saat Error / Internet Putus**:
   - Jika saat jam 08:00 internet mati atau web error, bot tidak akan menyerah.
   - Bot akan terus mencoba ulang setiap **60 detik** (bisa disesuaikan) sampai berhasil check-in.
   - Setelah sukses, jam check-out langsung disesuaikan secara presisi (+9 jam).
3. **Deteksi Tanggal Merah & Libur Nasional**:
   - Otomatis melewati (skip) hari **Sabtu & Minggu**.
   - Otomatis mengecek daftar **Hari Libur Nasional / Tanggal Merah Indonesia** via API & cache lokal offline (`holidays_cache.json`).
   - Mendukung daftar cuti bersama / libur kustom di `config.json`.
4. **Tahan Restart / Crash (State Persistence)**:
   - Status absensi harian disimpan di `attendance_state.json`.
   - Jika komputer restart atau mati lampu, saat bot menyala kembali ia akan mengingat jam check-in tadi pagi dan tetap mengeksekusi check-out di jam yang tepat.
   - Otomatis melakukan sinkronisasi dengan status di server E-Kinerja jika Anda sempat absen manual lewat HP.
5. **Notifikasi Lengkap**:
   - **Pop-up Windows Desktop Notification** (Native Windows Toast).
   - **Telegram Bot** (opsional).
   - **Discord Webhook** (opsional).
6. **Bisa Berjalan di Background (Auto-Start)**:
   - Disediakan script `install_autostart.bat` agar bot langsung aktif di latar belakang tanpa jendela hitam (*silent background*) saat Windows dinyalakan.

---

## 📁 Struktur Folder

```text
bot_absen/
├── .env                     <- Tempat isi password & email akun E-Kinerja
├── .env.example             <- Template contoh konfigurasi
├── config.json              <- Pengaturan umum (durasi kerja, jam target, koordinat)
├── requirements.txt         <- Dependensi Python (requests, python-dotenv, colorama)
│
├── core/
│   ├── client.py            <- HTTP Client Inertia.js untuk E-Kinerja (Login, Check-in, Check-out)
│   ├── holidays.py          <- Modul pengecekan tanggal merah & libur nasional
│   ├── state_manager.py     <- Penyimpan status absensi harian & kalkulator jam kerja
│   ├── notifier.py          <- Pengirim notifikasi (Desktop Toast, Telegram, Discord)
│   └── scheduler.py         <- Mesin penjadwal utama 24/7 & sistem auto-retry
│
├── main.py                  <- Program utama bot
├── test_diagnostic.py       <- Alat tes diagnostik koneksi, kalender & konfigurasi
│
├── start_bot.bat            <- Jalankan bot dengan jendela console (1-Klik)
├── run_hidden.vbs           <- Jalankan bot tanpa jendela CMD (tersembunyi)
├── install_autostart.bat    <- Pasang bot agar otomatis hidup saat PC dinyalakan
└── uninstall_autostart.bat  <- Hapus bot dari startup Windows
```

---

## 🚀 Panduan Penggunaan

### Langkah 1: Masukkan Password Akun Anda
1. Buka file [`.env`](file:///c:/Users/Rahmat%20Siddiqi/Desktop/bot_absen/.env) menggunakan Text Editor (Notepad / VS Code).
2. Temukan baris:
   ```env
   EKINERJA_EMAIL=email_anda@example.com
   EKINERJA_PASSWORD=ganti_dengan_password_anda
   ```
3. Ganti `ganti_dengan_password_anda` dengan password asli akun E-Kinerja Anda, lalu simpan file (`Ctrl + S`).

---

### Langkah 2: Tes Diagnostik & Verifikasi Akun
Buka terminal / Command Prompt di folder ini, lalu jalankan:
```bash
python test_diagnostic.py
```
Periksa apakah status server dan konfigurasi sudah bertanda centang hijau.

Untuk mengetes apakah email dan password Anda bisa login ke E-Kinerja:
```bash
python main.py --test-login
```
Jika berhasil, terminal akan menampilkan nama dan status absensi Anda hari ini.

---

### Langkah 3: Menjalankan Bot

Pilih salah satu metode berikut sesuai preferensi Anda:

#### Opsi A: Jalankan Langsung (Dengan Jendela Console)
- Cukup klik ganda (double-click) file [`start_bot.bat`](file:///c:/Users/Rahmat%20Siddiqi/Desktop/bot_absen/start_bot.bat).
- Jendela hitam akan menampilkan status jam komputer, jadwal check-in, dan proses kerja bot secara langsung.

#### Opsi B: Pasang Otomatis Saat Komputer Dinyalakan (Rekomendasi untuk PC Selalu Hidup)
- Klik ganda file [`install_autostart.bat`](file:///c:/Users/Rahmat%20Siddiqi/Desktop/bot_absen/install_autostart.bat).
- Bot akan didaftarkan ke folder Startup Windows. Setiap kali komputer dihidupkan atau pengguna login, bot akan otomatis berjalan di latar belakang secara hening (*silent background* via `run_hidden.vbs`).
- Setiap ada aktivitas Check-in atau Check-out, Anda akan menerima notifikasi pop-up Windows di sudut kanan bawah layar.

---

## ⚙️ Perintah Tambahan (CLI)

| Perintah | Fungsi |
|---|---|
| `python main.py` | Menjalankan bot normal (looping 24/7) |
| `python main.py --status` | Melihat status absensi hari ini & tanggal merah |
| `python main.py --test-login` | Tes login dan cek status absensi di server E-Kinerja |
| `python main.py --checkin-now` | Memaksa Check-in langsung saat ini juga (Manual Trigger) |
| `python main.py --checkout-now` | Memaksa Check-out langsung saat ini juga (Manual Trigger) |

---

## 🔔 Notifikasi Telegram (Opsional)
Jika Anda ingin mendapat notifikasi absensi ke HP melalui Telegram:
1. Buat bot di `@BotFather` di Telegram untuk mendapatkan **Bot Token**.
2. Ambil Chat ID Anda (bisa lewat `@userinfobot`).
3. Buka file [`.env`](file:///c:/Users/Rahmat%20Siddiqi/Desktop/bot_absen/.env) dan isi:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
   TELEGRAM_CHAT_ID=123456789
   ```

---

## ❓ FAQ & Troubleshooting

- **Komputer mati lampu atau restart saat jam kerja?**
  Tidak masalah. Saat komputer hidup kembali, bot membaca file `attendance_state.json` atau server E-Kinerja, sehingga tetap tahu jam berapa tadi pagi Anda check-in dan kapan harus check-out.
- **Bagaimana jika jam 08:00 internet mati?**
  Bot akan terus mencoba ulang setiap 60 detik. Saat internet kembali menyala (misal 08:20), check-in akan langsung dicatat, dan jam check-out akan otomatis dimundurkan ke 17:20 (+9 jam).
- **Bagaimana cara menghentikan bot?**
  - Jika berjalan lewat `start_bot.bat`: Tekan `Ctrl + C` di jendela CMD.
  - Jika berjalan di background: Buka Task Manager (`Ctrl + Shift + Esc`), cari `python.exe`, lalu klik *End Task*.
  - Untuk membatalkan auto-start: Jalankan [`uninstall_autostart.bat`](file:///c:/Users/Rahmat%20Siddiqi/Desktop/bot_absen/uninstall_autostart.bat).
