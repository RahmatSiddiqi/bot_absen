const { EkinerjaClient } = require('../lib/ekinerja');
const { isHolidayOrWeekend } = require('../lib/holidays');
const { sendNotification } = require('../lib/notifier');

module.exports = async function handler(req, res) {
  try {
    const force = req.query.force === 'true';

    // 1. Holiday & Weekend check
    const holiday = await isHolidayOrWeekend(new Date());
    if (holiday.isOff && !force) {
      console.log(`[Checkin API] Hari libur: ${holiday.reason}. Skip checkin.`);
      return res.status(200).json({
        success: true,
        skipped: true,
        reason: holiday.reason,
        message: `Check-in dilewati karena ${holiday.reason}.`
      });
    }

    // 2. Perform Checkin
    const client = new EkinerjaClient();
    const result = await client.checkin(req.query.keterangan || "");

    if (result.success) {
      if (result.alreadyDone) {
        return res.status(200).json(result);
      }
      await sendNotification("Check-In Berhasil", result.message, "SUCCESS");
      return res.status(200).json(result);
    } else {
      await sendNotification("Check-In Gagal", result.error, "ERROR");
      return res.status(400).json(result);
    }
  } catch (err) {
    return res.status(500).json({ success: false, error: err.message });
  }
};
