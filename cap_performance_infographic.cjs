const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

(async () => {
  const dateCompact = process.argv[2] || new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const htmlPath = path.join(__dirname, 'linkedin-performance-infographic.html');
  const outputPath = path.join(__dirname, `linkedin-performance-infographic-${dateCompact}.png`);

  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
    ],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });
  await page.setContent(fs.readFileSync(htmlPath, 'utf8'), { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: outputPath, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
  await browser.close();
  console.log(`Performance infographic saved to ${outputPath}`);
})();
