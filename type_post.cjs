const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function getElementShadow(page, selector) {
  const handle = await page.evaluateHandle((sel) => {
    function findEl(root, selectorText) {
      if (!root) return null;
      const el = root.querySelector(selectorText);
      if (el) return el;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = findEl(node.shadowRoot, selectorText);
          if (found) return found;
        }
      }
      return null;
    }
    return findEl(document.body, sel);
  }, selector);
  return handle.asElement();
}

(async () => {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error("Usage: node type_post.cjs <filePath>");
    process.exit(1);
  }

  const text = fs.readFileSync(filePath, 'utf8');

  console.log("Connecting to browser on http://127.0.0.1:9222...");
  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' });
  
  const pages = await browser.pages();
  const page = pages.find(p => p.url().includes('linkedin.com/feed'));
  if (!page) {
    console.error("LinkedIn feed page not found!");
    process.exit(1);
  }

  console.log("Bringing page to front...");
  await page.bringToFront();

  console.log("Finding editor in shadow DOM...");
  const editorEl = await getElementShadow(page, '.ql-editor, [contenteditable="true"]');
  if (!editorEl) {
    console.error("Editor element not found in shadow DOM!");
    process.exit(1);
  }

  console.log("Focusing and clearing editor...");
  await page.evaluate(e => {
    e.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
  }, editorEl);

  console.log("Typing text...");
  await page.keyboard.type(text);

  console.log("✓ Done typing!");
  process.exit(0);
})();
