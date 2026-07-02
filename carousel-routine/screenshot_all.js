const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
const path = require('path');

const TEMP_DIR = '/Users/prithal/Documents/carousel-routine/temp/carousel-branded';
const DATE_STR = new Date().toISOString().slice(0,10);
const DATE = DATE_STR.replace(/-/g,'');
const OUTPUT_DIR = `/Users/prithal/Documents/carousel-routine/output/${DATE_STR}/carousel-branded`;

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files', '--disable-web-security'],
    protocolTimeout: 180000
  });

  // Screenshot carousel slides
  for (let i = 1; i <= 7; i++) {
    const slideNum = String(i).padStart(2, '0');
    const slidePath = path.join(TEMP_DIR, `slide-${slideNum}.html`);
    const outPath = path.join(OUTPUT_DIR, `slide-${slideNum}.png`);

    const page = await browser.newPage();
    await page.setDefaultNavigationTimeout(60000);
    await page.setViewport({ width: 1080, height: 1080 });
    await page.goto(`file://${slidePath}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await new Promise(r => setTimeout(r, 1500));
    try {
      await page.screenshot({ path: outPath, clip: {x:0, y:0, width:1080, height:1080}, timeout: 60000 });
      console.log(`✓ slide-${slideNum}.png`);
    } catch(e) {
      console.error(`✗ slide-${slideNum}: ${e.message}`);
    }
    await page.close();
  }

  // Infographic via local HTTP server (has no external assets to load)
  const infPage = await browser.newPage();
  await infPage.setDefaultNavigationTimeout(60000);
  await infPage.setViewport({ width: 1080, height: 1080 });
  const infHTML = fs.readFileSync(process.env.HOME + '/Desktop/linkedin-infographic.html', 'utf8');
  const infServer = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html; charset=utf-8'});
    res.end(infHTML);
  });
  await new Promise(r => infServer.listen(8780, r));
  await infPage.goto('http://localhost:8780', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1500));
  try {
    await infPage.screenshot({ path: `/tmp/linkedin-infographic-${DATE}.png`, clip: {x:0,y:0,width:1080,height:1080}, timeout: 60000 });
    console.log(`✓ linkedin-infographic-${DATE}.png`);
  } catch(e) {
    console.error(`✗ infographic: ${e.message}`);
  }
  infServer.close();
  await infPage.close();

  await browser.close();
  console.log('ALL_DONE');
})();
