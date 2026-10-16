import re
import json
import logging
import urllib.parse
from typing import Optional, Dict, Any, Tuple
import requests

logger = logging.getLogger("EkinerjaClient")

class EkinerjaClient:
    BASE_URL = "https://ekinerja.paperlesshospital.id"

    def __init__(self, email: str, password: str, latitude: float = 4.919988968942603, longitude: float = 97.79774437307512):
        self.email = email
        self.password = password
        self.latitude = latitude
        self.longitude = longitude
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html, application/xhtml+xml, application/json, text/plain, */*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Origin': self.BASE_URL,
        })
        self.csrf_token: Optional[str] = None
        self.inertia_version: Optional[str] = None
        self.is_logged_in = False
        self.user_info: Dict[str, Any] = {}

    def _extract_page_data(self, content: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Extract CSRF token and Inertia page data from HTML or raw JSON."""
        # Check if content is already direct JSON (Inertia response)
        content_stripped = content.strip()
        if content_stripped.startswith("{") and content_stripped.endswith("}"):
            try:
                page_data = json.loads(content_stripped)
                if isinstance(page_data, dict) and "props" in page_data:
                    return self.csrf_token, page_data
            except Exception:
                pass

        # Extract CSRF token from meta tag
        csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', content)
        csrf = csrf_match.group(1) if csrf_match else self.csrf_token

        # Extract data-page script content (using multiline/DOTALL match)
        page_data = None
        data_match = re.search(r'<script\s+data-page=["\']app["\'][^>]*>([\s\S]*?)</script>', content)
        if data_match:
            try:
                page_data = json.loads(data_match.group(1).strip())
            except Exception as e:
                logger.error(f"Gagal parse JSON data-page: {e}")

        return csrf, page_data

    def _get_inertia_headers(self, referer: str = "/absensi") -> Dict[str, str]:
        """Prepare Inertia AJAX headers."""
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'X-Inertia': 'true',
            'Content-Type': 'application/json',
            'Referer': f"{self.BASE_URL}{referer}",
            'Origin': self.BASE_URL
        }
        if self.csrf_token:
            headers['X-CSRF-TOKEN'] = self.csrf_token

        # Include unquoted XSRF-TOKEN cookie if present
        xsrf = self.session.cookies.get('XSRF-TOKEN')
        if xsrf:
            headers['X-XSRF-TOKEN'] = urllib.parse.unquote(xsrf)

        if self.inertia_version:
            headers['X-Inertia-Version'] = self.inertia_version
        return headers

    def refresh_page(self, endpoint: str = "/absensi") -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Fetch HTML page to get fresh session, CSRF token, and Inertia version.
        Returns (success, page_data, error_message).
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            res = self.session.get(url, timeout=20)
            if res.status_code == 409 and 'X-Inertia-Location' in res.headers:
                # Version mismatch reload
                redirect_url = res.headers['X-Inertia-Location']
                res = self.session.get(redirect_url, timeout=20)

            if res.status_code != 200:
                return False, None, f"HTTP {res.status_code} saat mengakses {url}"

            csrf, page_data = self._extract_page_data(res.text)
            if csrf:
                self.csrf_token = csrf
            if page_data and 'version' in page_data:
                self.inertia_version = page_data['version']

            # Check if user is authenticated from page props
            if page_data:
                auth = page_data.get('props', {}).get('auth', {})
                user = auth.get('user')
                if user:
                    self.is_logged_in = True
                    self.user_info = user
                else:
                    self.is_logged_in = False
                    self.user_info = {}

            return True, page_data, "OK"
        except requests.exceptions.RequestException as e:
            return False, None, f"Gagal koneksi: {str(e)}"

    def login(self) -> Tuple[bool, str]:
        """
        Login to E-Kinerja using email and password.
        Returns (success, message).
        """
        logger.info(f"Mencoba login sebagai {self.email}...")

        # 1. First get login page for fresh CSRF token & cookies
        ok, page_data, msg = self.refresh_page("/login")
        if not ok:
            return False, f"Gagal memuat halaman login: {msg}"

        if self.is_logged_in:
            nama = self.user_info.get('name', self.email)
            logger.info(f"Sudah dalam kondisi login sebagai {nama}")
            return True, f"Sudah login sebagai {nama}"

        # 2. Submit credentials via Inertia POST
        login_url = f"{self.BASE_URL}/login"
        headers = self._get_inertia_headers(referer="/login")
        payload = {
            'email': self.email,
            'password': self.password,
            'remember': True
        }

        try:
            # allow_redirects=False to inspect the 302 location
            res = self.session.post(login_url, json=payload, headers=headers, allow_redirects=False, timeout=20)

            # If 302 Redirect to /dashboard or another page (means credentials are valid!)
            if res.status_code in [302, 303]:
                loc = res.headers.get('Location', '')
                logger.info(f"Login response 302 -> Redirect ke {loc}")

                # If redirected back to /login, then login failed
                if "/login" in loc:
                    # fetch login page with error flash
                    _, err_page, _ = self.refresh_page("/login")
                    err_msg = "Email atau password tidak sesuai."
                    if err_page:
                        errors = err_page.get('props', {}).get('errors', {})
                        if errors:
                            err_msg = ", ".join(f"{k}: {v}" for k, v in errors.items())
                    return False, f"Login gagal: {err_msg}"

                # Successful login redirect (e.g. /dashboard or /)
                # Now verify by loading /absensi page directly
                ok_abs, page_abs, msg_abs = self.refresh_page("/absensi")
                if ok_abs and self.is_logged_in:
                    nama = self.user_info.get('name', self.email)
                    logger.info(f"Login BERHASIL! Selamat datang, {nama}")
                    return True, f"Berhasil login sebagai {nama}"

            # If status 200 (direct Inertia JSON response)
            csrf, page_data = self._extract_page_data(res.text)
            if page_data:
                errors = page_data.get('props', {}).get('errors', {})
                if errors:
                    err_msg = ", ".join(f"{k}: {v}" for k, v in errors.items())
                    return False, f"Login ditolak: {err_msg}"

                auth = page_data.get('props', {}).get('auth', {})
                user = auth.get('user')
                if user:
                    self.is_logged_in = True
                    self.user_info = user
                    nama = user.get('name', self.email)
                    logger.info(f"Login BERHASIL! Selamat datang, {nama}")
                    return True, f"Berhasil login sebagai {nama}"

            # Fallback check by loading /absensi
            ok_abs, page_abs, _ = self.refresh_page("/absensi")
            if ok_abs and self.is_logged_in:
                nama = self.user_info.get('name', self.email)
                logger.info(f"Login diverifikasi berhasil: {nama}")
                return True, f"Berhasil login sebagai {nama}"

            return False, "Login gagal: Kredensial salah atau session tidak terbentuk."
        except requests.exceptions.RequestException as e:
            return False, f"Koneksi terputus saat login: {str(e)}"

    def get_attendance_status(self) -> Tuple[bool, Dict[str, Any], str]:
        """
        Check current attendance status from /absensi.
        Returns: (success, status_dict, message)
        """
        ok, page_data, msg = self.refresh_page("/absensi")
        if not ok:
            return False, {}, msg

        if not self.is_logged_in:
            # Need to login first
            login_ok, login_msg = self.login()
            if not login_ok:
                return False, {}, f"Gagal login: {login_msg}"
            ok, page_data, msg = self.refresh_page("/absensi")
            if not ok or not page_data:
                return False, {}, f"Gagal memuat absensi setelah login: {msg}"

        props = page_data.get('props', {})
        quick = props.get('quickAttendance', {})
        absensi_hari_ini = props.get('absensiHariIni')

        status = {
            'can_access': quick.get('can_access', True),
            'has_logged_in': quick.get('has_logged_in', False),
            'has_logged_out': quick.get('has_logged_out', False),
            'can_logout': quick.get('can_logout', False),
            'waktu_login': quick.get('waktu_login'),
            'waktu_logout': quick.get('waktu_logout'),
            'minimum_work_hours': quick.get('minimum_work_hours', 8),
            'absensi_hari_ini': absensi_hari_ini,
            'user_name': self.user_info.get('name', ''),
            'employee_id': self.user_info.get('employee_id', '')
        }

        # If absensiHariIni is populated, verify waktu_login
        if absensi_hari_ini:
            if not status['waktu_login'] and absensi_hari_ini.get('waktu_login'):
                status['waktu_login'] = absensi_hari_ini.get('waktu_login')
                status['has_logged_in'] = True
            if not status['waktu_logout'] and absensi_hari_ini.get('waktu_logout'):
                status['waktu_logout'] = absensi_hari_ini.get('waktu_logout')
                status['has_logged_out'] = True

        return True, status, "OK"

    def checkin(self, keterangan: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """
        Perform Check-in (POST /absensi/login)
        Returns: (success, message, response_details)
        """
        logger.info(f"Memulai proses Check-in [Lat: {self.latitude}, Lng: {self.longitude}]...")

        # 1. Ensure logged in and on /absensi
        ok, status, msg = self.get_attendance_status()
        if not ok:
            return False, f"Gagal cek status absensi: {msg}", {}

        if status.get('has_logged_in'):
            waktu = status.get('waktu_login', 'Sudah tercatat')
            logger.info(f"Hari ini SUDAH check-in sebelumnya pada: {waktu}")
            return True, f"Sudah check-in hari ini ({waktu})", status

        checkin_url = f"{self.BASE_URL}/absensi/login"
        headers = self._get_inertia_headers(referer="/absensi")
        payload = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'keterangan': keterangan or ""
        }

        try:
            res = self.session.post(checkin_url, json=payload, headers=headers, allow_redirects=True, timeout=25)
            if res.status_code == 409 and 'X-Inertia-Location' in res.headers:
                res = self.session.get(res.headers['X-Inertia-Location'], timeout=20)

            # Check if check-in was successful by verifying status
            ok_verify, updated_status, verify_msg = self.get_attendance_status()
            if ok_verify and updated_status.get('has_logged_in'):
                waktu = updated_status.get('waktu_login', '')
                logger.info(f"CHECK-IN BERHASIL DICATAT! Waktu: {waktu}")
                return True, f"Check-in Berhasil! Waktu: {waktu}", updated_status
            else:
                _, page_data = self._extract_page_data(res.text)
                err_msg = "Unknown error"
                if page_data:
                    errors = page_data.get('props', {}).get('errors', {})
                    if errors:
                        err_msg = ", ".join(f"{k}: {v}" for k, v in errors.items())
                return False, f"Check-in gagal: {err_msg}", {}

        except requests.exceptions.RequestException as e:
            return False, f"Koneksi gagal saat check-in: {str(e)}", {}

    def checkout(self, keterangan: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """
        Perform Check-out (POST /absensi/logout)
        Returns: (success, message, response_details)
        """
        logger.info(f"Memulai proses Check-out [Lat: {self.latitude}, Lng: {self.longitude}]...")

        # 1. Ensure logged in and on /absensi
        ok, status, msg = self.get_attendance_status()
        if not ok:
            return False, f"Gagal cek status absensi: {msg}", {}

        if not status.get('has_logged_in'):
            return False, "Tidak dapat check-out karena belum melakukan check-in hari ini!", status

        if status.get('has_logged_out'):
            waktu = status.get('waktu_logout', 'Sudah tercatat')
            logger.info(f"Hari ini SUDAH check-out sebelumnya pada: {waktu}")
            return True, f"Sudah check-out hari ini ({waktu})", status

        checkout_url = f"{self.BASE_URL}/absensi/logout"
        headers = self._get_inertia_headers(referer="/absensi")
        payload = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'keterangan': keterangan or ""
        }

        try:
            res = self.session.post(checkout_url, json=payload, headers=headers, allow_redirects=True, timeout=25)
            if res.status_code == 409 and 'X-Inertia-Location' in res.headers:
                res = self.session.get(res.headers['X-Inertia-Location'], timeout=20)

            # Verify check-out status
            ok_verify, updated_status, verify_msg = self.get_attendance_status()
            if ok_verify and updated_status.get('has_logged_out'):
                waktu = updated_status.get('waktu_logout', '')
                logger.info(f"CHECK-OUT BERHASIL DICATAT! Waktu: {waktu}")
                return True, f"Check-out Berhasil! Waktu: {waktu}", updated_status
            else:
                _, page_data = self._extract_page_data(res.text)
                err_msg = "Periksa kembali durasi jam kerja atau data absensi."
                if page_data:
                    errors = page_data.get('props', {}).get('errors', {})
                    if errors:
                        err_msg = ", ".join(f"{k}: {v}" for k, v in errors.items())
                return False, f"Check-out gagal: {err_msg}", {}

        except requests.exceptions.RequestException as e:
            return False, f"Koneksi gagal saat check-out: {str(e)}", {}
