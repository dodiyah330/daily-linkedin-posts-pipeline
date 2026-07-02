const puppeteer = require('puppeteer-core');
const path = require('path');

(async () => {
  const htmlPath = process.argv[2];
  const pdfPath = process.argv[3];

  if (!htmlPath || !pdfPath) {
    console.error("Usage: node print_paper.cjs <htmlPath> <pdfPath>");
    process.exit(1);
  }

  const absoluteHtmlPath = path.resolve(htmlPath);
  const absolutePdfPath = path.resolve(pdfPath);

  console.log(`Printing HTML to PDF...\nSource: ${absoluteHtmlPath}\nOutput: ${absolutePdfPath}`);

  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-web-security',
      '--disable-gpu'
    ]
  });

  const page = await browser.newPage();
  
  // Set viewport to A4 aspect ratio representation
  await page.setViewport({ width: 1200, height: 1600 });

  await page.setRequestInterception(true);
  page.on('request', req => {
    const url = req.url();
    if (url.includes('fonts.googleapis.com') || url.includes('fonts.gstatic.com')) {
      req.abort();
    } else {
      req.continue();
    }
  });

  await page.goto('file://' + absoluteHtmlPath, { waitUntil: 'domcontentloaded' });

  // Wait for web fonts to load
  await page.evaluate(() => document.fonts.ready);

  // Give a small buffer for page layout stabilization
  await page.evaluate(() => new Promise(r => setTimeout(r, 500)));

  await page.pdf({
    path: absolutePdfPath,
    format: 'A4',
    margin: {
      top: '15mm',
      right: '15mm',
      bottom: '15mm',
      left: '15mm'
    },
    printBackground: true
  });

  await browser.close();
  console.log(`✓ PDF printed successfully.`);
})();
