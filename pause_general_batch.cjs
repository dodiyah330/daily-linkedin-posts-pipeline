#!/usr/bin/env node
/** Delete all scheduled posts EXCEPT the 5 automation-leads slots (Jul 6–10). */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const KEEP_SLOTS = [
  ['Mon', 'July 6', '9:00 AM'],
  ['Tue', 'July 7', '12:00 PM'],
  ['Wed', 'July 8', '9:00 AM'],
  ['Thu', 'July 9', '12:00 PM'],
  ['Fri', 'July 10', '9:00 AM'],
];

function findPort() {
  const tmpDir = os.tmpdir();
  const dirs = fs.readdirSync(tmpDir).filter(n =>
    n.startsWith('agent-browser-chrome-') || n.startsWith('agent-browser-profile-')
  );
  if (!dirs.length) throw new Error('Launch agent-browser with LinkedIn open first');
  const latest = dirs.map(name => ({
    path: path.join(tmpDir, name),
    mtime: fs.statSync(path.join(tmpDir, name)).mtimeMs,
  })).sort((a, b) => b.mtime - a.mtime)[0].path;
  return fs.readFileSync(path.join(latest, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
}

function shouldKeep(label) {
  if (!label) return false;
  return KEEP_SLOTS.some(([day, month, time]) =>
    label.includes(day) && label.includes(month) && label.includes(time)
  );
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
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 20000 });
  await new Promise(r => setTimeout(r, 4000));
  await clickNativelyShadow(page, root =>
    Array.from(root.querySelectorAll('button, [role="button"], span, div')).find(
      el => el.innerText && el.innerText.trim().includes('Start a post')
    )
  );
  await new Promise(r => setTimeout(r, 3000));
  await clickNativelyShadow(page, root => {
    const buttons = Array.from(root.querySelectorAll('button'));
    const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
    if (postBtn && postBtn.previousElementSibling) return postBtn.previousElementSibling;
    return buttons.find(b => (b.getAttribute('aria-label') || '').includes('Schedule'));
  });
  await new Promise(r => setTimeout(r, 3000));
  await clickNativelyShadow(page, root =>
    Array.from(root.querySelectorAll('button, a, span')).find(
      el => (el.innerText || '').toLowerCase().includes('view all scheduled posts')
    )
  );
  await new Promise(r => setTimeout(r, 5000));
  for (let i = 0; i < 12; i++) {
    const more = await clickNativelyShadow(page, root =>
      Array.from(root.querySelectorAll('button, span, a')).find(
        e => e.innerText && e.innerText.trim() === 'Show more Scheduled posts'
      )
    );
    if (!more) break;
    await new Promise(r => setTimeout(r, 1500));
  }
}

async function listActionLabels(page) {
  return page.evaluate(() => {
    function walk(root, out) {
      if (!root) return;
      for (const btn of root.querySelectorAll('button')) {
        const label = btn.getAttribute('aria-label') || '';
        if (label.includes('Actions menu for scheduled post')) out.push(label);
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

(async () => {
  const port = findPort();
  const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
  const page = (await browser.pages()).find(p => p.url().includes('linkedin.com'));
  if (!page) throw new Error('LinkedIn tab not found');
  await page.bringToFront();
  await openScheduledModal(page);

  let deleted = 0;
  let kept = 0;

  while (true) {
    const labels = await listActionLabels(page);
    const target = labels.find(l => !shouldKeep(l));
    if (!target) {
      console.log(`Done. Deleted ${deleted}, kept ${labels.length} automation posts.`);
      break;
    }

    console.log(`Deleting: ${target.slice(0, 100)}...`);
    const clicked = await clickNativelyShadow(page, root => {
      const btns = Array.from(root.querySelectorAll('button'));
      return btns.find(b => (b.getAttribute('aria-label') || '') === target);
    });
    if (!clicked) {
      console.log('Could not click actions menu — stopping.');
      break;
    }
    await new Promise(r => setTimeout(r, 2000));
    await clickNativelyShadow(page, root =>
      Array.from(root.querySelectorAll('button, div, span, [role="button"]')).find(
        b => b.innerText && b.innerText.trim() === 'Delete post'
      )
    );
    await new Promise(r => setTimeout(r, 2000));
    const confirmed = await clickNativelyShadow(page, root => {
      const btns = Array.from(root.querySelectorAll('button'));
      return btns.find(b => b.innerText && b.innerText.trim() === 'Delete');
    });
    if (!confirmed) {
      console.log('Delete confirm not found — stopping.');
      break;
    }
    await new Promise(r => setTimeout(r, 4000));
    deleted++;
  }

  const remaining = await listActionLabels(page);
  kept = remaining.length;
  console.log('\nRemaining scheduled posts:');
  remaining.forEach(l => console.log('  KEEP:', l.replace('Actions menu for scheduled post that will be published on ', '')));

  fs.writeFileSync(path.join(__dirname, '.general_batch_paused'), new Date().toISOString() + '\n');
  console.log('\nWrote .general_batch_paused marker.');
  process.exit(0);
})().catch(err => {
  console.error(err);
  process.exit(1);
});
