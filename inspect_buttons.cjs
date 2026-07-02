const puppeteer = require('puppeteer-core');
const fs = require('fs');

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

    const buttons = await page.evaluate(() => {
      const found = [];
      function search(root) {
        if (!root) return;
        const els = root.querySelectorAll('button, [role="button"]');
        for (const el of els) {
          const className = el.className || '';
          if (className.includes('msg-') || className.includes('msg-overlay') || el.id.includes('msg-') || el.id.includes('attachment-trigger')) {
            continue; // Skip messaging
          }
          // Filter to elements inside share box / modal
          let isModal = false;
          let p = el;
          while (p) {
            const classStr = p.className ? (typeof p.className === 'string' ? p.className : (p.className.baseVal || '')) : '';
            const tag = p.tagName || '';
            if (tag === 'DIALOG' || classStr.includes('modal') || classStr.includes('composer') || classStr.includes('share-box') || classStr.includes('editor')) {
              isModal = true;
              break;
            }
            p = p.parentNode || p.host;
          }
          if (isModal) {
            found.push({
              tag: el.tagName,
              innerText: el.innerText ? el.innerText.trim() : '',
              ariaLabel: el.getAttribute('aria-label') || '',
              className: className,
              id: el.id || ''
            });
          }
        }
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) search(node.shadowRoot);
        }
      }
      search(document.body);
      return found;
    });

    console.log("Filtered buttons in modal:", buttons);
    fs.writeFileSync('/Users/prithal/3d website/linkedin-automation-routine/modal_buttons.json', JSON.stringify(buttons, null, 2));
    console.log("Saved to modal_buttons.json");
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();
