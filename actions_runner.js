const { EkinerjaClient } = require('./lib/ekinerja');
const { isHolidayOrWeekend } = require('./lib/holidays');
const { sendNotification } = require('./lib/notifier');

async function main() {
  const action = process.argv[2] || 'auto';
  console.log("==================================================");
  console.log(`🤖 GitHub Actions E-Kinerja Runner [Action: ${action.toUpperCase()}]`);
  console.log("==================================================");

  // 1. Check Holiday & Weekend
  const holiday = await isHolidayOrWeekend(new Date());
  console.log(`Status Hari: ${holiday.reason} (${holiday.date})`);

  if (holiday.isOff) {
    console.log(`[SKIP] Hari ini libur (${holiday.reason}). Tidak melakukan absensi.`);
    return;
  }

  const client = new EkinerjaClient();
  const statusRes = await client.getStatus();
  if (!statusRes.success) {
    console.error(`[ERROR] Gagal mendapatkan status E-Kinerja: ${statusRes.error}`);
    process.exit(1);
  }

  const data = statusRes.data;
  console.log(`User: ${data.user?.name} (ID: ${data.user?.employee_id})`);
  console.log(`Status Check-In  : ${data.hasLoggedIn ? 'Sudah (' + data.waktuLogin + ')' : 'Belum'}`);
  console.log(`Status Check-Out : ${data.hasLoggedOut ? 'Sudah (' + data.waktuLogout + ')' : 'Belum'}`);

  // Determine action
  let targetAction = action;
  if (action === 'auto') {
    const hourJakarta = parseInt(
      new Intl.DateTimeFormat('en-US', {
        timeZone: 'Asia/Jakarta',
        hour: 'numeric',
        hour12: false
      }).format(new Date()),
      10
    );
    if (hourJakarta < 14) {
      targetAction = 'checkin';
    } else {
      targetAction = 'checkout';
    }
  }

  // --- CHECKIN EXECUTION ---
  if (targetAction === 'checkin') {
    if (data.hasLoggedIn) {
      console.log(`[INFO] Sudah check-in sebelumnya pada ${data.waktuLogin}. Tidak perlu check-in lagi.`);
      return;
    }

    console.log("[ACTION] Memulai proses Check-In...");
    const checkinRes = await client.checkin();
    if (checkinRes.success) {
      console.log(`[SUCCESS] ${checkinRes.message}`);
      await sendNotification("Check-In Berhasil (GitHub Actions)", checkinRes.message, "SUCCESS");
    } else {
      console.error(`[FAILED] Check-In gagal: ${checkinRes.error}`);
      await sendNotification("Check-In Gagal (GitHub Actions)", checkinRes.error, "ERROR");
      process.exit(1);
    }
  }

  // --- CHECKOUT EXECUTION ---
  if (targetAction === 'checkout') {
    if (!data.hasLoggedIn) {
      console.log("[INFO] Belum melakukan check-in hari ini. Melewati check-out.");
      return;
    }

    if (data.hasLoggedOut) {
      console.log(`[INFO] Sudah check-out sebelumnya pada ${data.waktuLogout}. Tidak perlu check-out lagi.`);
      return;
    }

    // Dynamic 9-hour checkout calculation
    let checkinDate = new Date();
    if (data.waktuLogin) {
      const parsed = new Date(data.waktuLogin.replace(' ', 'T'));
      if (!isNaN(parsed.getTime())) {
        checkinDate = parsed;
      }
    }

    const workHours = parseFloat(process.env.WORK_DURATION_HOURS || "9.0");
    const scheduledCheckoutTime = new Date(checkinDate.getTime() + workHours * 60 * 60 * 1000);
    const now = new Date();

    const inStr = new Intl.DateTimeFormat('id-ID', {
      timeZone: 'Asia/Jakarta',
      timeStyle: 'medium'
    }).format(checkinDate);

    const schedStr = new Intl.DateTimeFormat('id-ID', {
      timeZone: 'Asia/Jakarta',
      timeStyle: 'medium'
    }).format(scheduledCheckoutTime);

    console.log(`Waktu Check-In   : ${inStr} WIB`);
    console.log(`Target Check-Out : ${schedStr} WIB (+${workHours} jam)`);

    if (now < scheduledCheckoutTime) {
      const diffMin = Math.round((scheduledCheckoutTime - now) / 60000);
      console.log(`[WAIT] Belum saatnya check-out. Waktu checkout dijadwalkan pada ${schedStr} (${diffMin} menit lagi). Menunggu cron berikutnya.`);
      return;
    }

    // Time is due!
    console.log("[ACTION] Waktu checkout telah tiba! Memulai proses Check-Out...");
    const checkoutRes = await client.checkout();
    if (checkoutRes.success) {
      console.log(`[SUCCESS] ${checkoutRes.message}`);
      await sendNotification("Check-Out Berhasil (GitHub Actions)", checkoutRes.message, "SUCCESS");
    } else {
      console.error(`[FAILED] Check-Out gagal: ${checkoutRes.error}`);
      await sendNotification("Check-Out Gagal (GitHub Actions)", checkoutRes.error, "ERROR");
      process.exit(1);
    }
  }

  console.log("==================================================");
}

main().catch(err => {
  console.error("Fatal Error:", err);
  process.exit(1);
});
