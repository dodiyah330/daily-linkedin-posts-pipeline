const puppeteer = require('puppeteer-core');
const fs = require('fs');

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

async function fillFieldShadow(page, selector, value) {
  const el = await getElementShadow(page, selector);
  if (!el) throw new Error(`Could not find element to fill: ${selector}`);
  
  await page.evaluate((input) => {
    input.focus();
    input.select();
  }, el);
  
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.press('Backspace');
  
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.type(value);
  await page.keyboard.press('Enter');
  await new Promise(r => setTimeout(r, 200));
  await page.keyboard.press('Escape');
  await new Promise(r => setTimeout(r, 200));
  await page.keyboard.press('Tab');
  await el.dispose();
  await new Promise(r => setTimeout(r, 1000));
}

async function fillTimeComboboxShadow(page, selector, value) {
  const el = await getElementShadow(page, selector);
  if (!el) throw new Error(`Could not find combobox element to fill: ${selector}`);
  
  await page.evaluate((input) => {
    input.focus();
    input.select();
  }, el);
  
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.press('Backspace');
  
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.type(value);
  console.log(`Typed ${value} into time combobox, waiting for suggestions...`);
  await new Promise(r => setTimeout(r, 1500));
  
  await page.keyboard.press('ArrowDown');
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.press('Enter');
  await el.dispose();
  await new Promise(r => setTimeout(r, 1000));
}

(async () => {
  const caption = fs.readFileSync('/Users/prithal/3d website/linkedin-automation-routine/post3_caption.txt', 'utf8').trim();
  const date = '06/09/2026';
  const time = '8:30 AM';
  const prefix = '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/post_regular';

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

    const currentUrl = page.url();
    if (!currentUrl.includes('linkedin.com/feed')) {
      console.log("Navigating to feed home page to start clean...");
      try {
        await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 15000 });
      } catch (err) {
        console.log("Navigation timeout/error, continuing anyway:", err.message);
      }
    } else {
      console.log("Already on LinkedIn feed, skipping navigation...");
    }
    await new Promise(r => setTimeout(r, 3000));

    console.log("Checking and closing any open composers first...");
    const closedComposer = await page.evaluate(() => {
      function findEl(root, sel) {
        if (!root) return null;
        const el = root.querySelector(sel);
        if (el) return el;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findEl(node.shadowRoot, sel);
            if (found) return found;
          }
        }
        return null;
      }
      const hasEditor = !!findEl(document.body, '.ql-editor');
      if (!hasEditor) return "no-composer-found";

      function findDismissBtn(root) {
        if (!root) return null;
        const btn = Array.from(root.querySelectorAll('button')).find(
          b => (b.ariaLabel && b.ariaLabel.includes('Dismiss')) || 
               (b.innerText && b.innerText.includes('Dismiss')) ||
               (b.ariaLabel && b.ariaLabel.toLowerCase() === 'close') ||
               (b.className && b.className.includes('close-button'))
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
      if (dismissBtn) {
        dismissBtn.click();
        return "clicked-dismiss";
      }
      return "composer-found-but-no-dismiss-btn";
    });
    console.log("Composer check result:", closedComposer);
    if (closedComposer === "clicked-dismiss") {
      await new Promise(r => setTimeout(r, 2000));
    }

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
    
    console.log("Filling post caption text...");
    const editorEl = await getElementShadow(page, editorSelector);
    if (!editorEl) throw new Error("Editor not found");

    console.log("Focusing and clearing editor...");
    await page.evaluate((el) => {
      el.focus();
      document.execCommand('selectAll', false, null);
      document.execCommand('delete', false, null);
    }, editorEl);

    await new Promise(r => setTimeout(r, 1000));
    console.log("Typing text...");
    await page.keyboard.type(caption);
    await new Promise(r => setTimeout(r, 2000));
    await editorEl.dispose();

    // Verify caption is populated
    const editorText = await page.evaluate(() => {
      function findText(root) {
        const el = root.querySelector('.ql-editor');
        if (el) return el.innerText.trim();
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const txt = findText(node.shadowRoot);
            if (txt) return txt;
          }
        }
        return null;
      }
      return findText(document.body);
    });
    console.log("Caption text in editor (length):", editorText ? editorText.length : 0);
    if (!editorText || editorText.length < 5) {
      throw new Error("Validation Failed: Post caption in editor is blank or too short!");
    }

    await page.screenshot({ path: `${prefix}_draft_composer.png` });
    console.log(`Saved screenshot to: ${prefix}_draft_composer.png`);

    console.log("Opening Schedule Settings...");
    const clickedScheduleIcon = await clickNativelyShadow(page, (root) => {
      const buttons = Array.from(root.querySelectorAll('button'));
      const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
      if (postBtn && postBtn.previousElementSibling) {
        return postBtn.previousElementSibling;
      }
      return buttons.find(b => b.ariaLabel && b.ariaLabel.includes('Schedule'));
    });
    if (!clickedScheduleIcon) throw new Error("Could not find Schedule icon");
    await new Promise(r => setTimeout(r, 3000));

    console.log(`Setting schedule: Date=${date}, Time=${time}`);
    await fillFieldShadow(page, 'input[placeholder*="Date"], input[aria-label*="date"], input[id*="date"]', date);
    await fillTimeComboboxShadow(page, 'input[placeholder*="Time"], input[aria-label*="time"], input[id*="time"], input[role="combobox"]', time);

    await page.screenshot({ path: `${prefix}_schedule_settings.png` });
    console.log(`Saved screenshot to: ${prefix}_schedule_settings.png`);

    console.log("Saving schedule settings (clicking Next)...");
    const clickedNext = await clickNativelyShadow(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(
        b => b.innerText && b.innerText.trim() === 'Next'
      );
    });
    if (!clickedNext) throw new Error("Could not click Next in schedule modal");
    await new Promise(r => setTimeout(r, 3000));

    await page.screenshot({ path: `${prefix}_final_draft.png` });
    console.log(`Saved screenshot to: ${prefix}_final_draft.png`);

    console.log("Clicking final 'Schedule' button...");
    const clickedScheduleFinal = await clickNativelyShadow(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(
        b => b.innerText && b.innerText.trim() === 'Schedule'
      );
    });
    if (!clickedScheduleFinal) throw new Error("Could not find final 'Schedule' button");
    
    console.log("Success! Waiting 6s for scheduling process to complete...");
    await new Promise(r => setTimeout(r, 6000));

    const isClosed = await page.evaluate(() => {
      function findEl(root, sel) {
        if (!root) return null;
        const el = root.querySelector(sel);
        if (el) return el;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findEl(node.shadowRoot, sel);
            if (found) return found;
          }
        }
        return null;
      }
      return !findEl(document.body, '.ql-editor');
    });
    if (!isClosed) throw new Error("composer editor did not close. Scheduling might have failed!");
    
    console.log("✓ Successfully scheduled post 3!");
    process.exit(0);

  } catch (err) {
    console.error("Automator Exception:", err);
    try {
      const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' });
      const pages = await browser.pages();
      const page = pages.find(p => p.url().includes('linkedin.com/feed'));
      if (page) {
        await page.screenshot({ path: `${prefix}_error.png` });
        console.log(`Saved error screenshot to ${prefix}_error.png`);
      }
    } catch (e) {
      console.error("Failed to capture error screenshot:", e);
    }
    process.exit(1);
  }
})();
