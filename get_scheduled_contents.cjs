const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

(async () => {
  try {
    const tmpDir = '/var/folders/c7/crm35d6s6t18fsxlt7ylmf580000gn/T';
    const dirs = fs.readdirSync(tmpDir).filter(name => name.startsWith('agent-browser-chrome-'));
    if (dirs.length === 0) throw new Error('No agent-browser-chrome dirs found');
    const latestDir = dirs.map(name => {
      const fullPath = path.join(tmpDir, name);
      return { path: fullPath, mtime: fs.statSync(fullPath).mtimeMs };
    }).sort((a, b) => b.mtime - a.mtime)[0].path;
    const portFile = path.join(latestDir, 'DevToolsActivePort');
    const content = fs.readFileSync(portFile, 'utf8');
    const port = content.split('\n')[0].trim();
    
    console.log(`Connecting to browser on port ${port}...`);
    const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com/feed'));
    if (!page) throw new Error("Feed page not found");
    await page.bringToFront();
    
    console.log("Clicking 12:15 AM button...");
    await page.evaluate(() => {
      function findBtn(root) {
        if (!root) return null;
        const btn = Array.from(root.querySelectorAll('button')).find(
          b => b.getAttribute('aria-label')?.includes('Thu June 11, 2026 at 12:15 AM')
        );
        if (btn) return btn;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findBtn(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      const b = findBtn(document.body);
      if (b) b.click();
    });
    await new Promise(r => setTimeout(r, 4000));
    
    console.log("Taking screenshot of detail view...");
    const screenshotPath = '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/preview_12_15_am.png';
    await page.screenshot({ path: screenshotPath });
    console.log(`Screenshot saved to: ${screenshotPath}`);

    const detailText = await page.evaluate(() => {
      // Dump text of elements within the modal
      function findText(root) {
        if (!root) return null;
        // Let's print out all divs with text
        const modal = root.querySelector('.artdeco-modal, [role="dialog"]');
        if (modal) {
          // Let's get the text of the actual post description/body
          const body = modal.querySelector('.feed-shared-update-v2__description, .update-components-text, p, span');
          return modal.innerText;
        }
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findText(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      return findText(document.body);
    });
    
    console.log("=== DETAIL TEXT FOR 12:15 AM ===");
    console.log(detailText);
    console.log("================================");
    
    // Click Back
    await page.evaluate(() => {
      function findBack(root) {
        if (!root) return null;
        const btn = Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Back'
        );
        if (btn) return btn;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findBack(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      const b = findBack(document.body);
      if (b) b.click();
    });
    await new Promise(r => setTimeout(r, 2000));
    
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();
