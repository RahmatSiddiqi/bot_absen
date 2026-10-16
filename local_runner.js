require('dotenv').config();
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const statusHandler = require('./api/status');
const checkinHandler = require('./api/checkin');
const checkoutHandler = require('./api/checkout');
const botHandler = require('./api/bot');

const PORT = process.env.PORT || 3000;

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  // Add Vercel-like helpers to req/res
  req.query = parsedUrl.query;
  res.status = (code) => {
    res.statusCode = code;
    return res;
  };
  res.json = (data) => {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(data));
  };

  try {
    if (pathname === '/api/status') {
      return await statusHandler(req, res);
    } else if (pathname === '/api/checkin') {
      return await checkinHandler(req, res);
    } else if (pathname === '/api/checkout') {
      return await checkoutHandler(req, res);
    } else if (pathname === '/api/bot') {
      return await botHandler(req, res);
    } else {
      // Serve static files from public/
      let filePath = path.join(__dirname, 'public', pathname === '/' ? 'index.html' : pathname);
      if (fs.existsSync(filePath)) {
        const ext = path.extname(filePath);
        const mimeTypes = {
          '.html': 'text/html',
          '.js': 'text/javascript',
          '.css': 'text/css',
          '.png': 'image/png'
        };
        res.setHeader('Content-Type', mimeTypes[ext] || 'text/plain');
        return res.end(fs.readFileSync(filePath));
      }

      res.status(404).json({ error: 'Not Found' });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

server.listen(PORT, () => {
  console.log(`\n=============================================================`);
  console.log(`🚀 E-KINERJA BOT WEB SERVER AKTIF (JavaScript Edition)`);
  console.log(`=============================================================`);
  console.log(`• Local Dashboard : http://localhost:${PORT}`);
  console.log(`• API Status      : http://localhost:${PORT}/api/status`);
  console.log(`• API Check-In    : http://localhost:${PORT}/api/checkin`);
  console.log(`• API Check-Out   : http://localhost:${PORT}/api/checkout`);
  console.log(`• API Cron Bot    : http://localhost:${PORT}/api/bot`);
  console.log(`=============================================================\n`);
});
