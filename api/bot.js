const checkinHandler = require('./checkin');
const checkoutHandler = require('./checkout');
const statusHandler = require('./status');

module.exports = async function handler(req, res) {
  const action = req.query.action || 'auto';

  if (action === 'checkin') {
    return checkinHandler(req, res);
  }

  if (action === 'checkout') {
    return checkoutHandler(req, res);
  }

  if (action === 'status') {
    return statusHandler(req, res);
  }

  // Auto mode: decides based on current hour in Jakarta (WIB)
  const hourJakarta = parseInt(
    new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Jakarta',
      hour: 'numeric',
      hour12: false
    }).format(new Date()),
    10
  );

  console.log(`[Bot Auto] Jam WIB saat ini: ${hourJakarta}:00`);

  if (hourJakarta >= 6 && hourJakarta < 14) {
    // Morning to early afternoon -> Check-in window
    return checkinHandler(req, res);
  } else if (hourJakarta >= 14 && hourJakarta <= 23) {
    // Afternoon / Evening -> Check-out window
    return checkoutHandler(req, res);
  } else {
    return res.status(200).json({
      success: true,
      message: `Di luar jam kerja aktif (${hourJakarta}:00 WIB). Tidak ada tindakan.`
    });
  }
};
