import json
import logging
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger("StateManager")

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attendance_state.json")

class StateManager:
    def __init__(self, work_duration_hours: float = 9.0):
        self.work_duration_hours = work_duration_hours
        self.current_state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load state from local file or initialize default."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("date") == today_str:
                        return data
            except Exception as e:
                logger.warning(f"Gagal membaca state file: {e}")

        # Initialize fresh state for today
        return self._create_default_state(today_str)

    def _create_default_state(self, date_str: str) -> Dict[str, Any]:
        state = {
            "date": date_str,
            "is_holiday_or_weekend": False,
            "holiday_reason": "",
            "checkin_status": "PENDING",    # PENDING, IN_PROGRESS, SUCCESS, SKIPPED
            "checkin_time": None,           # ISO string e.g. "2026-10-17T08:20:15"
            "scheduled_checkout_time": None,# ISO string e.g. "2026-10-17T17:20:15"
            "checkout_status": "PENDING",   # PENDING, IN_PROGRESS, SUCCESS, SKIPPED
            "checkout_time": None,          # ISO string
            "checkin_attempts": 0,
            "checkout_attempts": 0,
            "last_error": None,
            "last_updated": datetime.now().isoformat()
        }
        self._save_state(state)
        return state

    def _save_state(self, state: Optional[Dict[str, Any]] = None):
        """Save current state to json file."""
        if state is not None:
            self.current_state = state
        self.current_state["last_updated"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.current_state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Gagal menyimpan state: {e}")

    def refresh_day_if_needed(self):
        """Check if date has rolled over to a new day."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        if self.current_state.get("date") != today_str:
            logger.info(f"Hari baru terdeteksi: {today_str}. Mengatur ulang state absensi...")
            self.current_state = self._create_default_state(today_str)

    def mark_holiday(self, reason: str):
        self.current_state["is_holiday_or_weekend"] = True
        self.current_state["holiday_reason"] = reason
        self.current_state["checkin_status"] = "SKIPPED"
        self.current_state["checkout_status"] = "SKIPPED"
        self._save_state()

    def record_checkin_success(self, checkin_dt: datetime):
        """
        Record check-in success and calculate scheduled checkout time!
        Rule: scheduled checkout = checkin_time + work_duration_hours (e.g. 9 hours).
        Example: checkin at 08:20 -> checkout at 17:20.
        """
        self.current_state["checkin_status"] = "SUCCESS"
        self.current_state["checkin_time"] = checkin_dt.isoformat()

        # Calculate checkout: checkin_time + work_duration_hours
        checkout_dt = checkin_dt + timedelta(hours=self.work_duration_hours)
        self.current_state["scheduled_checkout_time"] = checkout_dt.isoformat()
        self.current_state["last_error"] = None
        self._save_state()
        logger.info(f"State saved: Checkin pada {checkin_dt.strftime('%H:%M:%S')}. Jadwal Checkout dihitung otomatis: {checkout_dt.strftime('%H:%M:%S')}")

    def record_checkout_success(self, checkout_dt: datetime):
        """Record checkout success."""
        self.current_state["checkout_status"] = "SUCCESS"
        self.current_state["checkout_time"] = checkout_dt.isoformat()
        self.current_state["last_error"] = None
        self._save_state()
        logger.info(f"State saved: Checkout berhasil pada {checkout_dt.strftime('%H:%M:%S')}")

    def record_error(self, step: str, error_msg: str):
        if step == "checkin":
            self.current_state["checkin_attempts"] += 1
        elif step == "checkout":
            self.current_state["checkout_attempts"] += 1
        self.current_state["last_error"] = f"[{step.upper()}] {error_msg}"
        self._save_state()

    def get_scheduled_checkout(self) -> Optional[datetime]:
        """Return scheduled checkout datetime if checkin has succeeded."""
        iso_str = self.current_state.get("scheduled_checkout_time")
        if iso_str:
            try:
                return datetime.fromisoformat(iso_str)
            except Exception:
                return None
        return None
