const { EkinerjaClient } = require('../lib/ekinerja');
const { isHolidayOrWeekend } = require('../lib/holidays');
const { sendNotification } = require('../lib/notifier');

module.exports = async function handler(req, res) {
  try {
    const force = req.query.force === 'true';

    // 1. Holiday & Weekend check
    const holiday = await isHolidayOrWeekend(new Date());
    if (holiday.isOff && !force) {
      return res.status(200).json({
        success: true,
        skipped: true,
        reason: holiday.reason,
        message: `Check-out dilewati karena ${holiday.reason}.`
      });
    }

    const client = new EkinerjaClient();
    const statusRes = await client.getStatus();
    if (!statusRes.success) {
      return res.status(500).json(statusRes);
    }

    const data = statusRes.data;
    if (!data.hasLoggedIn) {
      return res.status(200).json({
        success: false,
        message: "Belum melakukan check-in hari ini. Tidak dapat check-out."
      });
    }

    if (data.hasLoggedOut) {
      return res.status(200).json({
        success: true,
        alreadyDone: true,
        message: `Hari ini sudah check-out pada: ${data.waktuLogout}`
      });
    }

    // Dynamic 9-hour calculation
    // e.g. waktuLogin = "2026-10-17 08:20:00" or ISO format
    let checkinDate = new Date();
    if (data.waktuLogin) {
      const parsed = new Date(data.waktuLogin.replace(' ', 'T'));
      if (!isNaN(parsed.getTime())) {
        checkinDate = parsed;
      }
    }

    // Work duration in hours (default 9 hours)
    const workHours = parseFloat(process.env.WORK_DURATION_HOURS || "9.0");
    const scheduledCheckoutTime = new Date(checkinDate.getTime() + workHours * 60 * 60 * 1000);
    const now = new Date();

    const diffMinutes = Math.round((scheduledCheckoutTime - now) / (60 * 1000));

    if (now < scheduledCheckoutTime && !force) {
      const schedStr = new Intl.DateTimeFormat('id-ID', {
        timeZone: 'Asia/Jakarta',
        timeStyle: 'medium'
      }).format(scheduledCheckoutTime);

      const inStr = new Intl.DateTimeFormat('id-ID', {
        timeZone: 'Asia/Jakarta',
        timeStyle: 'medium'
      }).format(checkinDate);

      return res.status(200).json({
        success: true,
        waiting: true,
        waktuLogin: inStr,
        scheduledCheckoutTime: schedStr,
        remainingMinutes: diffMinutes,
        message: `Belum waktunya check-out. Check-in pada ${inStr}, maka check-out dijadwalkan pada ${schedStr} (${diffMinutes} menit lagi).`
      });
    }

    // Time has arrived or forced! Perform checkout
    const result = await client.checkout(req.query.keterangan || "");
    if (result.success) {
      await sendNotification("Check-Out Berhasil", result.message, "SUCCESS");
      return res.status(200).json(result);
    } else {
      await sendNotification("Check-Out Gagal", result.error, "ERROR");
      return res.status(400).json(result);
    }

  } catch (err) {
    return res.status(500).json({ success: false, error: err.message });
  }
};
