const { EkinerjaClient } = require('../lib/ekinerja');
const { isHolidayOrWeekend } = require('../lib/holidays');

module.exports = async function handler(req, res) {
  try {
    const client = new EkinerjaClient();
    const status = await client.getStatus();
    const holiday = await isHolidayOrWeekend(new Date());

    const nowJakarta = new Intl.DateTimeFormat('id-ID', {
      timeZone: 'Asia/Jakarta',
      dateStyle: 'full',
      timeStyle: 'medium'
    }).format(new Date());

    return res.status(200).json({
      serverTimeWIB: nowJakarta,
      holiday,
      attendance: status
    });
  } catch (err) {
    return res.status(500).json({ success: false, error: err.message });
  }
};
