#!/usr/bin/env node
/** Scrape visible caption snippets for automation slots Jul 6–10 from scheduled posts modal */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const TARGETS = [
  'Posting Mon, Jul 6 at 9:00 AM',
  'Posting Tue, Jul 7 at 12:00 PM',
  'Posting Wed, Jul 8 at 9:00 AM',
  'Posting Thu, Jul 9 at 12:00 PM',
  'Posting Fri, Jul 10 at 9:00 AM',
];

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

async function openScheduledModal(page) {
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await new Promise(r => setTimeout(r, 4000));
  await page.evaluate(() => {
    function findEl(root) {
      if (!root) return null;
      const el = Array.from(root.querySelectorAll('*')).find(
        e => (e.tagName === 'BUTTON' || e.getAttribute('role') === 'button' || e.getAttribute('aria-label') === 'Start a post') &&
          e.innerText && e.innerText.trim().includes('Start a post')
      );
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
    const btn = findEl(document.body);
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 3000));
  await page.evaluate(() => {
    function findScheduleIcon(root) {
      if (!root) return null;
      const buttons = Array.from(root.querySelectorAll('button'));
      const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
      if (postBtn && postBtn.previousElementSibling) return postBtn.previousElementSibling;
      const schedBtn = buttons.find(b => b.getAttribute('aria-label')?.includes('Schedule'));
      if (schedBtn) return schedBtn;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = findScheduleIcon(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    const btn = findScheduleIcon(document.body);
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 3000));
  await page.evaluate(() => {
    function findViewAll(root) {
      if (!root) return null;
      const el = Array.from(root.querySelectorAll('a, button, span')).find(
        e => e.innerText && e.innerText.includes('View all scheduled posts')
      );
      if (el) return el;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = findViewAll(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    const btn = findViewAll(document.body);
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 4000));
  for (let i = 0; i < 15; i++) {
    const clicked = await page.evaluate(() => {
      function findShowMore(root) {
        if (!root) return null;
        const el = Array.from(root.querySelectorAll('button, span, a')).find(
          e => e.innerText && e.innerText.trim() === 'Show more Scheduled posts'
        );
        if (el) return el;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findShowMore(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      function findScrollable(root) {
        if (!root) return null;
        const heading = Array.from(root.querySelectorAll('h2, span, p')).find(
          el => el.innerText && el.innerText.includes('Scheduled posts')
        );
        if (heading) {
          let p = heading.parentNode;
          while (p && p !== document.body) {
            if ((p.classList && p.classList.contains('artdeco-modal')) || p.getAttribute('role') === 'dialog') {
              const elements = p.querySelectorAll('*');
              for (const el of elements) {
                if (el.scrollHeight > el.clientHeight) return el;
              }
              return p.querySelector('.artdeco-modal__content') || p;
            }
            p = p.parentNode || p.host;
          }
        }
        return null;
      }
      const btn = findShowMore(document.body);
      if (btn) { btn.click(); return 'more'; }
      const s = findScrollable(document.body);
      if (s) { s.scrollTop = s.scrollHeight; return 'scroll'; }
      return null;
    });
    if (!clicked) break;
    await new Promise(r => setTimeout(r, 1200));
  }
}

(async () => {
  const port = findPort();
  const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
  const page = (await browser.pages()).find(p => p.url().includes('linkedin.com'));
  await page.bringToFront();
  await openScheduledModal(page);

  const snippets = await page.evaluate((targets) => {
    function allText(root) {
      if (!root) return '';
      let t = root.innerText || '';
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) t += '\n' + allText(node.shadowRoot);
      }
      return t;
    }
    const body = allText(document.body);
    const results = {};
    for (const target of targets) {
      const idx = body.indexOf(target);
      if (idx === -1) {
        results[target] = 'NOT FOUND';
        continue;
      }
      const chunk = body.slice(idx, idx + 400).replace(/\s+/g, ' ').trim();
      results[target] = chunk;
    }
    return results;
  }, TARGETS);

  for (const target of TARGETS) {
    console.log('\n=== ' + target + ' ===');
    console.log(snippets[target]);
  }
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
