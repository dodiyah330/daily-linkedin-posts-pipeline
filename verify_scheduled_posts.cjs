const puppeteer = require('puppeteer-core');

async function getElementShadow(page, selector) {
  const handle = await page.evaluateHandle((sel) => {
    function findEl(root) {
      if (!root) return null;
      const el = root.querySelector(sel);
      if (el) return el;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = findEl(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return findEl(document.body);
  }, selector);
  return handle.asElement();
}

async function waitForSelectorShadow(page, selector, timeout = 15000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const el = await getElementShadow(page, selector);
    if (el) {
      await el.dispose();
      return true;
    }
    await new Promise(r => setTimeout(r, 500));
  }
  throw new Error(`Timeout waiting for shadow selector: ${selector}`);
}

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
    console.log("Connecting to browser...");
    const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com/feed'));
    if (!page) {
      console.error("LinkedIn feed page not found!");
      process.exit(1);
    }
    await page.bringToFront();
    await page.setViewport({ width: 1280, height: 1200 });

    console.log("Navigating to feed home page...");
    try {
      await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 15000 });
    } catch (e) {
      console.log("Navigation timeout/error, continuing anyway:", e.message);
    }
    await new Promise(r => setTimeout(r, 6000));

    console.log("Checking and closing any open composers first...");
    await page.evaluate(() => {
      function findDismissBtn(root) {
        if (!root) return null;
        const btn = Array.from(root.querySelectorAll('button')).find(
          b => {
            const label = b.getAttribute('aria-label') || '';
            const txt = b.innerText || '';
            const cls = b.className || '';
            return label.includes('Dismiss') || 
                   txt.includes('Dismiss') ||
                   label.toLowerCase() === 'close' ||
                   cls.includes('close-button');
          }
        );
        if (btn) return btn;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findDismissBtn(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      const dismissBtn = findDismissBtn(document.body);
      if (dismissBtn) dismissBtn.click();
    });
    await new Promise(r => setTimeout(r, 2000));

    console.log("Clicking 'Start a post'...");
    const clickStartPost = await clickNativelyShadow(page, (root) => {
      return Array.from(root.querySelectorAll('*')).find(
        el => (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || el.getAttribute('aria-label') === 'Start a post') &&
              el.innerText && el.innerText.trim().includes('Start a post')
      );
    });
    if (!clickStartPost) throw new Error("Could not find 'Start a post' button");

    const editorSelector = '.ql-editor, [contenteditable="true"]';
    await waitForSelectorShadow(page, editorSelector, 15000);
    await new Promise(r => setTimeout(r, 1000));

    console.log("Opening Schedule Settings...");
    const clickedScheduleIcon = await clickNativelyShadow(page, (root) => {
      const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
      const container = modal || root;
      const buttons = Array.from(container.querySelectorAll('button'));
      const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
      if (postBtn && postBtn.previousElementSibling) {
        return postBtn.previousElementSibling;
      }
      return buttons.find(b => {
        const label = b.getAttribute('aria-label') || '';
        return label.includes('Schedule');
      });
    });
    if (!clickedScheduleIcon) throw new Error("Could not find Schedule icon");
    await new Promise(r => setTimeout(r, 3000));

    console.log("Clicking 'View all scheduled posts'...");
    const clickedViewAll = await clickNativelyShadow(page, (root) => {
      const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
      const container = modal || root;
      return Array.from(container.querySelectorAll('a, button, span')).find(
        el => el.innerText && el.innerText.includes('View all scheduled posts')
      );
    });
    if (!clickedViewAll) throw new Error("Could not find 'View all scheduled posts' link");
    await new Promise(r => setTimeout(r, 6000));

    console.log("Taking screenshot of scheduled posts page...");
    await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/all_scheduled_posts.png' });
    console.log("✓ Screenshot saved to all_scheduled_posts.png");
    process.exit(0);

  } catch (err) {
    console.error("Verification Exception:", err);
    process.exit(1);
  }
})();
