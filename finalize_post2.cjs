const puppeteer = require('puppeteer-core');

async function clickNativelyShadow(page, finderFn) {
  try {
    const handle = await page.evaluateHandle((finder) => {
      const fn = new Function('return ' + finder)();
      function findInShadow(root) {
        if (!root) return null;
        const res = fn(root);
        if (res) return res;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findInShadow(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      return findInShadow(document.body);
    }, finderFn.toString());

    const el = handle.asElement();
    if (el) {
      await page.evaluate(e => e.focus(), el);
      await el.click();
      await page.evaluate(e => e.click(), el);
      await el.dispose();
      return true;
    }
    return false;
  } catch (err) {
    console.error("clickNativelyShadow error:", err);
    return false;
  }
}

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
    
    // Set larger viewport to see all controls
    console.log("Setting viewport to 1280x1200...");
    await page.setViewport({ width: 1280, height: 1200 });
    await new Promise(r => setTimeout(r, 1000));
    
    // Screenshot before clicking
    await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/pre_click_schedule.png' });
    console.log("Pre-click screenshot saved to pre_click_schedule.png");

    console.log("Locating and clicking final 'Schedule' button...");
    const clicked = await clickNativelyShadow(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(
        b => b.innerText && b.innerText.trim() === 'Schedule'
      );
    });
    
    if (clicked) {
      console.log("✓ 'Schedule' button clicked successfully.");
      await new Promise(r => setTimeout(r, 6000)); // wait for submit
      await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/post_click_schedule.png' });
      console.log("Post-click screenshot saved to post_click_schedule.png");
      process.exit(0);
    } else {
      console.error("✗ Could not find 'Schedule' button in the page/shadow DOM.");
      process.exit(1);
    }
  } catch (err) {
    console.error("Error finalizing post 2:", err);
    process.exit(1);
  }
})();
