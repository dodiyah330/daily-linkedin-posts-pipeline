#!/usr/bin/env node
/** Screenshot US infographic HTML files to PNG. */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const manifestPath = process.argv[2];
if (!manifestPath) {
  console.error('Usage: node cap_us_images.cjs <manifest.json>');
  process.exit(1);
}

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

(async () => {
  const chromePaths = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
  ];
  const executablePath = chromePaths.find(p => fs.existsSync(p));
  if (!executablePath) throw new Error('Chrome not found');

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });

  for (const entry of manifest.images) {
    await page.setContent(fs.readFileSync(entry.html, 'utf8'), { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: entry.png, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
    console.log(`Saved ${entry.png}`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
