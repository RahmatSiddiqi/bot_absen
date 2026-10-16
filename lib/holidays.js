let cachedHolidays = {};
let lastFetchYear = null;

async function fetchHolidays(year = new Date().getFullYear()) {
  if (lastFetchYear === year && Object.keys(cachedHolidays).length > 0) {
    return cachedHolidays;
  }

  try {
    const res = await fetch(`https://date.nager.at/api/v3/PublicHolidays/${year}/ID`);
    if (res.ok) {
      const data = await res.json();
      for (const item of data) {
        if (item.date && (item.localName || item.name)) {
          cachedHolidays[item.date] = item.localName || item.name;
        }
      }
      lastFetchYear = year;
      return cachedHolidays;
    }
  } catch (e) {
    console.warn("Gagal fetch libur dari Nager.Date:", e.message);
  }

  // Fallback to APIHariLibur_V2
  try {
    const res = await fetch("https://raw.githubusercontent.com/guangrei/APIHariLibur_V2/main/holidays.json");
    if (res.ok) {
      const data = await res.json();
      for (const [dateStr, info] of Object.entries(data)) {
        if (typeof info === 'object' && info.is_holiday) {
          cachedHolidays[dateStr] = info.summary || "Hari Libur Nasional";
        } else if (typeof info === 'string') {
          cachedHolidays[dateStr] = info;
        }
      }
      lastFetchYear = year;
    }
  } catch (e) {
    console.warn("Gagal fetch libur dari APIHariLibur_V2:", e.message);
  }

  return cachedHolidays;
}

async function isHolidayOrWeekend(targetDate = new Date(), customHolidays = []) {
  // Format YYYY-MM-DD in Asia/Jakarta timezone
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Jakarta',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(targetDate); // returns "YYYY-MM-DD"

  // Get day of week in Jakarta (0 = Sunday, 6 = Saturday)
  const dayOfWeekStr = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Jakarta',
    weekday: 'short'
  }).format(targetDate);

  if (dayOfWeekStr === 'Sat') {
    return { isOff: true, reason: 'Hari Sabtu (Weekend)', date: parts };
  }
  if (dayOfWeekStr === 'Sun') {
    return { isOff: true, reason: 'Hari Minggu (Weekend)', date: parts };
  }

  // Custom holidays
  if (customHolidays && customHolidays.includes(parts)) {
    return { isOff: true, reason: `Cuti Bersama / Custom Libur (${parts})`, date: parts };
  }

  // National holidays
  const year = parseInt(parts.split('-')[0], 10);
  const holidays = await fetchHolidays(year);
  if (holidays[parts]) {
    return { isOff: true, reason: `Tanggal Merah: ${holidays[parts]}`, date: parts };
  }

  return { isOff: false, reason: 'Hari Kerja Normal', date: parts };
}

module.exports = { fetchHolidays, isHolidayOrWeekend };
