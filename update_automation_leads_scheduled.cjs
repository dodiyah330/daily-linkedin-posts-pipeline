#!/usr/bin/env node
/** Update Jul 6–10 automation-leads scheduled posts with latest captions from schedule_automation_leads.json */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

function findPort() {
  const tmpDir = os.tmpdir();
  const dirs = fs.readdirSync(tmpDir).filter(n =>
    n.startsWith('agent-browser-chrome-') || n.startsWith('agent-browser-profile-')
  );
  if (!dirs.length) throw new Error('Launch agent-browser first');
  const latest = dirs.map(name => ({
    path: path.join(tmpDir, name),
    mtime: fs.statSync(path.join(tmpDir, name)).mtimeMs,
  })).sort((a, b) => b.mtime - a.mtime)[0].path;
  return fs.readFileSync(path.join(latest, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
}

function toLabel(dateStr, time) {
  const [m, d, y] = dateStr.split('/');
  const dt = new Date(parseInt(y, 10), parseInt(m, 10) - 1, parseInt(d, 10));
  return `${DAYS[dt.getDay()]} ${MONTHS[dt.getMonth()]} ${parseInt(d, 10)}, ${y} at ${time}`;
}

function toMatchTokens(dateStr, time) {
  const [m, d] = dateStr.split('/');
  return { month: MONTHS[parseInt(m, 10) - 1], day: parseInt(d, 10), time };
}

async function getElementShadow(page, selector) {
  const handle = await page.evaluateHandle((sel) => {
    function findEl(root) {
      if (!root) return null;
      const els = root.querySelectorAll(sel);
      for (const el of els) {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) return el;
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const f = findEl(node.shadowRoot);
          if (f) return f;
        }
      }
      return null;
    }
    return findEl(document.body);
  }, selector);
  return handle.asElement();
}

async function clickNativelyShadow(page, finderFn) {
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

async function fillCaption(page, text) {
  const client = await page.createCDPSession();
  const editor = await getElementShadow(page, '.ql-editor');
  if (!editor) return false;
  await editor.click();
  await page.keyboard.down('Control');
  await page.keyboard.press('KeyA');
  await page.keyboard.up('Control');
  await page.keyboard.press('Backspace');
  await client.send('Input.insertText', { text });
  await editor.dispose();
  return true;
}

async function openScheduledModal(page) {
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await new Promise(r => setTimeout(r, 3000));
  await clickNativelyShadow(page, root =>
    Array.from(root.querySelectorAll('*')).find(el => el.innerText && el.innerText.trim().includes('Start a post'))
  );
  await new Promise(r => setTimeout(r, 2500));
  await clickNativelyShadow(page, root => {
    const buttons = Array.from(root.querySelectorAll('button'));
    const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
    if (postBtn && postBtn.previousElementSibling) return postBtn.previousElementSibling;
    return buttons.find(b => b.ariaLabel && b.ariaLabel.includes('Schedule'));
  });
  await new Promise(r => setTimeout(r, 2500));
  await clickNativelyShadow(page, root =>
    Array.from(root.querySelectorAll('button, a')).find(el => {
      const t = (el.innerText || '').trim().toLowerCase();
      return t.includes('view all scheduled posts');
    })
  );
  await new Promise(r => setTimeout(r, 5000));
}

(async () => {
  const schedulePath = path.join(__dirname, 'schedule_automation_leads.json');
  const { posts } = JSON.parse(fs.readFileSync(schedulePath, 'utf8'));
  const onlyIds = process.env.POST_IDS ? process.env.POST_IDS.split(',').map(Number) : null;
  const regularPosts = posts.filter(p => p.type === 'regular' && (!onlyIds || onlyIds.includes(p.id)));

  const port = findPort();
  const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
  const page = (await browser.pages()).find(p => p.url().includes('linkedin.com'));
  if (!page) throw new Error('LinkedIn tab not found');
  await page.bringToFront();
  await page.setViewport({ width: 1280, height: 1200 });

  for (const post of regularPosts) {
    const { month, day, time } = toMatchTokens(post.date, post.time);
    console.log(`\n--- Updating post ${post.id}: ${month} ${day} at ${time} ---`);
    await openScheduledModal(page);

    const clicked = await clickNativelyShadow(page, root => {
      const btns = Array.from(root.querySelectorAll('button'));
      return btns.find(b => {
        const a = b.ariaLabel || '';
        return a.includes('Actions menu for scheduled post') &&
          a.includes(`${month} ${day}`) &&
          a.includes(time);
      });
    });
    if (!clicked) {
      console.log(`Could not find scheduled post for ${month} ${day} ${time} — will schedule fresh later`);
      continue;
    }
    await new Promise(r => setTimeout(r, 2000));

    await clickNativelyShadow(page, root =>
      Array.from(root.querySelectorAll('button, div, li, span, [role="button"]')).find(
        b => b.innerText && b.innerText.trim() === 'Edit post'
      )
    );
    await new Promise(r => setTimeout(r, 3000));

    const filled = await fillCaption(page, post.caption);
    console.log(`Caption fill: ${filled ? 'ok' : 'failed'}`);
    await new Promise(r => setTimeout(r, 1500));

    await clickNativelyShadow(page, root =>
      Array.from(root.querySelectorAll('button')).find(b => {
        const t = (b.innerText || '').trim();
        return t === 'Schedule' || b.getAttribute('aria-label') === 'Schedule';
      })
    );
    await new Promise(r => setTimeout(r, 4000));
    console.log(`✓ Updated post ${post.id}`);
  }

  const pollPost = posts.find(p => p.type === 'poll');
  if (pollPost) {
    console.log('\n--- Poll post: delete old + re-schedule recommended ---');
    console.log('Run: START_POST_ID=3 SCHEDULE_FILE=schedule_automation_leads.json node schedule_all_posts.cjs');
    console.log('(after manually deleting Jul 8 9AM poll if duplicate)');
  }

  console.log('\nRegular post updates complete.');
})().catch(err => {
  console.error(err);
  process.exit(1);
});
