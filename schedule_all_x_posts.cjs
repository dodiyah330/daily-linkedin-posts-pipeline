/**
 * Schedule posts on X (Twitter) via the native web composer.
 *
 * Mirrors schedule_all_posts.cjs: connect to an agent-browser Chrome session
 * that is already logged into x.com, then drive compose → schedule UI.
 *
 * Usage:
 *   agent-browser --session x_bot --profile Default open https://x.com/home
 *   SCHEDULE_FILE=schedule_x.json node schedule_all_x_posts.cjs
 *
 * Env:
 *   SCHEDULE_FILE   Path to schedule JSON (default: schedule_x.json)
 *   START_POST_ID   Resume from post id (default: 1)
 *   POST_NOW=1      Publish immediately instead of scheduling
 *   X_START_URL     Override start URL (default: https://x.com/home)
 *   X_MAX_CHARS     Soft length check (default: 280; Premium allows more)
 *
 * Post types: text | image (single or up to 4 images via assetPaths = X gallery)
 * Requires X Premium for native scheduling (calendar icon). Free accounts:
 * use POST_NOW=1 or a third-party scheduler.
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function scrubCaption(text) {
  return String(text || '')
    .replace(/\u2014/g, ',') // —
    .replace(/\u2013/g, ',') // –
    .replace(/\s*--\s*/g, ', ')
    .replace(/ ,/g, ',')
    .replace(/,\s*,+/g, ',')
    .trim();
}

const SELECTORS = {
  composeNav: '[data-testid="SideNav_NewTweet_Button"]',
  textarea: '[data-testid="tweetTextarea_0"]',
  fileInput: '[data-testid="fileInput"]',
  scheduleOption: '[data-testid="scheduleOption"]',
  tweetButton: '[data-testid="tweetButton"]',
  tweetButtonInline: '[data-testid="tweetButtonInline"]',
  appBarClose: '[data-testid="app-bar-close"]',
};

async function connectToAgentBrowser() {
  const tmpDir = os.tmpdir();
  const dirs = fs.readdirSync(tmpDir).filter(
    (name) =>
      name.startsWith('agent-browser-chrome-') ||
      name.startsWith('agent-browser-profile-')
  );
  if (dirs.length === 0) {
    throw new Error(
      'No agent-browser profile dirs in tmp. Launch agent-browser first.'
    );
  }
  const latestDir = dirs
    .map((name) => {
      const fullPath = path.join(tmpDir, name);
      return { path: fullPath, mtime: fs.statSync(fullPath).mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime)[0].path;
  const portFile = path.join(latestDir, 'DevToolsActivePort');
  const content = fs.readFileSync(portFile, 'utf8');
  const port = content.split('\n')[0].trim();
  console.log(`Connecting to browser on port ${port}...`);
  return puppeteer.connect({
    browserURL: `http://127.0.0.1:${port}`,
    protocolTimeout: 120000,
  });
}

async function findXPage(browser) {
  const pages = await browser.pages();
  return (
    pages.find((p) => {
      const u = p.url();
      return u.includes('x.com') || u.includes('twitter.com');
    }) || null
  );
}

async function clickFirst(page, selectors, { timeout = 10000 } = {}) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    for (const sel of selectors) {
      const el = await page.$(sel);
      if (!el) continue;
      const visible = await el.evaluate((e) => {
        const r = e.getBoundingClientRect();
        const s = window.getComputedStyle(e);
        return (
          r.width > 0 &&
          r.height > 0 &&
          s.visibility !== 'hidden' &&
          s.display !== 'none'
        );
      });
      if (!visible) {
        await el.dispose();
        continue;
      }
      try {
        await el.click();
      } catch {
        await el.evaluate((e) => e.click());
      }
      await el.dispose();
      return sel;
    }
    await sleep(400);
  }
  return null;
}

async function clickByText(page, texts, { roleButtons = true } = {}) {
  const wanted = texts.map((t) => t.toLowerCase());
  return page.evaluate(
    (wantedTexts, includeRole) => {
      const nodes = [
        ...document.querySelectorAll('button'),
        ...(includeRole
          ? [...document.querySelectorAll('[role="button"]')]
          : []),
      ];
      for (const el of nodes) {
        const t = (el.innerText || el.textContent || '').trim().toLowerCase();
        const aria = (el.getAttribute('aria-label') || '').trim().toLowerCase();
        if (!wantedTexts.includes(t) && !wantedTexts.includes(aria)) continue;
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) continue;
        el.click();
        return t || aria;
      }
      return null;
    },
    wanted,
    roleButtons
  );
}

async function fillTweetText(page, text) {
  const box = await page.waitForSelector(SELECTORS.textarea, { timeout: 20000 });
  await box.click({ clickCount: 1 });
  await sleep(300);

  // Clear existing content
  await page.keyboard.down(process.platform === 'darwin' ? 'Meta' : 'Control');
  await page.keyboard.press('a');
  await page.keyboard.up(process.platform === 'darwin' ? 'Meta' : 'Control');
  await page.keyboard.press('Backspace');
  await sleep(200);

  // Prefer CDP insertText (Draft.js listens to beforeinput / insertText)
  try {
    const client = await page.createCDPSession();
    await client.send('Input.insertText', { text });
    await client.detach();
  } catch (e) {
    console.log('CDP insertText failed, falling back to keyboard:', e.message);
    await page.keyboard.type(text, { delay: 8 });
  }

  await sleep(500);
  const len = await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    return (el?.innerText || el?.textContent || '').trim().length;
  }, SELECTORS.textarea);

  if (len < Math.min(5, text.trim().length)) {
    console.log('Text still short — retrying via page.evaluate insertText...');
    await page.evaluate((sel, value) => {
      const el = document.querySelector(sel);
      if (!el) return;
      el.focus();
      const selRange = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(el);
      selRange.removeAllRanges();
      selRange.addRange(range);
      document.execCommand('delete');
      const lines = value.split('\n');
      for (let i = 0; i < lines.length; i++) {
        if (i > 0) document.execCommand('insertLineBreak');
        if (lines[i]) document.execCommand('insertText', false, lines[i]);
      }
      el.dispatchEvent(
        new InputEvent('input', {
          bubbles: true,
          cancelable: true,
          inputType: 'insertText',
        })
      );
    }, SELECTORS.textarea, text);
    await sleep(500);
  }

  const finalLen = await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    return (el?.innerText || el?.textContent || '').trim().length;
  }, SELECTORS.textarea);
  console.log(`Caption length in composer: ${finalLen}`);
  if (finalLen < 1) throw new Error('Failed to fill tweet text');
  return finalLen;
}

async function uploadImages(page, paths) {
  const list = (Array.isArray(paths) ? paths : [paths]).filter(Boolean).slice(0, 4);
  if (!list.length) return;
  for (const p of list) {
    if (!fs.existsSync(p)) throw new Error(`Image not found: ${p}`);
  }
  console.log(
    `Uploading ${list.length} image(s): ${list.map((p) => path.basename(p)).join(', ')}`
  );

  let input = await page.$(SELECTORS.fileInput);
  if (!input) {
    await clickFirst(page, [
      '[aria-label="Add photos or video"]',
      '[aria-label*="media" i]',
      '[data-testid="toolBar"] [aria-label*="photo" i]',
    ]);
    await sleep(800);
    input = await page.$(SELECTORS.fileInput);
  }
  if (!input) throw new Error('Could not find media file input');

  // X accepts multiple files on one file input (gallery / swipe carousel, max 4)
  await input.uploadFile(...list);
  await sleep(3500 + list.length * 800);

  await page
    .waitForSelector('[data-testid="attachments"], [data-testid="tweetPhoto"]', {
      timeout: 15000,
    })
    .catch(() => {});
  console.log('Image upload complete');
}

function parseDateTime(dateStr, timeStr) {
  // date: MM/DD/YYYY ; time: "9:00 AM" / "12:00 PM"
  const [mm, dd, yyyy] = dateStr.split(/[\/\-]/).map((x) => parseInt(x, 10));
  const m = timeStr.trim().match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (!m) throw new Error(`Bad time format: ${timeStr} (want e.g. 9:00 AM)`);
  let hour = parseInt(m[1], 10);
  const minute = parseInt(m[2], 10);
  const ampm = m[3].toUpperCase();
  if (ampm === 'PM' && hour !== 12) hour += 12;
  if (ampm === 'AM' && hour === 12) hour = 0;
  return {
    month: mm, // 1-12
    day: dd,
    year: yyyy,
    hour24: hour,
    hour12: ((hour + 11) % 12) + 1,
    minute,
    ampm,
    jsMonth: mm - 1,
  };
}

async function setScheduleDateTime(page, dateStr, timeStr) {
  const dt = parseDateTime(dateStr, timeStr);
  console.log(
    `Setting schedule: ${dateStr} ${timeStr} → hour24=${dt.hour24} min=${dt.minute}`
  );
  await sleep(800);

  // Tag the 5 schedule <select>s so Puppeteer's page.select can drive React onChange
  const tagged = await page.evaluate(() => {
    const dialogs = [...document.querySelectorAll('[role="dialog"]')];
    const scope = dialogs.find((d) => d.querySelectorAll('select').length >= 5);
    if (!scope) return { ok: false, reason: 'schedule dialog with 5 selects not found' };
    const selects = [...scope.querySelectorAll('select')];
    const ids = ['x_sched_mon', 'x_sched_day', 'x_sched_yr', 'x_sched_hour', 'x_sched_min'];
    selects.slice(0, 5).forEach((s, i) => {
      s.id = ids[i];
    });
    const hourOpts = [...selects[3].options].map((o) => o.value);
    return {
      ok: true,
      is24h: hourOpts.includes('13') || hourOpts.includes('23') || hourOpts.includes('0'),
      hourOptsSample: hourOpts.slice(0, 5),
    };
  });
  if (!tagged.ok) throw new Error(tagged.reason);

  const hourVal = tagged.is24h
    ? String(dt.hour24)
    : String(dt.hour12);
  // Minute options use unpadded values ("0") in current X UI
  const minVal = String(dt.minute);

  await page.select('#x_sched_mon', String(dt.month));
  await page.select('#x_sched_day', String(dt.day));
  await page.select('#x_sched_yr', String(dt.year));
  await page.select('#x_sched_hour', hourVal);
  await page.select('#x_sched_min', minVal);
  await sleep(600);

  const check = await page.evaluate((wantAmpm, wantHour12) => {
    const scope = [...document.querySelectorAll('[role="dialog"]')].find(
      (d) => d.querySelector('#x_sched_hour')
    );
    const preview =
      (scope?.innerText || '').split('\n').find((l) => /Will send on/i.test(l)) ||
      '';
    return {
      preview,
      hour: document.querySelector('#x_sched_hour')?.value,
      minute: document.querySelector('#x_sched_min')?.value,
      timeInput: scope?.querySelector('input[type="time"]')?.value || null,
      previewHasAmpm: preview.toUpperCase().includes(wantAmpm),
      previewHasHour:
        preview.includes(`${wantHour12}:`) ||
        preview.includes(` ${wantHour12}:`) ||
        preview.includes(` ${String(wantHour12).padStart(2, '0')}:`),
    };
  }, dt.ampm, dt.hour12);

  console.log('Datetime check:', JSON.stringify({ tagged, hourVal, minVal, check }));
  if (check.preview && (!check.previewHasAmpm || !check.previewHasHour)) {
    throw new Error(
      `Schedule preview mismatch: "${check.preview}" (wanted ${dt.hour12}:xx ${dt.ampm})`
    );
  }
  if (check.preview) console.log(`Preview OK: ${check.preview}`);
}

async function confirmScheduleDialog(page) {
  const clicked =
    (await clickFirst(page, [
      '[data-testid="scheduledConfirmationPrimaryAction"]',
      '[data-testid="scheduledConfirmationButton"]',
      '[data-testid="confirmSchedule"]',
      '[data-testid="scheduleConfirmButton"]',
      '[data-testid="dateTimeConfirm"]',
      '[data-testid="DatePickerConfirmButton"]',
    ])) || (await clickByText(page, ['Confirm', 'Done', 'OK', 'Set', 'Apply']));
  if (!clicked) {
    console.log('Confirm not found — pressing Enter');
    await page.keyboard.press('Enter');
  } else {
    console.log(`Confirmed schedule dialog via: ${clicked}`);
  }
  await sleep(2000);
}

async function clickFinalScheduleOrPost(page, postNow) {
  if (postNow) {
    const clicked =
      (await clickFirst(page, [
        SELECTORS.tweetButton,
        SELECTORS.tweetButtonInline,
      ])) || (await clickByText(page, ['Post']));
    if (!clicked) throw new Error("Could not click 'Post'");
    console.log('Clicked Post');
  } else {
    // After date confirm, the primary button becomes "Schedule"
    let clicked = await page.evaluate(() => {
      const btn =
        document.querySelector('[data-testid="tweetButton"]') ||
        document.querySelector('[data-testid="tweetButtonInline"]');
      if (!btn) return null;
      const t = (btn.innerText || '').trim();
      const disabled =
        btn.disabled ||
        btn.getAttribute('aria-disabled') === 'true' ||
        (typeof btn.className === 'string' && btn.className.includes('disabled'));
      if (disabled) return `disabled:${t}`;
      btn.click();
      return t || 'tweetButton';
    });
    if (!clicked || String(clicked).startsWith('disabled')) {
      clicked = await clickByText(page, ['Schedule']);
    }
    if (!clicked || String(clicked).startsWith('disabled')) {
      throw new Error(`Could not click final Schedule (got ${clicked})`);
    }
    console.log(`Clicked Schedule via: ${clicked}`);
  }

  // Wait for composer to close — do NOT Discard (that cancels an unsent draft)
  const closed = await page
    .waitForFunction(
      () => !document.querySelector('[data-testid="tweetTextarea_0"]'),
      { timeout: 12000 }
    )
    .then(() => true)
    .catch(() => false);
  if (!closed) {
    console.warn(
      'Composer still open after Schedule/Post — leaving it (no Discard). Continuing.'
    );
    await page.keyboard.press('Escape');
    await sleep(1000);
    // If discard sheet appears, cancel it (keep draft) rather than discarding
    await clickByText(page, ['Cancel', 'Keep editing', 'Not now']);
  }
  await sleep(1500);
}

async function closeComposerIfOpen(page) {
  const stillOpen = await page.$(SELECTORS.textarea);
  if (!stillOpen) return;
  console.log('Composer still open — dismissing...');
  await clickFirst(page, [
    SELECTORS.appBarClose,
    '[aria-label="Close"]',
    '[data-testid="app-bar-close"]',
  ]);
  await sleep(800);
  // Discard draft confirmation
  await clickByText(page, ['Discard', 'Discard post']);
  await sleep(1000);
}

async function openComposer(page) {
  // Prefer direct compose URL for a clean modal each time
  try {
    await page.goto('https://x.com/compose/post', {
      waitUntil: 'domcontentloaded',
      timeout: 20000,
    });
  } catch (e) {
    console.log('Compose navigation warning:', e.message);
  }
  await sleep(2500);

  const hasBox = await page.$(SELECTORS.textarea);
  if (hasBox) return;

  console.log('Opening composer via sidebar Post button...');
  const clicked = await clickFirst(page, [
    SELECTORS.composeNav,
    'a[href="/compose/post"]',
    'a[aria-label="Post"]',
  ]);
  if (!clicked) throw new Error('Could not open X compose modal — are you logged in?');
  await page.waitForSelector(SELECTORS.textarea, { timeout: 15000 });
}

(async () => {
  const scheduleFile = process.env.SCHEDULE_FILE
    ? path.resolve(__dirname, process.env.SCHEDULE_FILE)
    : path.join(__dirname, 'schedule_x.json');
  const maxChars = parseInt(process.env.X_MAX_CHARS || '280', 10);
  const postNow = process.env.POST_NOW === '1';
  const screenshotDir = path.join(__dirname, 'slack_downloads');
  if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

  if (!fs.existsSync(scheduleFile)) {
    console.error(`Schedule file not found: ${scheduleFile}`);
    console.error('Run: python3 prepare_x_schedule.py');
    process.exit(1);
  }

  const schedule = JSON.parse(fs.readFileSync(scheduleFile, 'utf8'));
  const posts = schedule.posts || [];
  console.log(`Loaded ${posts.length} posts from ${path.basename(scheduleFile)}`);

  let browser;
  try {
    browser = await connectToAgentBrowser();
    let page = await findXPage(browser);
    if (!page) {
      const startUrl = process.env.X_START_URL || schedule.startUrl || 'https://x.com/home';
      console.log(`No x.com tab found — opening ${startUrl}`);
      page = await browser.newPage();
      await page.goto(startUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await sleep(3000);
    }
    await page.bringToFront();
    await page.setViewport({ width: 1280, height: 1000 });

    // Login check
    const loggedIn = await page.$(SELECTORS.composeNav);
    if (!loggedIn) {
      console.error(
        'Not logged into X (SideNav Post button missing). Log in in agent-browser, then retry.'
      );
      process.exit(1);
    }

    const startFrom = parseInt(process.env.START_POST_ID || '1', 10);
    const queue = posts.filter((p) => p.id >= startFrom);
    if (startFrom > 1) {
      console.log(`Resuming from post ${startFrom} (${queue.length} remaining)`);
    }

    console.log(`\n${'='.repeat(60)}`);
    console.log(
      `${postNow ? 'POSTING' : 'SCHEDULING'} ${queue.length} X POSTS`
    );
    console.log(`${'='.repeat(60)}\n`);

    for (const post of queue) {
      const type = post.type || (post.assetPath ? 'image' : 'text');
      console.log(`\n${'='.repeat(50)}`);
      console.log(
        `Post ${post.id}/${posts.length} (${type}): ${post.date} ${post.time}`
      );
      console.log(`${'='.repeat(50)}`);
      const prefix = path.join(screenshotDir, `x_post_${post.id}_${type}`);

      const caption = scrubCaption((post.caption || post.text || '').trim());
      if (!caption) throw new Error(`Post ${post.id} has empty caption`);
      if (/—|--/.test(post.caption || post.text || '')) {
        console.warn(`Post ${post.id}: stripped dash punctuation from caption`);
      }
      if (caption.length > maxChars) {
        console.warn(
          `Warning: caption is ${caption.length} chars (X_MAX_CHARS=${maxChars}). Premium allows longer; free accounts will fail.`
        );
      }

      await openComposer(page);
      await sleep(1000);

      if (type === 'image' || post.assetPath || post.assetPaths) {
        const paths = post.assetPaths || (post.assetPath ? [post.assetPath] : []);
        await uploadImages(page, paths);
      }

      console.log('Filling caption...');
      await fillTweetText(page, caption);
      await page.screenshot({ path: `${prefix}_draft.png` }).catch(() => {});

      if (postNow) {
        await clickFinalScheduleOrPost(page, true);
      } else {
        console.log('Opening schedule picker...');
        const schedClicked = await clickFirst(page, [
          SELECTORS.scheduleOption,
          '[aria-label*="Schedule" i]',
          '[data-testid*="schedule" i]',
        ]);
        if (!schedClicked) {
          throw new Error(
            'Schedule icon not found. Native scheduling needs X Premium on desktop web.'
          );
        }
        // Wait for date/time sheet (selects or labeled inputs)
        const sheetReady = await page
          .waitForFunction(
            () => {
              const dialogs = [...document.querySelectorAll('[role="dialog"]')];
              const scope =
                dialogs.find((d) => d.querySelectorAll('select').length >= 3) ||
                document;
              if (scope.querySelectorAll('select').length >= 3) return true;
              return !!document.querySelector(
                'select[aria-label*="Month" i], select[aria-label*="Hour" i], input[placeholder*="Date" i]'
              );
            },
            { timeout: 10000 }
          )
          .then(() => true)
          .catch(() => false);
        if (!sheetReady) {
          console.warn('Schedule sheet selects not detected yet — continuing anyway');
        }
        await sleep(800);

        await setScheduleDateTime(page, post.date, post.time);
        await page.screenshot({ path: `${prefix}_schedule.png` }).catch(() => {});
        await confirmScheduleDialog(page);

        // Caption can sometimes clear after schedule confirm — refill if needed
        const lenAfter = await page.evaluate((sel) => {
          const el = document.querySelector(sel);
          return (el?.innerText || '').trim().length;
        }, SELECTORS.textarea);
        if (lenAfter < 5) {
          console.log('Caption lost after schedule confirm — re-filling...');
          await fillTweetText(page, caption);
        }

        await clickFinalScheduleOrPost(page, false);
      }

      await page.screenshot({ path: `${prefix}_done.png` }).catch(() => {});
      // Avoid Discard — closeComposerIfOpen can kill a just-scheduled draft
      console.log(`✓ Post ${post.id} ${postNow ? 'posted' : 'scheduled'}`);
      await sleep(2500);
    }

    console.log(`\n${'='.repeat(60)}`);
    console.log(`✓ ALL ${queue.length} X POSTS COMPLETE`);
    console.log(`${'='.repeat(60)}`);
    process.exit(0);
  } catch (err) {
    console.error('X scheduler error:', err);
    try {
      const pages = browser ? await browser.pages() : [];
      const page = pages.find(
        (p) => p.url().includes('x.com') || p.url().includes('twitter.com')
      );
      if (page) {
        await page.screenshot({
          path: path.join(__dirname, 'error_x_screenshot.png'),
        });
        console.log('Saved error_x_screenshot.png');
      }
    } catch (_) {}
    process.exit(1);
  }
})();
