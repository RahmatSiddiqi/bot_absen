import json
import logging
import os
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import requests

logger = logging.getLogger("HolidayChecker")

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "holidays_cache.json")

class HolidayChecker:
    def __init__(self, custom_holidays: Optional[List[str]] = None):
        """
        custom_holidays: List of dates in YYYY-MM-DD format that should be considered holidays (e.g. cuti bersama)
        """
        self.custom_holidays = set(custom_holidays or [])
        self.holidays: Dict[str, str] = {} # "YYYY-MM-DD": "Nama Libur"
        self._load_cache()

    def _load_cache(self):
        """Load cached holidays from local file."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self.holidays = json.load(f)
                logger.info(f"Loaded {len(self.holidays)} libur nasional dari cache.")
            except Exception as e:
                logger.warning(f"Gagal membaca cache hari libur: {e}")

    def _save_cache(self):
        """Save holidays to local cache file."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.holidays, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Gagal menyimpan cache hari libur: {e}")

    def fetch_holidays(self, year: Optional[int] = None) -> bool:
        """
        Fetch national holidays from public APIs.
        """
        if year is None:
            year = datetime.now().year

        success = False

        # Try Nager.Date API
        try:
            url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/ID"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for item in data:
                    d = item.get("date")
                    name = item.get("localName") or item.get("name")
                    if d and name:
                        self.holidays[d] = name
                success = True
                logger.info(f"Berhasil update {len(data)} libur dari Nager.Date ({year})")
        except Exception as e:
            logger.warning(f"Gagal mengambil libur dari Nager.Date: {e}")

        # Try APIHariLibur_V2
        try:
            url = "https://raw.githubusercontent.com/guangrei/APIHariLibur_V2/main/holidays.json"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for d_str, info in data.items():
                    # format might be "2026-05-01" or dict
                    if isinstance(info, dict):
                        if info.get("is_holiday"):
                            self.holidays[d_str] = info.get("summary", "Hari Libur Nasional")
                    elif isinstance(info, str):
                        self.holidays[d_str] = info
                success = True
                logger.info("Berhasil update libur dari APIHariLibur_V2")
        except Exception as e:
            logger.warning(f"Gagal mengambil libur dari APIHariLibur_V2: {e}")

        if success:
            self._save_cache()

        return success

    def is_holiday_or_weekend(self, dt: Optional[date] = None) -> Tuple[bool, str]:
        """
        Check if given date is Saturday/Sunday or Tanggal Merah.
        Returns (is_off, reason).
        """
        if dt is None:
            dt = datetime.now().date()
        elif isinstance(dt, datetime):
            dt = dt.date()

        date_str = dt.strftime("%Y-%m-%d")

        # 1. Weekend check (Monday is 0, Sunday is 6)
        day_names = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        weekday = dt.weekday()
        if weekday == 5:
            return True, f"Hari Sabtu (Weekend)"
        if weekday == 6:
            return True, f"Hari Minggu (Weekend)"

        # 2. Custom holidays check
        if date_str in self.custom_holidays:
            return True, f"Custom Libur / Cuti Bersama ({date_str})"

        # 3. National holiday check
        if date_str in self.holidays:
            return True, f"Tanggal Merah: {self.holidays[date_str]}"

        # If cache is empty or year not loaded, try to fetch if not done yet
        if not self.holidays:
            if self.fetch_holidays(dt.year):
                if date_str in self.holidays:
                    return True, f"Tanggal Merah: {self.holidays[date_str]}"

        return False, f"Hari Kerja ({day_names[weekday]})"
