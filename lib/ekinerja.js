const BASE_URL = "https://ekinerja.paperlesshospital.id";

class CookieSession {
  constructor() {
    this.cookies = new Map();
  }

  updateCookies(res) {
    let raw = [];
    if (typeof res.headers.getSetCookie === 'function') {
      raw = res.headers.getSetCookie();
    } else {
      const single = res.headers.get('set-cookie');
      if (single) raw = [single];
    }

    for (const line of raw) {
      if (!line) continue;
      const parts = line.split(';')[0].split('=');
      if (parts.length >= 2) {
        this.cookies.set(parts[0].trim(), parts.slice(1).join('=').trim());
      }
    }
  }

  getCookieHeader() {
    return Array.from(this.cookies.entries()).map(([k, v]) => `${k}=${v}`).join('; ');
  }

  getCookie(name) {
    return this.cookies.get(name);
  }
}

class EkinerjaClient {
  constructor(options = {}) {
    this.email = options.email || process.env.EKINERJA_EMAIL;
    this.password = options.password || process.env.EKINERJA_PASSWORD;
    this.latitude = parseFloat(options.latitude || process.env.LATITUDE || "4.919988968942603");
    this.longitude = parseFloat(options.longitude || process.env.LONGITUDE || "97.79774437307512");
    this.session = new CookieSession();
    this.csrfToken = null;
    this.inertiaVersion = null;
    this.isLoggedIn = false;
    this.user = null;
  }

  _extractPageData(html) {
    // 1. If response is already raw JSON
    const trimmed = html.trim();
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      try {
        const parsed = JSON.parse(trimmed);
        if (parsed.props) return { csrf: this.csrfToken, pageData: parsed };
      } catch (e) {}
    }

    // 2. Extract CSRF meta
    const csrfMatch = html.match(/<meta\s+name=["']csrf-token["']\s+content=["']([^"']+)["']/i);
    const csrf = csrfMatch ? csrfMatch[1] : this.csrfToken;

    // 3. Extract Inertia data-page
    let pageData = null;
    const dataMatch = html.match(/<script\s+data-page=["']app["'][^>]*>([\s\S]*?)<\/script>/i);
    if (dataMatch) {
      try {
        pageData = JSON.parse(dataMatch[1].trim());
      } catch (e) {
        console.error("Gagal parse Inertia data-page JSON:", e);
      }
    }

    return { csrf, pageData };
  }

  _getInertiaHeaders(referer = "/absensi") {
    const headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'text/html, application/xhtml+xml, application/json, text/plain, */*',
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      'X-Inertia': 'true',
      'Origin': BASE_URL,
      'Referer': `${BASE_URL}${referer}`,
      'Cookie': this.session.getCookieHeader()
    };
    if (this.csrfToken) headers['X-CSRF-TOKEN'] = this.csrfToken;
    const xsrf = this.session.getCookie('XSRF-TOKEN');
    if (xsrf) headers['X-XSRF-TOKEN'] = decodeURIComponent(xsrf);
    if (this.inertiaVersion) headers['X-Inertia-Version'] = this.inertiaVersion;
    return headers;
  }

  async refreshPage(endpoint = "/absensi") {
    try {
      const url = `${BASE_URL}${endpoint}`;
      const res = await fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Cookie': this.session.getCookieHeader()
        }
      });
      this.session.updateCookies(res);

      if (res.status !== 200) {
        return { success: false, error: `HTTP ${res.status} saat akses ${endpoint}` };
      }

      const text = await res.text();
      const { csrf, pageData } = this._extractPageData(text);
      if (csrf) this.csrfToken = csrf;
      if (pageData?.version) this.inertiaVersion = pageData.version;

      const user = pageData?.props?.auth?.user;
      if (user) {
        this.isLoggedIn = true;
        this.user = user;
      } else {
        this.isLoggedIn = false;
        this.user = null;
      }

      return { success: true, pageData };
    } catch (err) {
      return { success: false, error: `Koneksi gagal: ${err.message}` };
    }
  }

  async login() {
    console.log(`[JS Client] Login ke ${this.email}...`);
    const init = await this.refreshPage("/login");
    if (!init.success) return { success: false, error: init.error };

    if (this.isLoggedIn) {
      return { success: true, message: `Sudah login sebagai ${this.user.name}` };
    }

    const loginUrl = `${BASE_URL}/login`;
    const headers = this._getInertiaHeaders("/login");
    const payload = {
      email: this.email,
      password: this.password,
      remember: true
    };

    try {
      const res = await fetch(loginUrl, {
        method: 'POST',
        redirect: 'manual',
        headers,
        body: JSON.stringify(payload)
      });
      this.session.updateCookies(res);

      const loc = res.headers.get('location') || '';
      if (res.status === 302 || res.status === 303) {
        if (loc.includes('/login')) {
          return { success: false, error: "Login ditolak: Email atau password tidak sesuai." };
        }
        // Valid redirect to dashboard or absensi
        const absCheck = await this.refreshPage("/absensi");
        if (absCheck.success && this.isLoggedIn) {
          console.log(`[JS Client] Login sukses! Selamat datang, ${this.user.name}`);
          return { success: true, message: `Berhasil login sebagai ${this.user.name}` };
        }
      }

      return { success: false, error: "Gagal memverifikasi session login." };
    } catch (err) {
      return { success: false, error: `Koneksi putus saat login: ${err.message}` };
    }
  }

  async getStatus() {
    let check = await this.refreshPage("/absensi");
    if (!check.success || !this.isLoggedIn) {
      const loginRes = await this.login();
      if (!loginRes.success) return { success: false, error: loginRes.error };
      check = await this.refreshPage("/absensi");
      if (!check.success) return { success: false, error: check.error };
    }

    const props = check.pageData?.props || {};
    const quick = props.quickAttendance || {};
    const absensiHariIni = props.absensiHariIni || null;

    let hasLoggedIn = quick.has_logged_in || false;
    let hasLoggedOut = quick.has_logged_out || false;
    let waktuLogin = quick.waktu_login || null;
    let waktuLogout = quick.waktu_logout || null;

    if (absensiHariIni) {
      if (!waktuLogin && absensiHariIni.waktu_login) waktuLogin = absensiHariIni.waktu_login;
      if (!waktuLogout && absensiHariIni.waktu_logout) waktuLogout = absensiHariIni.waktu_logout;
      if (waktuLogin) hasLoggedIn = true;
      if (waktuLogout) hasLoggedOut = true;
    }

    return {
      success: true,
      data: {
        canAccess: quick.can_access !== false,
        hasLoggedIn,
        hasLoggedOut,
        waktuLogin,
        waktuLogout,
        minimumWorkHours: quick.minimum_work_hours || 8,
        user: this.user
      }
    };
  }

  async checkin(keterangan = "") {
    const statusRes = await this.getStatus();
    if (!statusRes.success) return statusRes;

    if (statusRes.data.hasLoggedIn) {
      return {
        success: true,
        alreadyDone: true,
        message: `Hari ini sudah check-in pada: ${statusRes.data.waktuLogin}`,
        data: statusRes.data
      };
    }

    const checkinUrl = `${BASE_URL}/absensi/login`;
    const headers = this._getInertiaHeaders("/absensi");
    const payload = {
      latitude: this.latitude,
      longitude: this.longitude,
      keterangan: keterangan || ""
    };

    try {
      const res = await fetch(checkinUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });
      this.session.updateCookies(res);

      const verify = await this.getStatus();
      if (verify.success && verify.data.hasLoggedIn) {
        return {
          success: true,
          message: `Check-in BERHASIL dicatat pada: ${verify.data.waktuLogin}`,
          data: verify.data
        };
      }
      return { success: false, error: "Server tidak mencatat check-in. Periksa kembali lokasi atau jadwal." };
    } catch (err) {
      return { success: false, error: `Koneksi gagal saat check-in: ${err.message}` };
    }
  }

  async checkout(keterangan = "") {
    const statusRes = await this.getStatus();
    if (!statusRes.success) return statusRes;

    if (!statusRes.data.hasLoggedIn) {
      return { success: false, error: "Belum bisa check-out karena belum check-in hari ini!" };
    }

    if (statusRes.data.hasLoggedOut) {
      return {
        success: true,
        alreadyDone: true,
        message: `Hari ini sudah check-out pada: ${statusRes.data.waktuLogout}`,
        data: statusRes.data
      };
    }

    const checkoutUrl = `${BASE_URL}/absensi/logout`;
    const headers = this._getInertiaHeaders("/absensi");
    const payload = {
      latitude: this.latitude,
      longitude: this.longitude,
      keterangan: keterangan || ""
    };

    try {
      const res = await fetch(checkoutUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });
      this.session.updateCookies(res);

      const verify = await this.getStatus();
      if (verify.success && verify.data.hasLoggedOut) {
        return {
          success: true,
          message: `Check-out BERHASIL dicatat pada: ${verify.data.waktuLogout}`,
          data: verify.data
        };
      }
      return { success: false, error: "Server tidak mencatat check-out. Pastikan durasi kerja sudah mencukupi." };
    } catch (err) {
      return { success: false, error: `Koneksi gagal saat check-out: ${err.message}` };
    }
  }
}

async function testLogin() {
  require('dotenv').config();
  const client = new EkinerjaClient();
  const res = await client.getStatus();
  console.log("Hasil Uji Login Node.js:", JSON.stringify(res, null, 2));
}

module.exports = { EkinerjaClient, testLogin };
