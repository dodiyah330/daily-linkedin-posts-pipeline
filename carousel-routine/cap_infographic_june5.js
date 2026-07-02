const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');

(async () => {
  console.log('Starting June 5 infographic screenshot...');
  const browser = await puppeteer.launch({
    headless: 'shell',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });
  
  const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html; charset=utf-8'});
    res.end(fs.readFileSync('/Users/prithal/3d website/linkedin-automation-routine/linkedin-infographic.html'));
  });
  
  await new Promise(r => server.listen(8766, r));
  console.log('Local server listening on 8766');
  
  await page.goto('http://localhost:8766', { waitUntil: 'domcontentloaded' });
  // Wait for fonts to load
  await page.evaluate(() => document.fonts.ready);
  // Additional wait
  await page.evaluate(() => new Promise(r => setTimeout(r, 500)));
  
  const outputPath = '/Users/prithal/3d website/linkedin-automation-routine/linkedin-infographic-20260605.png';
  await page.screenshot({ path: outputPath, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
  console.log(`Screenshot saved to ${outputPath}`);
  
  server.close();
  await browser.close();
  console.log('Browser closed, server stopped.');
})();
