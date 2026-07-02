// Generic 1080x1080 screenshotter. Usage: node cap_html_1080.js <input.html> <output.png>
const puppeteer = require('/Users/prithal/Downloads/daily-linkedin-posts-pipeline/carousel-routine/node_modules/puppeteer');
const path = require('path');
(async () => {
  const htmlPath = process.argv[2];
  const outPath = process.argv[3];
  if (!htmlPath || !outPath) { console.error('usage: node cap_html_1080.js <in.html> <out.png>'); process.exit(1); }
  const browser = await puppeteer.launch({
    headless: 'shell',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 2 });
  await page.goto('file://' + encodeURI(path.resolve(htmlPath)), { waitUntil: 'networkidle0', timeout: 35000 });
  try { await page.evaluate(() => document.fonts.ready); } catch (e) {}
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: outPath, type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1080 } });
  await browser.close();
  console.log('saved', outPath);
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
