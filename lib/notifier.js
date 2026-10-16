async function sendNotification(title, message, level = "INFO") {
  const telegramToken = process.env.TELEGRAM_BOT_TOKEN;
  const telegramChatId = process.env.TELEGRAM_CHAT_ID;
  const discordWebhook = process.env.DISCORD_WEBHOOK_URL;

  console.log(`[NOTIF ${level}] ${title}: ${message}`);

  // 1. Telegram
  if (telegramToken && telegramChatId) {
    const icons = { SUCCESS: "✅", INFO: "ℹ️", WARNING: "⚠️", ERROR: "❌" };
    const icon = icons[level] || "📌";
    const text = `${icon} *${title}*\n\n${message}`;
    try {
      await fetch(`https://api.telegram.org/bot${telegramToken}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: telegramChatId,
          text: text,
          parse_mode: "Markdown"
        })
      });
    } catch (e) {
      console.warn("Gagal kirim notif Telegram:", e.message);
    }
  }

  // 2. Discord
  if (discordWebhook) {
    const colors = { SUCCESS: 0x2ecc71, INFO: 0x3498db, WARNING: 0xf39c12, ERROR: 0xe74c3c };
    try {
      await fetch(discordWebhook, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          embeds: [{
            title: title,
            description: message,
            color: colors[level] || 0x95a5a6
          }]
        })
      });
    } catch (e) {
      console.warn("Gagal kirim Discord webhook:", e.message);
    }
  }
}

module.exports = { sendNotification };
