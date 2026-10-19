import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Try colorama for colored terminal output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = BLUE = MAGENTA = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""

from core.client import EkinerjaClient
from core.holidays import HolidayChecker
from core.state_manager import StateManager
from core.notifier import Notifier
from core.scheduler import AttendanceScheduler
from core.crypto import load_secure_credentials

# Setup logging
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "bot.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("Main")

def print_banner():
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}=============================================================
         🤖 E-KINERJA BOT ABSENSI OTOMATIS (24/7)
=============================================================
{Fore.GREEN} Target Web      : https://ekinerja.paperlesshospital.id
 Jadwal Masuk    : 08:00 WIB (Senin - Jumat)
 Durasi Kerja    : 9 Jam (Check-in 08:20 -> Check-out 17:20)
 Fitur Khusus    : Auto-Retry saat error / offline
                   Skip Otomatis Tanggal Merah & Libur
============================================================={Style.RESET_ALL}
"""
    print(banner)

def load_settings():
    """Load configuration from .env and config.json."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(base_dir, ".env"))

    config_path = os.path.join(base_dir, "config.json")
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Gagal membaca config.json: {e}")

    # Prioritaskan kredensial terenkripsi (credentials.enc)
    enc_path = os.path.join(base_dir, "credentials.enc")
    email = ""
    password = ""
    if os.path.exists(enc_path):
        try:
            creds = load_secure_credentials(enc_path)
            email = creds.get("email", "")
            password = creds.get("password", "")
            logger.info("Berhasil memuat kredensial terenkripsi (credentials.enc)")
        except Exception as e:
            logger.error(f"Gagal membuka kredensial terenkripsi: {e}")

    # Fallback ke .env atau config.json jika belum ada credentials.enc
    if not email:
        email = os.getenv("EKINERJA_EMAIL") or config.get("email", "")
    if not password:
        password = os.getenv("EKINERJA_PASSWORD") or config.get("password", "")
    lat = float(os.getenv("LATITUDE") or config.get("latitude", 5.2447668))
    lng = float(os.getenv("LONGITUDE") or config.get("longitude", 96.9965177))

    checkin_target = os.getenv("CHECKIN_TARGET_TIME") or config.get("checkin_target_time", "08:00")
    work_duration = float(os.getenv("WORK_DURATION_HOURS") or config.get("work_duration_hours", 9.0))
    retry_interval = int(os.getenv("RETRY_INTERVAL_SECONDS") or config.get("retry_interval_seconds", 60))

    checkin_note = os.getenv("CHECKIN_NOTE") or config.get("checkin_note", "")
    checkout_note = os.getenv("CHECKOUT_NOTE") or config.get("checkout_note", "")

    enable_toast = os.getenv("ENABLE_DESKTOP_TOAST", "true").lower() in ("true", "1", "yes")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN") or None
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID") or None
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL") or None
    custom_holidays = config.get("custom_holidays", [])

    return {
        "email": email,
        "password": password,
        "latitude": lat,
        "longitude": lng,
        "checkin_target": checkin_target,
        "work_duration": work_duration,
        "retry_interval": retry_interval,
        "checkin_note": checkin_note,
        "checkout_note": checkout_note,
        "enable_toast": enable_toast,
        "telegram_token": telegram_token,
        "telegram_chat_id": telegram_chat_id,
        "discord_webhook": discord_webhook,
        "custom_holidays": custom_holidays
    }

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Bot Absensi E-Kinerja")
    parser.add_argument("--test-login", action="store_true", help="Tes koneksi dan login ke akun E-Kinerja")
    parser.add_argument("--status", action="store_true", help="Cek status absensi hari ini dan kalender libur")
    parser.add_argument("--checkin-now", action="store_true", help="Paksa Check-In langsung saat ini juga")
    parser.add_argument("--checkout-now", action="store_true", help="Paksa Check-Out langsung saat ini juga")
    args = parser.parse_args()

    settings = load_settings()

    if not settings["email"] or not settings["password"] or settings["password"] == "ganti_dengan_password_anda":
        print(f"{Fore.RED}[PERHATIAN] Password belum diatur di file .env!{Style.RESET_ALL}")
        print(f"Silakan buka file {Fore.YELLOW}.env{Style.RESET_ALL} lalu masukkan password akun E-Kinerja Anda pada baris:")
        print(f"{Fore.CYAN}EKINERJA_PASSWORD=password_asli_anda{Style.RESET_ALL}\n")
        if not args.status:
            return

    client = EkinerjaClient(
        email=settings["email"],
        password=settings["password"],
        latitude=settings["latitude"],
        longitude=settings["longitude"]
    )
    holiday_checker = HolidayChecker(custom_holidays=settings["custom_holidays"])
    state_manager = StateManager(work_duration_hours=settings["work_duration"])
    notifier = Notifier(
        telegram_token=settings["telegram_token"],
        telegram_chat_id=settings["telegram_chat_id"],
        discord_webhook=settings["discord_webhook"],
        enable_desktop_toast=settings["enable_toast"]
    )

    scheduler = AttendanceScheduler(
        client=client,
        holiday_checker=holiday_checker,
        state_manager=state_manager,
        notifier=notifier,
        checkin_target_time=settings["checkin_target"],
        work_duration_hours=settings["work_duration"],
        retry_interval_seconds=settings["retry_interval"],
        checkin_note=settings["checkin_note"],
        checkout_note=settings["checkout_note"]
    )

    # 1. Action: Test Login
    if args.test_login:
        print(f"\n{Fore.YELLOW}Mengetes login ke E-Kinerja...{Style.RESET_ALL}")
        ok, msg = client.login()
        if ok:
            print(f"{Fore.GREEN}✔ {msg}{Style.RESET_ALL}")
            print(f"  Nama Pegawai : {client.user_info.get('name')}")
            print(f"  ID Pegawai   : {client.user_info.get('employee_id')}")
            print(f"  Email        : {client.user_info.get('email')}")

            # Check attendance
            ok_att, status, att_msg = client.get_attendance_status()
            if ok_att:
                print(f"\n{Fore.CYAN}Status Absensi Saat Ini:{Style.RESET_ALL}")
                print(f"  Sudah Check-In  : {'✔ Ya' if status.get('has_logged_in') else '❌ Belum'}")
                print(f"  Waktu Check-In  : {status.get('waktu_login') or '-'}")
                print(f"  Sudah Check-Out : {'✔ Ya' if status.get('has_logged_out') else '❌ Belum'}")
                print(f"  Waktu Check-Out : {status.get('waktu_logout') or '-'}")
        else:
            print(f"{Fore.RED}✖ {msg}{Style.RESET_ALL}")
        return

    # 2. Action: Status
    if args.status:
        print(f"\n{Fore.CYAN}=== STATUS SISTEM ==={Style.RESET_ALL}")
        print(scheduler.get_status_summary())
        return

    # 3. Action: Manual Check-In
    if args.checkin_now:
        print(f"\n{Fore.YELLOW}Menjalankan Check-In Manual...{Style.RESET_ALL}")
        ok = scheduler.execute_checkin_attempt()
        if ok:
            print(f"{Fore.GREEN}✔ Check-in berhasil!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✖ Check-in gagal! Cek log di atas.{Style.RESET_ALL}")
        return

    # 4. Action: Manual Check-Out
    if args.checkout_now:
        print(f"\n{Fore.YELLOW}Menjalankan Check-Out Manual...{Style.RESET_ALL}")
        ok = scheduler.execute_checkout_attempt()
        if ok:
            print(f"{Fore.GREEN}✔ Check-out berhasil!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✖ Check-out gagal! Cek log di atas.{Style.RESET_ALL}")
        return

    # 5. Default: Start Continuous 24/7 Scheduler
    print(f"{Fore.GREEN}Memulai Bot Absensi Otomatis 24/7...{Style.RESET_ALL}")
    print(f"• Email Akun         : {settings['email']}")
    print(f"• Jadwal Check-In    : {settings['checkin_target']} WIB")
    print(f"• Durasi Jam Kerja   : {settings['work_duration']} jam (Check-out = Check-in + 9 jam)")
    print(f"• Koordinat Lokasi   : {settings['latitude']}, {settings['longitude']}")
    print(f"• Interval Retry     : {settings['retry_interval']} detik jika offline/error\n")
    print(f"{Fore.YELLOW}Tekan Ctrl + C untuk menghentikan bot.{Style.RESET_ALL}\n")

    scheduler.run_loop()

if __name__ == "__main__":
    main()
