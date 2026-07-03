#!/usr/bin/env node
/** Delete scheduled posts matching old automation-leads batch (before profile update). */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const OLD_MARKERS = [
  'signaling a massive push into desktop-level',
  'without hiring more account managers',
  '200 demo requests a week',
  'What is the main obstacle stopping your team',
  'Lead Enrichment: Instantly research',
  'PandaDoc or DocuSign',
  'What is holding your business back from automating manual work',
];

const MAX_DELETE = parseInt(process.env.MAX_DELETE || '5', 10);

function findChromePort() {
  const tmpDir = os.tmpdir();
  const prefixes = ['agent-browser-profile-', 'agent-browser-chrome-'];
  const dirs = fs.readdirSync(tmpDir).filter(n => prefixes.some(p => n.startsWith(p)));
  if (!dirs.length) throw new Error('No agent-browser profile dir found');
  const latest = dirs.map(name => ({
    path: path.join(tmpDir, name),
    mtime: fs.statSync(path.join(tmpDir, name)).mtimeMs,
  })).sort((a, b) => b.mtime - a.mtime)[0].path;
  const port = fs.readFileSync(path.join(latest, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
  return port;
}

async function clickNativelyShadow(page, finderFn) {
  await page.evaluate(() => {
    document.querySelectorAll('.msg-overlay-container, [class*="msg-overlay"], #msg-overlay').forEach(el => el.remove());
  });
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
  if (!el) return false;
  await page.evaluate(e => { e.focus(); e.click(); }, el);
  await el.dispose();
  return true;
}

async function openScheduledModal(page) {
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await new Promise(r => setTimeout(r, 3000));
  await clickNativelyShadow(page, (root) =>
    Array.from(root.querySelectorAll('button, [role="button"], span, div')).find(
      el => el.innerText && el.innerText.trim().includes('Start a post')
    )
  );
  await new Promise(r => setTimeout(r, 3000));
  await clickNativelyShadow(page, (root) => {
    const buttons = Array.from(root.querySelectorAll('button'));
    const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
    if (postBtn && postBtn.previousElementSibling) return postBtn.previousElementSibling;
    return buttons.find(b => b.ariaLabel && b.ariaLabel.includes('Schedule'));
  });
  await new Promise(r => setTimeout(r, 2500));
  await clickNativelyShadow(page, (root) =>
    Array.from(root.querySelectorAll('button, a')).find(el => {
      const txt = el.innerText ? el.innerText.trim().toLowerCase() : '';
      return txt.includes('view all scheduled posts');
    })
  );
  await new Promise(r => setTimeout(r, 5000));
}

async function getScheduledPreviews(page) {
  return page.evaluate(() => {
    function walk(root, out) {
      if (!root) return;
      for (const btn of root.querySelectorAll('button')) {
        const label = btn.getAttribute('aria-label') || '';
        if (label.includes('Actions menu for scheduled post')) {
          let text = '';
          let parent = btn.closest('li, article, div[class*="scheduled"]') || btn.parentElement;
          for (let i = 0; i < 8 && parent; i++) {
            text = parent.innerText || text;
            if (text.length > 80) break;
            parent = parent.parentElement;
          }
          out.push({ label, text: text.slice(0, 500) });
        }
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) walk(node.shadowRoot, out);
      }
    }
    const out = [];
    walk(document.body, out);
    return out;
  });
}

function matchesOldBatch(text) {
  const t = (text || '').toLowerCase();
  return OLD_MARKERS.some(m => t.includes(m.toLowerCase()));
}

(async () => {
  const port = findChromePort();
  const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
  const page = (await browser.pages()).find(p => p.url().includes('linkedin.com')) || (await browser.newPage());
  await page.bringToFront();
  await openScheduledModal(page);

  let deleted = 0;
  while (deleted < MAX_DELETE) {
    const previews = await getScheduledPreviews(page);
    const target = previews.find(p => matchesOldBatch(p.text) || matchesOldBatch(p.label));
    if (!target) {
      console.log(`No more old automation posts found. Deleted ${deleted}.`);
      break;
    }
    console.log(`Deleting post matching old batch: ${target.label.slice(0, 80)}...`);

    const clicked = await clickNativelyShadow(page, (root) => {
      const btns = Array.from(root.querySelectorAll('button'));
      if (target.label) {
        const exact = btns.find(b => b.ariaLabel === target.label);
        if (exact) return exact;
      }
      return btns.find(b => b.ariaLabel && b.ariaLabel.includes('Actions menu for scheduled post'));
    });
    if (!clicked) break;

    await new Promise(r => setTimeout(r, 2000));
    await clickNativelyShadow(page, (root) =>
      Array.from(root.querySelectorAll('button, div, span, [role="button"]')).find(
        b => b.innerText && b.innerText.trim() === 'Delete post'
      )
    );
    await new Promise(r => setTimeout(r, 2000));
    await clickNativelyShadow(page, (root) => {
      const confirmBtns = Array.from(root.querySelectorAll('button'));
      return confirmBtns.find(b => b.innerText && b.innerText.trim() === 'Delete');
    });
    await new Promise(r => setTimeout(r, 4000));
    deleted++;
    console.log(`Deleted ${deleted}/${MAX_DELETE}`);
  }

  console.log(`Done. Total deleted: ${deleted}`);
  process.exit(0);
})().catch(err => {
  console.error(err);
  process.exit(1);
});
