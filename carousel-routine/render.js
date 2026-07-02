#!/usr/bin/env node

/**
 * render.js — Puppeteer HTML → PNG renderer for carousel-routine
 *
 * Usage: node render.js [DATE] [CAROUSEL_DIR]
 *   DATE         optional YYYY-MM-DD (defaults to today)
 *   CAROUSEL_DIR optional subdirectory, e.g. "carousel-1"
 *                - reads  from temp/CAROUSEL_DIR/slide-*.html
 *                - writes to output/DATE/CAROUSEL_DIR/slide-*.png
 *                If omitted, reads temp/ and writes output/DATE/
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const BASE_DIR = path.resolve(__dirname);

async function render(dateStr, carouselDir) {
  const date = dateStr || new Date().toISOString().slice(0, 10);

  const tempDir  = carouselDir
    ? path.join(BASE_DIR, 'temp', carouselDir)
    : path.join(BASE_DIR, 'temp');

  const outDir = carouselDir
    ? path.join(BASE_DIR, 'output', date, carouselDir)
    : path.join(BASE_DIR, 'output', date);

  fs.mkdirSync(outDir, { recursive: true });

  if (!fs.existsSync(tempDir)) {
    console.error('ERROR: temp directory not found:', tempDir);
    process.exit(1);
  }

  const htmlFiles = fs
    .readdirSync(tempDir)
    .filter(f => /^slide-\d+\.html$/.test(f))
    .sort()
    .map(f => path.join(tempDir, f));

  if (htmlFiles.length === 0) {
    console.error('ERROR: No slide HTML files found in', tempDir);
    process.exit(1);
  }

  const label = carouselDir ? `[${carouselDir}]` : '';
  console.log(`${label} Found ${htmlFiles.length} slide(s). Launching headless browser…`);

  const browser = await puppeteer.launch({
    headless: 'shell',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--font-render-hinting=none',
      '--disable-web-security',
      '--disable-gpu',
    ],
  });

  const page = await browser.newPage();

  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });

  const results = [];

  for (const htmlFile of htmlFiles) {
    const baseName = path.basename(htmlFile, '.html');
    const outFile  = path.join(outDir, `${baseName}.png`);

    await page.goto('file://' + encodeURI(htmlFile), {
      waitUntil: 'domcontentloaded',
      timeout: 25000,
    });

    // Wait for web fonts
    await page.evaluate(() => document.fonts.ready);

    // Extra buffer for JS-rendered content (Chart.js, Rough.js, etc.)
    await page.evaluate(() => new Promise(r => setTimeout(r, 300)));

    await page.screenshot({
      path: outFile,
      type: 'png',
      clip: { x: 0, y: 0, width: 1080, height: 1080 },
      omitBackground: false,
    });

    console.log(`  ✓ ${label} ${baseName}.png`);
    results.push(outFile);
  }

  await browser.close();

  console.log(`\nDone. ${results.length} slide(s) → output/${date}/${carouselDir || ''}`);
  return results;
}

const dateArg    = process.argv[2] || null;
const carouselArg = process.argv[3] || null;

render(dateArg, carouselArg).catch(err => {
  console.error('FATAL:', err.message);
  process.exit(1);
});
