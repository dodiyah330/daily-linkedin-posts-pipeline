#!/usr/bin/env node
/** Delete one scheduled post by date/time slot, e.g. node delete_scheduled_slot.cjs "July 6" "9:00 AM" */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const monthDay = process.argv[2] || 'July 6';
const time = process.argv[3] || '9:00 AM';

function findPort() {
  const tmpDir = os.tmpdir();
  const dirs = fs.readdirSync(tmpDir).filter(n =>
    n.startsWith('agent-browser-chrome-') || n.startsWith('agent-browser-profile-')
  );
  const latest = dirs.map(name => ({
    path: path.join(tmpDir, name),
    mtime: fs.statSync(path.join(tmpDir, name)).mtimeMs,
  })).sort((a, b) => b.mtime - a.mtime)[0].path;
  return fs.readFileSync(path.join(latest, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
}

async function click(page, finderFn) {
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
          const f = findInShadow(node.shadowRoot);
          if (f) return f;
        }
      }
      return null;
    }
    return findInShadow(document.body);
  }, finderFn.toString());
  const el = handle.asElement();
  if (!el) return false;
  await page.evaluate(e => { e.focus(); e.click(); }, el);
  await el.dispose();
  return true;
}

async function openModal(page) {
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 3000));
  await click(page, root => Array.from(root.querySelectorAll('*')).find(el => el.innerText && el.innerText.includes('Start a post')));
  await new Promise(r => setTimeout(r, 2500));
  await click(page, root => {
    const btns = Array.from(root.querySelectorAll('button'));
    const postBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Post');
    return (postBtn && postBtn.previousElementSibling) || btns.find(b => (b.getAttribute('aria-label') || '').includes('Schedule'));
  });
  await new Promise(r => setTimeout(r, 2500));
  await click(page, root => Array.from(root.querySelectorAll('button, a')).find(el => (el.innerText || '').toLowerCase().includes('view all scheduled posts')));
  await new Promise(r => setTimeout(r, 5000));
}

(async () => {
  const port = findPort();
  const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
  const page = (await browser.pages()).find(p => p.url().includes('linkedin.com'));
  await page.bringToFront();
  await openModal(page);

  const shortMonth = monthDay.replace('July', 'Jul').replace('June', 'Jun');
  const ok = await click(page, root => {
    const btns = Array.from(root.querySelectorAll('button'));
    return btns.find(b => {
      const a = b.getAttribute('aria-label') || '';
      return a.includes('Actions menu for scheduled post') &&
        (a.includes(monthDay) || a.includes(shortMonth)) &&
        a.includes(time);
    });
  });
  if (!ok) {
    console.log(`No post found for ${monthDay} ${time}`);
    process.exit(0);
  }
  await new Promise(r => setTimeout(r, 2000));
  await click(page, root => Array.from(root.querySelectorAll('button, div, span')).find(b => b.innerText && b.innerText.trim() === 'Delete post'));
  await new Promise(r => setTimeout(r, 2000));
  await click(page, root => Array.from(root.querySelectorAll('button')).find(b => b.innerText && b.innerText.trim() === 'Delete'));
  await new Promise(r => setTimeout(r, 4000));
  console.log(`Deleted slot ${monthDay} ${time}`);
})().catch(e => { console.error(e); process.exit(1); });
