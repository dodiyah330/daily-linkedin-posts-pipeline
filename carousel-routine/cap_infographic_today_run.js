const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log('Starting infographic screenshot...');
  const browser = await puppeteer.launch({
    headless: 'shell',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });
  
  const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html; charset=utf-8'});
    const htmlPath = '/Users/prithal/3d website/linkedin-automation-routine/linkedin-infographic.html';
    res.end(fs.readFileSync(htmlPath));
  });
  
  await new Promise(r => server.listen(8766, r));
  console.log('Local server listening on 8766');
  
  await page.goto('http://localhost:8766', { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  
  const d = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const outputPath = `/Users/prithal/3d website/linkedin-automation-routine/linkedin-infographic-${d}.png`;
  await page.screenshot({ path: outputPath, clip: { x:0, y:0, width:1080, height:1080 } });
  console.log(`Screenshot saved to ${outputPath}`);
  
  server.close();
  await browser.close();
  console.log('Browser closed, server stopped.');
})();
