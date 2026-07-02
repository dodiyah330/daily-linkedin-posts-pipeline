#!/usr/bin/env node

/**
 * render-pdf.js — Combine already-rendered slide PNGs into a single PDF
 *
 * IMPORTANT: This script does NOT render HTML. It takes the finished PNG
 * files produced by render.js and stitches them into a multi-page PDF.
 * This guarantees the PDF matches the PNGs exactly.
 *
 * Usage: node render-pdf.js [DATE] [CAROUSEL_DIR]
 *   DATE         optional YYYY-MM-DD (defaults to today)
 *   CAROUSEL_DIR optional subdirectory, e.g. "carousel-branded"
 *
 * It looks for slide-01.png … slide-07.png in:
 *   output/DATE/CAROUSEL_DIR/
 *
 * And writes the PDF to the same directory.
 *
 * Strategy (in order):
 *   1. ImageMagick `magick` CLI  (fastest, no browser needed)
 *   2. Puppeteer page.pdf()      (renders a page of <img> tags pointing
 *      at the local PNGs with file:// protocol)
 */

const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

const BASE_DIR = path.resolve(__dirname);

// ── helpers ──────────────────────────────────────────────────────────

function findSlides(dir) {
  if (!fs.existsSync(dir)) {
    console.error('ERROR: output directory not found:', dir);
    process.exit(1);
  }
  const pngs = fs
    .readdirSync(dir)
    .filter(f => /^slide-\d+\.png$/.test(f))
    .sort()
    .map(f => path.join(dir, f));

  if (pngs.length === 0) {
    console.error('ERROR: No slide PNG files found in', dir);
    console.error('       Run render.js first to generate the PNGs.');
    process.exit(1);
  }
  return pngs;
}

function pdfName(dir, dateStr, carouselDir) {
  // Use carousel-YYYYMMDD.pdf as the filename
  const dateCompact = dateStr.replace(/-/g, '');
  return path.join(dir, `carousel-${dateCompact}.pdf`);
}

// ── Strategy 1: ImageMagick ──────────────────────────────────────────

function tryImageMagick(pngs, outPdf) {
  try {
    // Check if magick is available
    execSync('which magick', { stdio: 'pipe' });
  } catch {
    console.log('  magick not found, skipping ImageMagick strategy.');
    return false;
  }

  try {
    const cmd = `magick ${pngs.map(p => `"${p}"`).join(' ')} "${outPdf}"`;
    execSync(cmd, { stdio: 'pipe', timeout: 30000 });

    const stat = fs.statSync(outPdf);
    if (stat.size < 1000) {
      console.log('  magick produced a suspiciously small PDF, skipping.');
      fs.unlinkSync(outPdf);
      return false;
    }

    console.log(`  ✓ PDF created via ImageMagick (${Math.round(stat.size / 1024)} KB)`);
    return true;
  } catch (err) {
    console.log('  magick failed:', err.message);
    return false;
  }
}

// ── Strategy 2: Puppeteer ────────────────────────────────────────────

async function tryPuppeteer(pngs, outPdf) {
  let puppeteer;
  try {
    puppeteer = require('puppeteer');
  } catch {
    console.log('  puppeteer not found, skipping Puppeteer strategy.');
    return false;
  }

  try {
    // Build a simple HTML page where each slide is a full-page image.
    // Using base64-encoded images ensures no file:// permission issues.
    const slides = pngs.map(p => {
      const data = fs.readFileSync(p);
      const b64 = data.toString('base64');
      return `<div class="page"><img src="data:image/png;base64,${b64}"/></div>`;
    });

    const html = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"/>
<style>
  * { margin: 0; padding: 0; }
  @page { size: 1080px 1080px; margin: 0; }
  body { margin: 0; padding: 0; }
  .page { width: 1080px; height: 1080px; page-break-after: always; overflow: hidden; }
  .page:last-child { page-break-after: auto; }
  .page img { width: 1080px; height: 1080px; display: block; }
</style></head>
<body>${slides.join('\n')}</body></html>`;

    const browser = await puppeteer.launch({
      headless: 'shell',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'networkidle0' });
    await page.pdf({
      path: outPdf,
      width: '1080px',
      height: '1080px',
      printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });
    await browser.close();

    const stat = fs.statSync(outPdf);
    if (stat.size < 1000) {
      console.log('  Puppeteer produced a suspiciously small PDF, failing.');
      fs.unlinkSync(outPdf);
      return false;
    }

    console.log(`  ✓ PDF created via Puppeteer (${Math.round(stat.size / 1024)} KB)`);
    return true;
  } catch (err) {
    console.log('  Puppeteer PDF failed:', err.message);
    return false;
  }
}

// ── main ─────────────────────────────────────────────────────────────

async function main() {
  const dateStr = process.argv[2] || new Date().toISOString().slice(0, 10);
  const carouselDir = process.argv[3] || null;

  const outDir = carouselDir
    ? path.join(BASE_DIR, 'output', dateStr, carouselDir)
    : path.join(BASE_DIR, 'output', dateStr);

  const pngs = findSlides(outDir);
  const outPdf = pdfName(outDir, dateStr, carouselDir);

  const label = carouselDir ? `[${carouselDir}]` : '';
  console.log(`${label} Found ${pngs.length} slide PNG(s) in ${outDir}`);
  console.log(`${label} Generating PDF from PNGs…\n`);

  // Try strategies in order
  if (tryImageMagick(pngs, outPdf)) {
    console.log(`\nDone. PDF → ${outPdf}`);
    return;
  }

  if (await tryPuppeteer(pngs, outPdf)) {
    console.log(`\nDone. PDF → ${outPdf}`);
    return;
  }

  console.error('\nFATAL: All PDF strategies failed.');
  console.error('Install ImageMagick: brew install imagemagick');
  process.exit(1);
}

main().catch(err => {
  console.error('FATAL:', err.message);
  process.exit(1);
});
