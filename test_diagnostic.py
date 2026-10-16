import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from datetime import datetime
from dotenv import load_dotenv

from core.client import EkinerjaClient
from core.holidays import HolidayChecker
from core.state_manager import StateManager
from core.notifier import Notifier

def run_diagnostic():
    print("==================================================")
    print("      DIAGNOSTIK SISTEM BOT ABSENSI E-KINERJA      ")
    print("==================================================")

    # 1. Environment & Config
    base_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(base_dir, ".env"))

    email = os.getenv("EKINERJA_EMAIL", "")
    password = os.getenv("EKINERJA_PASSWORD", "")
    lat = os.getenv("LATITUDE", "")
    lng = os.getenv("LONGITUDE", "")

    print(f"\n[1] Pengecekan Konfigurasi .env:")
    print(f"  • Email       : {email if email else '❌ BELUM DIISI'}")
    print(f"  • Password    : {'❌ MASIH DEFAULT / BELUM DIISI' if (not password or password == 'ganti_dengan_password_anda') else '✔ Terkonfigurasi'}")
    print(f"  • Koordinat   : Lat={lat}, Lng={lng}")

    # 2. Kalender & Hari Libur
    print(f"\n[2] Pengecekan Kalender & Tanggal Merah:")
    checker = HolidayChecker()
    checker.fetch_holidays()
    now = datetime.now()
    is_off, reason = checker.is_holiday_or_weekend(now.date())
    print(f"  • Tanggal hari ini : {now.strftime('%A, %d %B %Y')}")
    print(f"  • Status hari ini  : {'LIBUR (' + reason + ')' if is_off else 'HARI KERJA'}")
    print(f"  • Total libur di database cache: {len(checker.holidays)}")

    # 3. State Manager
    print(f"\n[3] Pengecekan State Manager:")
    sm = StateManager(work_duration_hours=9.0)
    print(f"  • Tanggal State    : {sm.current_state.get('date')}")
    print(f"  • Check-in Status  : {sm.current_state.get('checkin_status')}")
    print(f"  • Checkout Status  : {sm.current_state.get('checkout_status')}")

    # 4. Tes Koneksi Web E-Kinerja
    print(f"\n[4] Pengecekan Koneksi ke E-Kinerja:")
    client = EkinerjaClient(email, password)
    ok, page_data, msg = client.refresh_page("/login")
    if ok:
        print(f"  • Status Server    : ✔ ONLINE (Terkoneksi)")
        print(f"  • CSRF Token       : ✔ {client.csrf_token[:15]}...")
        print(f"  • Inertia Version  : ✔ {client.inertia_version}")
    else:
        print(f"  • Status Server    : ❌ GAGAL ({msg})")

    # 5. Tes Notifikasi
    print(f"\n[5] Pengecekan Notifikasi Desktop:")
    notifier = Notifier(enable_desktop_toast=True)
    notifier.send("Tes Diagnostik", "Notifikasi desktop bot absensi berfungsi normal!", level="SUCCESS")
    print(f"  • Pop-up desktop Windows telah dikirim!")

    print("\n==================================================")
    print("Diagnostik selesai!")
    print("==================================================")

if __name__ == "__main__":
    run_diagnostic()
