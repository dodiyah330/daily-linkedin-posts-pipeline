const puppeteer = require('puppeteer');
(async () => {
  const [,, url, out] = process.argv;
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 630 });
  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
  } catch(e) {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  }
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: out });
  console.log('Saved:', out);
  await browser.close();
})();
