const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log('Starting infographic screenshot using puppeteer-core (setContent)...');
  const browser = await puppeteer.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--use-mock-keychain',
      '--password-store=basic',
      '--disable-extensions',
      '--disable-component-update',
      '--no-default-browser-check'
    ]
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });
  
  const htmlPath = path.join(__dirname, 'linkedin-infographic.html');
  const htmlContent = fs.readFileSync(htmlPath, 'utf8');
  await page.setContent(htmlContent, { waitUntil: 'domcontentloaded' });
  
  // Wait for fonts/layout
  await page.evaluate(() => document.fonts.ready);
  
  const d = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const outputPath = path.join(__dirname, `linkedin-infographic-${d}.png`);
  await page.screenshot({ path: outputPath, clip: { x:0, y:0, width:1080, height:1080 } });
  console.log(`Screenshot saved to ${outputPath}`);
  
  await browser.close();
  console.log('Browser closed.');
})();
