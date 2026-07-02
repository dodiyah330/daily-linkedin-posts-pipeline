#!/usr/bin/env node
/**
 * capture_source.js — pull REAL images from a product/source page for brand-story carousels.
 * Headless puppeteer (already installed in carousel-routine). No external browser MCP needed.
 *
 * Usage: node capture_source.js <SOURCE_URL> <ASSETS_DIR>
 * Produces in ASSETS_DIR:
 *   hero.png       — the page's og:image / twitter:image (designed social card, if present)
 *   shot-hero.png  — real screenshot of the hero (top of page)
 *   shot-2.png     — real screenshot after scrolling (product/feature section)
 *   logo.png       — brand logo mark via unavatar.io (Clearbit's free API is discontinued)
 *
 * Render these framed in a browser window (see branded-carousel "Browser-window screenshot
 * treatment"), never full-bleed — raw screenshots carry the source site's own headings.
 */
const puppeteer = require(require('path').join(__dirname, 'node_modules', 'puppeteer'));
const https = require('https');
const fs = require('fs');
const path = require('path');

function download(url, dest) {
  return new Promise((resolve) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (r) => {
      if (r.statusCode >= 300 && r.statusCode < 400 && r.headers.location) {
        return download(r.headers.location, dest).then(resolve);
      }
      if (r.statusCode !== 200) { resolve(false); return; }
      const f = fs.createWriteStream(dest);
      r.pipe(f);
      f.on('finish', () => { f.close(); resolve(fs.statSync(dest).size > 5000); });
    }).on('error', () => resolve(false));
  });
}

(async () => {
  const url = process.argv[2];
  const dir = process.argv[3];
  if (!url || !dir) { console.error('usage: node capture_source.js <url> <assets_dir>'); process.exit(1); }
  fs.mkdirSync(dir, { recursive: true });

  const browser = await puppeteer.launch({ headless: 'shell', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 860, deviceScaleFactor: 1 });
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 45000 });
    await new Promise((r) => setTimeout(r, 2500));

    const og = await page.evaluate(() => {
      const m = document.querySelector('meta[property="og:image"]') || document.querySelector('meta[name="twitter:image"]');
      return m ? m.content : '';
    });
    if (og) await download(og, path.join(dir, 'hero.png'));

    await page.screenshot({ path: path.join(dir, 'shot-hero.png') });
    await page.evaluate(() => window.scrollBy(0, 760));
    await new Promise((r) => setTimeout(r, 1500));
    await page.screenshot({ path: path.join(dir, 'shot-2.png') });

    // logo mark via unavatar (derive registrable domain from URL host)
    try {
      const host = new URL(url).hostname.replace(/^www\./, '');
      await download(`https://unavatar.io/${host}`, path.join(dir, 'logo.png'));
    } catch (e) { /* ignore */ }

    const report = ['hero.png', 'shot-hero.png', 'shot-2.png', 'logo.png'].map((f) => {
      const p = path.join(dir, f);
      return fs.existsSync(p) ? `${f}:${fs.statSync(p).size}b` : `${f}:MISSING`;
    });
    console.log('captured', report.join(' '));
  } catch (e) {
    console.error('capture error:', e.message);
    process.exitCode = 2;
  } finally {
    await browser.close();
  }
})();
