#!/usr/bin/env node
/** Screenshot automation infographic HTML files to 1080x1080 PNGs. */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const manifestPath = process.argv[2] || (() => {
  const base = __dirname;
  const dirs = fs.readdirSync(path.join(base, 'automation-images')).sort();
  if (!dirs.length) throw new Error('No automation-images batches found');
  return path.join(base, 'automation-images', dirs[dirs.length - 1], 'manifest.json');
})();

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

(async () => {
  const chromePaths = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
  ];
  const executablePath = chromePaths.find(p => fs.existsSync(p));
  if (!executablePath) throw new Error('Chrome not found for screenshots');

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });

  for (const entry of manifest.images) {
    const html = fs.readFileSync(entry.html, 'utf8');
    await page.setContent(html, { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: entry.png, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
    console.log(`Saved ${entry.png}`);
  }

  await browser.close();
})().catch(err => {
  console.error(err);
  process.exit(1);
});
