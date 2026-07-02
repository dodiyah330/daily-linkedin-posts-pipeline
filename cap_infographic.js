const puppeteer = require('puppeteer-core');
const http = require('http');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log("Launching browser to screenshot infographic...");
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
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 2 });
  
  const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end(fs.readFileSync(path.resolve(__dirname, './linkedin-infographic.html')));
  });
  
  await new Promise(r => server.listen(8766, r));
  console.log("Server listening on port 8766");
  
  await page.goto('http://localhost:8766', { waitUntil: 'networkidle0' });
  
  const d = new Date().toISOString().slice(0,10).replace(/-/g,'');
  const outPath = path.resolve(__dirname, `./linkedin-infographic-${d}.png`);
  
  await page.screenshot({ 
    path: outPath, 
    clip: { x: 0, y: 0, width: 1080, height: 1080 } 
  });
  
  console.log(`Screenshot saved to ${outPath}`);
  
  server.close();
  await browser.close();
  console.log("Infographic capture complete.");
})();
