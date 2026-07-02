const puppeteer = require('puppeteer-core');

(async () => {
  try {
    const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com/feed'));
    if (!page) {
      console.error("LinkedIn feed page not found!");
      process.exit(1);
    }
    await page.bringToFront();
    await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/current_state.png' });
    console.log("Screenshot saved to current_state.png");
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();
