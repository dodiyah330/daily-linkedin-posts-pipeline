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
      // Focus element
      await page.evaluate(e => e.focus(), el);
      // Native click
      await el.click();
      // Fallback click
      await page.evaluate(e => e.click(), el).catch(() => {});
      await el.dispose();
      return true;
    }
    return false;
  } catch (err) {
    console.error("clickNativelyShadow error:", err);
    return false;
  }
}

const correctedText = `Anthropic filing for an IPO is not the triumph it looks like.

For a company that has positioned itself as the safety-first, mission-driven counterweight to OpenAI, filing for an public offering represents a hard pivot into the public market's quarterly growth expectations.

Anthropic is raising capital, but they're also entering a phase where safe, slow, safety-centric AI research becomes a tough sell to institutional public market investors looking for immediate ARR growth.

Founders Wing sees something different worth talking about: this IPO is a defensive play. As compute costs rise and private capital markets get more selective, going public is the only way to lock in the massive, sustained funding needed to compete with OpenAI and Google.

It's not a victory lap; it's a resource grab in a race where the burn rate is measured in billions.

If Anthropic goes public, they will have to disclose their actual revenue, compute expenditures, and customer concentration. We will finally see the real unit economics of safety-first foundation models.

Will safety-centric positioning survive public market scrutiny? Or will the demands of retail and institutional investors force Anthropic to prioritize product speed over guardrails?`;

(async () => {
  const wsEndpoint = process.argv[2];
  try {
    const browser = await puppeteer.connect({ browserWSEndpoint: wsEndpoint });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com'));
    
    // Set viewport height 1200
    await page.setViewport({ width: 1280, height: 1200 });

    const editorEl = await getElementShadow(page, '.ql-editor, [contenteditable="true"]');
    if (!editorEl) throw new Error("Editor not found!");

    console.log("Clearing text editor...");
    await editorEl.focus();
    await page.evaluate((el) => {
      el.innerHTML = '<p><br></p>';
    }, editorEl);
    await editorEl.dispose();

    console.log("Typing corrected text...");
    await page.keyboard.type(correctedText);
    await new Promise(r => setTimeout(r, 2000));

    console.log("Taking screenshot before clicking Schedule...");
    await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/pre_save_anthropic.png' });

    console.log("Clicking 'Schedule' button with native click...");
    const clicked = await clickNativelyShadow(page, (root) => {
      const els = Array.from(root.querySelectorAll('button, div, span, [role="button"]'));
      return els.find(b => {
        const txt = b.innerText ? b.innerText.trim() : '';
        const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0;
        return (txt === 'Schedule' || b.getAttribute('aria-label') === 'Schedule') && isVisible;
      });
    });
    console.log("Click result:", clicked);

    console.log("Waiting 6 seconds for modal to close...");
    await new Promise(r => setTimeout(r, 6000));

    console.log("Taking screenshot after Schedule click...");
    await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/post_save_anthropic.png' });
    
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();
