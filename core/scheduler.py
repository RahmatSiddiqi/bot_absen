import logging
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple

from .client import EkinerjaClient
from .holidays import HolidayChecker
from .state_manager import StateManager
from .notifier import Notifier

logger = logging.getLogger("Scheduler")

class AttendanceScheduler:
    def __init__(
        self,
        client: EkinerjaClient,
        holiday_checker: HolidayChecker,
        state_manager: StateManager,
        notifier: Notifier,
        checkin_target_time: str = "08:00",
        work_duration_hours: float = 9.0,
        retry_interval_seconds: int = 60,
        checkin_note: str = "",
        checkout_note: str = ""
    ):
        self.client = client
        self.holiday_checker = holiday_checker
        self.state = state_manager
        self.notifier = notifier
        self.checkin_target_time = checkin_target_time # e.g. "08:00"
        self.work_duration_hours = work_duration_hours # 9.0 hours
        self.retry_interval_seconds = retry_interval_seconds # default 60s
        self.checkin_note = checkin_note
        self.checkout_note = checkout_note
        self.running = False
        self.last_status_display_time = 0

    def parse_time_on_date(self, time_str: str, target_date: date) -> datetime:
        """Parse HH:MM string into datetime on specific date."""
        parts = [int(p) for p in time_str.split(":")]
        return datetime(target_date.year, target_date.month, target_date.day, parts[0], parts[1], 0)

    def check_and_sync_with_server(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Query server status to see if today's attendance has already been recorded
        (e.g., from user's smartphone before the bot ran).
        """
        logger.info("Sinkronisasi status absensi hari ini dengan server E-Kinerja...")
        ok, status, msg = self.client.get_attendance_status()
        if not ok:
            logger.warning(f"Belum bisa sinkronisasi dengan server: {msg}")
            return False, {}

        # 1. If already checked in on server
        if status.get("has_logged_in") and self.state.current_state.get("checkin_status") != "SUCCESS":
            raw_waktu = status.get("waktu_login")
            checkin_dt = datetime.now()
            if raw_waktu:
                try:
                    # Clean ISO format or "YYYY-MM-DD HH:MM:SS"
                    cleaned = raw_waktu.replace("Z", "+00:00")
                    checkin_dt = datetime.fromisoformat(cleaned)
                    # convert to local time if timezone-aware
                    if checkin_dt.tzinfo is not None:
                        checkin_dt = checkin_dt.astimezone()
                        checkin_dt = checkin_dt.replace(tzinfo=None)
                except Exception:
                    checkin_dt = datetime.now()

            self.state.record_checkin_success(checkin_dt)
            sched = self.state.get_scheduled_checkout()
            sched_str = sched.strftime("%H:%M:%S") if sched else "-"
            self.notifier.send(
                "Sinkronisasi Absensi",
                f"Terdeteksi sudah Check-in pada {checkin_dt.strftime('%H:%M:%S')}. Jadwal Checkout disinkronkan ke: {sched_str}",
                level="INFO"
            )

        # 2. If already checked out on server
        if status.get("has_logged_out") and self.state.current_state.get("checkout_status") != "SUCCESS":
            raw_waktu = status.get("waktu_logout")
            checkout_dt = datetime.now()
            if raw_waktu:
                try:
                    cleaned = raw_waktu.replace("Z", "+00:00")
                    checkout_dt = datetime.fromisoformat(cleaned)
                    if checkout_dt.tzinfo is not None:
                        checkout_dt = checkout_dt.astimezone().replace(tzinfo=None)
                except Exception:
                    checkout_dt = datetime.now()
            self.state.record_checkout_success(checkout_dt)
            self.notifier.send(
                "Sinkronisasi Absensi",
                f"Terdeteksi sudah Check-out pada {checkout_dt.strftime('%H:%M:%S')}.",
                level="INFO"
            )

        return True, status

    def execute_checkin_attempt(self) -> bool:
        """
        Attempt check-in. If successful, records time and calculates dynamic checkout time.
        """
        now = datetime.now()
        logger.info(f"Mencoba melakukan CHECK-IN (Waktu saat ini: {now.strftime('%H:%M:%S')})...")
        ok, msg, details = self.client.checkin(keterangan=self.checkin_note)

        if ok:
            # Check-in success!
            actual_checkin_time = datetime.now()
            self.state.record_checkin_success(actual_checkin_time)
            sched_checkout = self.state.get_scheduled_checkout()
            checkout_str = sched_checkout.strftime("%H:%M:%S") if sched_checkout else "-"

            notif_msg = (
                f"Check-in BERHASIL dicatat pada: {actual_checkin_time.strftime('%H:%M:%S')}\n"
                f"Durasi kerja: {self.work_duration_hours} jam.\n"
                f"Jadwal Check-out otomatis hari ini: {checkout_str}"
            )
            self.notifier.send("Check-In Berhasil", notif_msg, level="SUCCESS")
            return True
        else:
            self.state.record_error("checkin", msg)
            logger.warning(f"Check-in GAGAL: {msg}. Akan dicoba ulang dalam {self.retry_interval_seconds} detik.")
            return False

    def execute_checkout_attempt(self) -> bool:
        """
        Attempt check-out. If successful, records completion.
        """
        now = datetime.now()
        logger.info(f"Mencoba melakukan CHECK-OUT (Waktu saat ini: {now.strftime('%H:%M:%S')})...")
        ok, msg, details = self.client.checkout(keterangan=self.checkout_note)

        if ok:
            # Checkout success!
            actual_checkout_time = datetime.now()
            self.state.record_checkout_success(actual_checkout_time)

            checkin_iso = self.state.current_state.get("checkin_time")
            checkin_str = datetime.fromisoformat(checkin_iso).strftime("%H:%M:%S") if checkin_iso else "-"

            notif_msg = (
                f"Check-out BERHASIL dicatat pada: {actual_checkout_time.strftime('%H:%M:%S')}\n"
                f"Check-in sebelumnya: {checkin_str}\n"
                f"Absensi hari ini selesai dengan sukses. Selamat beristirahat!"
            )
            self.notifier.send("Check-Out Berhasil", notif_msg, level="SUCCESS")
            return True
        else:
            self.state.record_error("checkout", msg)
            logger.warning(f"Check-out GAGAL: {msg}. Akan dicoba ulang dalam {self.retry_interval_seconds} detik.")
            return False

    def get_status_summary(self) -> str:
        """Get human-readable summary of current bot status."""
        now = datetime.now()
        today = now.date()
        st = self.state.current_state

        is_off, reason = self.holiday_checker.is_holiday_or_weekend(today)

        lines = [
            f"Waktu Komputer: {now.strftime('%A, %d %B %Y - %H:%M:%S')}",
            f"Status Hari Ini : {'LIBUR (' + reason + ')' if is_off else 'HARI KERJA'}",
            f"Check-in Status : {st.get('checkin_status')} (Jam: {st.get('checkin_time') or '-'})",
            f"Checkout Status : {st.get('checkout_status')} (Target: {st.get('scheduled_checkout_time') or '-'})",
        ]
        if st.get("last_error"):
            lines.append(f"Peringatan Terakhir: {st.get('last_error')}")
        return "\n".join(lines)

    def run_loop(self):
        """
        Continuous main loop for always-on computer.
        Handles daily rollover, holidays, dynamic check-in and check-out.
        """
        self.running = True
        logger.info("Bot Absensi E-Kinerja AKTIF. Menunggu jadwal absensi...")
        self.notifier.send("Bot Absensi Aktif", "Bot E-Kinerja siap berjalan otomatis di latar belakang.", level="INFO")

        # Initial synchronization with server
        self.check_and_sync_with_server()

        while self.running:
            try:
                now = datetime.now()
                today = now.date()

                # 1. Day Rollover Check
                self.state.refresh_day_if_needed()

                # 2. Check if today is Holiday or Weekend
                is_off, reason = self.holiday_checker.is_holiday_or_weekend(today)
                if is_off:
                    if self.state.current_state.get("checkin_status") != "SKIPPED":
                        logger.info(f"Hari ini adalah {reason}. Absensi dilewati (SKIPPED).")
                        self.state.mark_holiday(reason)
                        self.notifier.send("Hari Libur", f"Hari ini {reason}. Bot istirahat.", level="INFO")

                    # Sleep 60 seconds and continue
                    time.sleep(60)
                    continue

                # 3. Check-In Evaluation
                target_checkin_dt = self.parse_time_on_date(self.checkin_target_time, today)
                checkin_status = self.state.current_state.get("checkin_status")

                if checkin_status == "PENDING":
                    if now >= target_checkin_dt:
                        # It is time to check in!
                        success = self.execute_checkin_attempt()
                        if not success:
                            # Retry after interval
                            time.sleep(self.retry_interval_seconds)
                            continue

                # 4. Check-Out Evaluation
                checkout_status = self.state.current_state.get("checkout_status")
                scheduled_checkout_dt = self.state.get_scheduled_checkout()

                # If checkin was done, but scheduled_checkout_dt is not set yet, fallback to target checkin + 9 hours
                if checkin_status == "SUCCESS" and not scheduled_checkout_dt:
                    scheduled_checkout_dt = target_checkin_dt + timedelta(hours=self.work_duration_hours)
                    self.state.current_state["scheduled_checkout_time"] = scheduled_checkout_dt.isoformat()
                    self.state._save_state()

                if checkin_status == "SUCCESS" and checkout_status == "PENDING":
                    if scheduled_checkout_dt and now >= scheduled_checkout_dt:
                        # It is time to check out!
                        success = self.execute_checkout_attempt()
                        if not success:
                            # Retry after interval
                            time.sleep(self.retry_interval_seconds)
                            continue

                # 5. Periodic status logging every 30 minutes
                if time.time() - self.last_status_display_time > 1800:
                    self.last_status_display_time = time.time()
                    logger.info("Heartbeat: Bot aktif. Status:\n" + self.get_status_summary())

                # Sleep short tick for responsiveness
                time.sleep(10)

            except KeyboardInterrupt:
                logger.info("Bot dihentikan oleh pengguna (Ctrl+C).")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Terjadi kesalahan tidak terduga pada scheduler: {e}", exc_info=True)
                time.sleep(15)

    def stop(self):
        self.running = False
