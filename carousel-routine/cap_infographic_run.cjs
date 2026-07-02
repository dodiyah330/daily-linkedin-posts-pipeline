const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });
  const html = fs.readFileSync(path.join(ROOT, 'linkedin-infographic.html'), 'utf8');
  const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html);
  });
  await new Promise(r => server.listen(8791, r));
  await page.goto('http://localhost:8791', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 500));
  const d = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const out = path.join(ROOT, `linkedin-infographic-${d}.png`);
  await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
  console.log('infographic: ' + out);
  server.close();
  await browser.close();
  console.log('ALL_DONE');
})();
