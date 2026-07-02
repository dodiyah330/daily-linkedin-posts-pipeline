const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });
  const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end(fs.readFileSync(process.env.HOME + '/Desktop/linkedin-infographic.html'));
  });
  await new Promise(r => server.listen(8768, r));
  await page.goto('http://localhost:8768', { waitUntil: 'networkidle0' });
  const d = new Date().toISOString().slice(0,10).replace(/-/g,'');
  const outPath = `/tmp/linkedin-infographic-${d}.png`;
  await page.screenshot({ path: outPath, clip:{x:0,y:0,width:1080,height:1080} });
  server.close();
  await browser.close();
  console.log('Saved:', outPath);
})();
