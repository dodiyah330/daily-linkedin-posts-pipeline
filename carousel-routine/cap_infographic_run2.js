const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });
  const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end(fs.readFileSync(process.env.HOME + '/Desktop/linkedin-infographic.html'));
  });
  await new Promise(r => server.listen(8766, r));
  await page.goto('http://localhost:8766', { waitUntil: 'networkidle0' });
  const d = new Date().toISOString().slice(0,10).replace(/-/g,'');
  await page.screenshot({ path: `/tmp/linkedin-infographic-${d}.png`, clip:{x:0,y:0,width:1080,height:1080} });
  server.close();
  await browser.close();
  console.log('Screenshot saved: /tmp/linkedin-infographic-' + d + '.png');
})();
