/**
 * Delete all X scheduled posts via the Drafts → Scheduled → Edit UI.
 * Usage: node clear_x_scheduled.cjs
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function connect() {
  const tmp = os.tmpdir();
  const dirs = fs
    .readdirSync(tmp)
    .filter((n) => n.startsWith('agent-browser-profile-') || n.startsWith('agent-browser-chrome-'))
    .map((n) => ({ p: path.join(tmp, n), m: fs.statSync(path.join(tmp, n)).mtimeMs }))
    .sort((a, b) => b.m - a.m);
  if (!dirs.length) throw new Error('No agent-browser session');
  const port = fs
    .readFileSync(path.join(dirs[0].p, 'DevToolsActivePort'), 'utf8')
    .split('\n')[0]
    .trim();
  return puppeteer.connect({
    browserURL: `http://127.0.0.1:${port}`,
    protocolTimeout: 120000,
  });
}

(async () => {
  const browser = await connect();
  const page = (await browser.pages()).find(
    (p) => p.url().includes('x.com') || p.url().includes('twitter.com')
  );
  if (!page) throw new Error('No x.com tab — open agent-browser to x.com first');
  await page.bringToFront();
  await page.goto('https://x.com/compose/post', {
    waitUntil: 'domcontentloaded',
    timeout: 20000,
  });
  await sleep(2500);

  const clickText = async (texts) =>
    page.evaluate((wanted) => {
      const nodes = [
        ...document.querySelectorAll('button, [role="button"], [role="tab"]'),
      ];
      for (const el of nodes) {
        const t = (el.innerText || '').trim();
        if (wanted.includes(t)) {
          el.click();
          return t;
        }
      }
      return null;
    }, texts);

  if (!(await clickText(['Drafts']))) throw new Error('Drafts button missing');
  await sleep(1500);
  if (!(await clickText(['Scheduled']))) throw new Error('Scheduled tab missing');
  await sleep(1500);

  const before = await page.evaluate(() =>
    [...document.querySelectorAll('button')]
      .map((b) => (b.innerText || '').trim().split('\n')[0])
      .filter((t) => t.startsWith('Will send on'))
  );
  console.log(`Found ${before.length} scheduled:`);
  before.forEach((l) => console.log(' -', l));
  if (!before.length) {
    console.log('Nothing to delete');
    process.exit(0);
  }

  if (!(await clickText(['Edit']))) throw new Error('Edit missing');
  await sleep(1000);
  if (!(await clickText(['Select all']))) throw new Error('Select all missing');
  await sleep(800);

  // First Delete enables confirm sheet
  await clickText(['Delete']);
  await sleep(1200);

  // Confirm on the topmost dialog
  const confirmed = await page.evaluate(() => {
    const dialogs = [...document.querySelectorAll('[role="dialog"], [data-testid="confirmationSheetDialog"]')];
    for (const d of dialogs.reverse()) {
      const btn = [...d.querySelectorAll('button')].find(
        (b) => (b.innerText || '').trim() === 'Delete' && !b.disabled
      );
      if (btn) {
        btn.click();
        return true;
      }
    }
    const testId = document.querySelector(
      '[data-testid="confirmationSheetConfirm"]'
    );
    if (testId) {
      testId.click();
      return true;
    }
    return false;
  });
  console.log('Confirm delete clicked:', confirmed);
  await sleep(3000);

  const after = await page.evaluate(() =>
    [...document.querySelectorAll('button')]
      .map((b) => (b.innerText || '').trim().split('\n')[0])
      .filter((t) => t.startsWith('Will send on'))
  );
  console.log(`Remaining: ${after.length}`);
  after.forEach((l) => console.log(' -', l));
  process.exit(after.length ? 1 : 0);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
