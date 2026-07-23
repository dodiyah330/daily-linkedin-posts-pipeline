#!/usr/bin/env node
/**
 * Send LinkedIn DMs to 1st-degree connections outside India.
 *
 * Requires: agent-browser --session linkedin_bot open https://www.linkedin.com/feed/
 *
 * Env:
 *   DRY_RUN=1                 Discover/filter only, do not send
 *   MAX_DMS_PER_RUN=10        Cap per script run
 *   MAX_DMS_PER_DAY=20        Cap per calendar day
 *   DM_DELAY_MS=18000         Pause between sends
 *   DM_VARIANT=hook           Template key: hook|founder|ops|short
 *   DM_SCROLLS=12             Scrolls while collecting search results
 *   DM_SEARCH_BATCH=40        Max prospects to collect before filtering
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const LOG_FILE = path.join(__dirname, 'connection-dms-run-log.json');
const CACHE_FILE = path.join(__dirname, 'connection-dms-targets-cache.json');
const TEMPLATES_FILE = path.join(__dirname, 'connection_dm_templates.json');

const DRY_RUN = process.env.DRY_RUN === '1';
const DELAY_MS = parseInt(process.env.DM_DELAY_MS || '18000', 10);
const MAX_PER_RUN = parseInt(process.env.MAX_DMS_PER_RUN || '10', 10);
const MAX_PER_DAY = parseInt(process.env.MAX_DMS_PER_DAY || '20', 10);
const VARIANT = process.env.DM_VARIANT || 'hook';
const SEARCH_SCROLLS = parseInt(process.env.DM_SCROLLS || '12', 10);
const SEARCH_BATCH = parseInt(process.env.DM_SEARCH_BATCH || '40', 10);

// Major markets outside India (LinkedIn geoUrn)
const GEO_TARGETS = [
  { name: 'United States', urn: '103644278' },
  { name: 'United Kingdom', urn: '101165590' },
  { name: 'Canada', urn: '101174742' },
  { name: 'Australia', urn: '101452733' },
  { name: 'United Arab Emirates', urn: '104305776' },
  { name: 'Singapore', urn: '102454443' },
  { name: 'Germany', urn: '101282230' },
  { name: 'Netherlands', urn: '102890719' },
  { name: 'Saudi Arabia', urn: '100459316' },
  { name: 'France', urn: '105015875' },
  { name: 'Ireland', urn: '104738515' },
  { name: 'New Zealand', urn: '105490917' },
  { name: 'Switzerland', urn: '106693272' },
  { name: 'Spain', urn: '105646813' },
  { name: 'Italy', urn: '103350119' },
  { name: 'Sweden', urn: '105117694' },
  { name: 'Norway', urn: '103819153' },
  { name: 'Denmark', urn: '104514075' },
  { name: 'Poland', urn: '105072130' },
  { name: 'Portugal', urn: '100364837' },
  { name: 'Israel', urn: '101620260' },
  { name: 'Japan', urn: '101355337' },
  { name: 'South Korea', urn: '105149562' },
  { name: 'Hong Kong', urn: '103291313' },
  { name: 'Malaysia', urn: '106808692' },
  { name: 'South Africa', urn: '104035573' },
  { name: 'Brazil', urn: '106057199' },
  { name: 'Mexico', urn: '103323778' },
  { name: 'Armenia', urn: '103037114' },
];

const INDIA_MARKERS = [
  'india', 'mumbai', 'delhi', 'new delhi', 'bengaluru', 'bangalore', 'hyderabad',
  'chennai', 'kolkata', 'pune', 'ahmedabad', 'jaipur', 'surat', 'lucknow',
  'noida', 'gurgaon', 'gurugram', 'chandigarh', 'kochi', 'indore', 'nagpur',
  'vadodara', 'coimbatore', 'visakhapatnam', 'bhopal', 'patna', 'gujarat',
  'maharashtra', 'karnataka', 'tamil nadu', 'telangana', 'kerala', 'rajasthan',
];

function loadJson(file, fallback) {
  if (!fs.existsSync(file)) return fallback;
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return fallback;
  }
}

function saveJson(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2));
}

function appendLog(entry) {
  const log = loadJson(LOG_FILE, []);
  log.push(entry);
  saveJson(LOG_FILE, log.slice(-2000));
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function profileSlug(url) {
  const m = (url || '').match(/linkedin\.com\/in\/([^/?#]+)/i);
  return m ? m[1].toLowerCase() : '';
}

function firstName(fullName) {
  const cleaned = (fullName || '')
    .replace(/[•|].*$/, '')
    .replace(/\s+/g, ' ')
    .trim();
  const part = cleaned.split(' ')[0] || 'there';
  return part.replace(/[^A-Za-z\-']/g, '') || 'there';
}

function isIndiaLocation(text) {
  const t = (text || '').toLowerCase();
  if (!t) return false;
  return INDIA_MARKERS.some((m) => t.includes(m));
}

function loadTemplate() {
  const data = loadJson(TEMPLATES_FILE, { variants: {} });
  const key = VARIANT || data.default_variant || 'hook';
  const tpl = data.variants?.[key] || data.variants?.hook;
  if (!tpl) throw new Error(`No DM template for variant=${key}`);
  return tpl;
}

function sanitizeMessage(text) {
  // LinkedIn copy rule: never use "--" / em/en dashes
  return String(text || '')
    .replace(/\u2014/g, ':') // em dash —
    .replace(/\u2013/g, ' to ') // en dash –
    .replace(/--+/g, ':')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/:([^\s])/g, ': $1')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();
}

function renderMessage(template, name) {
  return sanitizeMessage(template.replace(/\{\{\s*FirstName\s*\}\}/g, firstName(name)));
}

function connectBrowser() {
  const tmpRoots = [os.tmpdir(), process.env.TMPDIR, '/var/folders'].filter(Boolean);
  const dirs = [];
  for (const root of tmpRoots) {
    try {
      if (!fs.existsSync(root)) continue;
      // Direct children
      for (const name of fs.readdirSync(root)) {
        if (name.startsWith('agent-browser-chrome-') || name.startsWith('agent-browser-profile-')) {
          dirs.push(path.join(root, name));
        }
      }
      // macOS: /var/folders/.../T/agent-browser-*
      if (root === '/var/folders') {
        for (const a of fs.readdirSync(root)) {
          const aPath = path.join(root, a);
          if (!fs.statSync(aPath).isDirectory()) continue;
          for (const b of fs.readdirSync(aPath)) {
            const tPath = path.join(aPath, b, 'T');
            if (!fs.existsSync(tPath)) continue;
            for (const name of fs.readdirSync(tPath)) {
              if (name.startsWith('agent-browser-chrome-') || name.startsWith('agent-browser-profile-')) {
                dirs.push(path.join(tPath, name));
              }
            }
          }
        }
      }
    } catch (_) {}
  }

  const withPort = dirs
    .map((dir) => {
      const portFile = path.join(dir, 'DevToolsActivePort');
      if (!fs.existsSync(portFile)) return null;
      return { path: dir, mtime: fs.statSync(dir).mtimeMs, portFile };
    })
    .filter(Boolean)
    .sort((a, b) => b.mtime - a.mtime);

  if (!withPort.length) {
    throw new Error(
      'No agent-browser profile found. Launch: agent-browser --session linkedin_bot open https://www.linkedin.com/feed/'
    );
  }
  const port = fs.readFileSync(withPort[0].portFile, 'utf8').split('\n')[0].trim();
  return `http://127.0.0.1:${port}`;
}

async function clickByText(page, texts, opts = {}) {
  const { tags = ['button', 'a', '[role="button"]'], partial = true, exclude = [], minY = 0 } = opts;
  const handle = await page.evaluateHandle((textList, tagList, usePartial, excludeList, minYVal) => {
    function norm(s) {
      return (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
    }
    function excluded(label) {
      return excludeList.some((x) => label.includes(norm(x)));
    }
    function matches(el) {
      const label = norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
      if (!label || excluded(label)) return false;
      return textList.some((t) => {
        const target = norm(t);
        return usePartial ? label.includes(target) : label === target;
      });
    }
    let best = null;
    let bestScore = -1;
    for (const tag of tagList) {
      for (const el of document.querySelectorAll(tag)) {
        if (!matches(el)) continue;
        const rect = el.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0 || rect.y < minYVal) continue;
        const href = (el.getAttribute('href') || '').toLowerCase();
        let score = rect.y;
        if (href.includes('/messaging/compose')) score += 10000;
        if (score > bestScore) {
          best = el;
          bestScore = score;
        }
      }
    }
    return best;
  }, texts, tags, partial, exclude, minY);

  const el = handle.asElement();
  if (!el) return false;
  const box = await el.boundingBox();
  if (box) {
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  } else {
    try {
      await el.click({ delay: 40 });
    } catch {
      await page.evaluate((e) => e.click(), el);
    }
  }
  await el.dispose();
  return true;
}

async function openCompose(page) {
  // Prefer direct compose href on profile Message CTA (avoids top-nav Messaging)
  const composeHref = await page.evaluate(() => {
    const links = [...document.querySelectorAll('a[href*="/messaging/compose"]')];
    const visible = links.find((a) => {
      const r = a.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.y > 80;
    });
    return visible ? visible.href : '';
  });
  if (composeHref) {
    await page.goto(composeHref, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
    await new Promise((r) => setTimeout(r, 2500));
    return true;
  }
  return clickByText(page, ['Message'], {
    exclude: ['messaging', 'message requests', 'open profile'],
    minY: 100,
  });
}

async function dismissOverlays(page) {
  try {
    await page.evaluate(() => {
      document.querySelectorAll('button').forEach((b) => {
        const t = ((b.getAttribute('aria-label') || '') + ' ' + (b.innerText || '')).toLowerCase();
        if (t.includes('dismiss') || t === 'close' || t.includes('close your conversation')) {
          try {
            b.click();
          } catch (_) {}
        }
      });
    });
  } catch (_) {}
  try {
    await page.keyboard.press('Escape');
  } catch (_) {}
  await new Promise((r) => setTimeout(r, 400));
}

function buildSearchUrl(geoUrn) {
  const params = new URLSearchParams();
  params.set('network', '["F"]');
  params.set('origin', 'FACETED_SEARCH');
  params.set('geoUrn', `["${geoUrn}"]`);
  return `https://www.linkedin.com/search/results/people/?${params.toString()}`;
}

async function extractSearchResults(page) {
  return page.evaluate(() => {
    const seen = new Set();
    const results = [];

    function parseCard(card) {
      const link = card.querySelector('a[href*="/in/"]');
      if (!link) return null;
      let href = (link.href || link.getAttribute('href') || '').split('?')[0].replace(/\/$/, '');
      if (href.startsWith('/')) href = `https://www.linkedin.com${href}`;
      const m = href.match(/linkedin\.com\/in\/([^/?#]+)/i);
      if (!m) return null;
      const slug = m[1].toLowerCase();
      if (seen.has(slug) || slug.includes('mini') || slug === 'me') return null;
      seen.add(slug);

      const nameEl = link.querySelector('span[aria-hidden="true"]') || link;
      let name = (nameEl.innerText || nameEl.textContent || '').trim().split('\n')[0];
      const lines = (card.innerText || '').split('\n').map((l) => l.trim()).filter(Boolean);
      if (!name || /mutual connection/i.test(name) || name.length > 60) {
        name = lines.find((l) => l.length < 50 && !/mutual|connect|message|• \d/i.test(l)) || slug;
      }
      const title =
        lines.find(
          (l) => l !== name && l.length < 140 && !/connect|message|mutual|• \d|1st|2nd|3rd/i.test(l)
        ) || '';
      const location =
        lines.find(
          (l) =>
            l !== name &&
            l !== title &&
            l.length < 80 &&
            /(united states|united kingdom|canada|australia|germany|singapore|emirates|netherlands|france|saudi|remote|area|city)/i.test(
              l
            )
        ) || '';

      return { slug, name, title, location, linkedin_url: `${href}/` };
    }

    const selectors = [
      'li.reusable-search__result-container',
      'div[data-view-name="search-entity-result-universal-template"]',
      '.entity-result',
    ];
    for (const sel of selectors) {
      document.querySelectorAll(sel).forEach((card) => {
        const p = parseCard(card);
        if (p) results.push(p);
      });
      if (results.length) return results;
    }

    document.querySelectorAll('a[href*="/in/"]').forEach((a) => {
      const card = a.closest('li') || a.closest('[data-view-name]') || a.parentElement;
      if (!card) return;
      const p = parseCard(card);
      if (p) results.push(p);
    });
    return results;
  });
}

async function collectTargets(page, needed, already) {
  const found = [];
  const cache = loadJson(CACHE_FILE, { profiles: [] });
  const useCacheOnly = process.env.DM_USE_CACHE === '1';

  if (useCacheOnly && (cache.profiles || []).length) {
    for (const p of cache.profiles) {
      if (found.length >= needed) break;
      if (already.has(p.slug)) continue;
      if (isIndiaLocation(p.location) || isIndiaLocation(p.title)) continue;
      found.push(p);
    }
    console.log(`Using cache: ${found.length} targets`);
    return found;
  }

  for (const geo of GEO_TARGETS) {
    if (found.length >= needed) break;
    const url = buildSearchUrl(geo.urn);
    console.log(`\nSearching 1st-degree in ${geo.name}`);
    console.log(url);

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    } catch (err) {
      console.log(`Nav error: ${err.message}`);
      await new Promise((r) => setTimeout(r, 2000));
    }
    await new Promise((r) => setTimeout(r, 3500));
    await dismissOverlays(page);

    for (let scroll = 0; scroll < SEARCH_SCROLLS && found.length < needed; scroll++) {
      let batch = [];
      try {
        batch = await extractSearchResults(page);
      } catch (err) {
        console.log(`Extract error (retrying): ${err.message}`);
        await new Promise((r) => setTimeout(r, 2000));
        try {
          batch = await extractSearchResults(page);
        } catch (_) {
          break;
        }
      }
      for (const p of batch) {
        if (found.length >= needed) break;
        if (already.has(p.slug)) continue;
        if (found.some((x) => x.slug === p.slug)) continue;
        if (isIndiaLocation(p.location) || isIndiaLocation(p.title)) continue;
        found.push({ ...p, geo: geo.name });
      }
      try {
        await page.evaluate(() => window.scrollBy(0, window.innerHeight * 0.9));
      } catch (_) {}
      await new Promise((r) => setTimeout(r, 1800));
    }
  }

  cache.profiles = [...(cache.profiles || []), ...found]
    .reduce((acc, p) => {
      if (!acc.some((x) => x.slug === p.slug)) acc.push(p);
      return acc;
    }, [])
    .slice(-2000);
  cache.last_search = todayStr();
  saveJson(CACHE_FILE, cache);

  console.log(`Collected ${found.length} non-India 1st-degree targets`);
  return found;
}

async function readProfileLocation(page) {
  return page.evaluate(() => {
    const selectors = [
      '.text-body-small.inline.t-black--light.break-words',
      'span.text-body-small.inline.t-black--light',
      '[data-anonymize="location"]',
      '.pv-text-details__left-panel .text-body-small',
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      const t = (el?.innerText || '').trim();
      if (t && t.length < 120) return t;
    }
    const body = document.body.innerText || '';
    const lines = body.split('\n').map((l) => l.trim()).filter(Boolean);
    const hit = lines.find((l) =>
      /,/.test(l) &&
      l.length < 80 &&
      !/followers|connections|message|connect|about|experience/i.test(l)
    );
    return hit || '';
  });
}

async function getEditorHandle(page) {
  const handle = await page.evaluateHandle(() => {
    function find(root) {
      if (!root) return null;
      const direct =
        root.querySelector('.msg-form__contenteditable') ||
        root.querySelector('.msg-form .ql-editor') ||
        root.querySelector('[contenteditable="true"].ql-editor') ||
        root.querySelector('div[role="textbox"][contenteditable="true"]');
      if (direct) return direct;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while ((node = walker.nextNode())) {
        if (node.shadowRoot) {
          const found = find(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return find(document.body);
  });
  return handle.asElement();
}

async function fillMessage(page, text) {
  const editor = await getEditorHandle(page);
  if (!editor) return false;

  await editor.click({ clickCount: 1 });
  await new Promise((r) => setTimeout(r, 300));
  await page.evaluate((el) => {
    el.focus();
    el.innerHTML = '<p><br></p>';
    el.dispatchEvent(new InputEvent('input', { bubbles: true }));
  }, editor);

  try {
    const client = await page.createCDPSession();
    await client.send('Input.insertText', { text });
    await client.detach();
  } catch (_) {
    await page.keyboard.type(text, { delay: 5 });
  }

  const len = await editor.evaluate((el) => (el.innerText || '').trim().length);
  await editor.dispose();
  return len > 20;
}

async function waitForEditor(page, timeoutMs = 12000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const ready = await page.evaluate(() => {
      const el =
        document.querySelector('.msg-form__contenteditable') ||
        document.querySelector('.msg-form [contenteditable="true"]') ||
        document.querySelector('[aria-label*="Write a message"]');
      if (!el) return false;
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    }).catch(() => false);
    if (ready) return true;
    await new Promise((r) => setTimeout(r, 400));
  }
  return false;
}

async function withTimeout(promise, ms, label) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(`${label} timed out after ${ms}ms`)), ms);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

async function sendMessageOnProfile(page, prospect, message) {
  await dismissOverlays(page);
  try {
    await withTimeout(
      page.goto(prospect.linkedin_url, { waitUntil: 'domcontentloaded', timeout: 35000 }),
      40000,
      'profile nav'
    );
  } catch (err) {
    if (!/ERR_ABORTED/i.test(err.message)) {
      // soft continue if URL already matches
      if (!String(page.url()).includes(prospect.slug)) {
        return { status: 'failed', error: `nav: ${err.message}` };
      }
    }
  }
  await new Promise((r) => setTimeout(r, 2800));
  await dismissOverlays(page);

  let location = '';
  try {
    location = await withTimeout(readProfileLocation(page), 10000, 'location');
  } catch (_) {}
  if (isIndiaLocation(location)) {
    return { status: 'skipped_india', location };
  }

  let opened = false;
  try {
    opened = await withTimeout(openCompose(page), 25000, 'open compose');
  } catch (err) {
    return { status: 'failed', error: err.message, location };
  }
  if (!opened) {
    return { status: 'failed', error: 'Message button not found', location };
  }

  await new Promise((r) => setTimeout(r, 1200));
  const editorReady = await waitForEditor(page, 10000);
  if (!editorReady) {
    return { status: 'failed', error: 'Message editor not ready', location };
  }

  const filled = await fillMessage(page, message);
  if (!filled) {
    return { status: 'failed', error: 'Could not fill message editor', location };
  }

  await new Promise((r) => setTimeout(r, 600));

  if (DRY_RUN) {
    return { status: 'dry_run', location, preview: message.slice(0, 120) };
  }

  let sent = false;
  try {
    sent = await page.evaluate(() => {
      const btn =
        document.querySelector('button.msg-form__send-button:not([disabled])') ||
        document.querySelector('.msg-form button[type="submit"]:not([disabled])');
      if (!btn) return false;
      btn.click();
      return true;
    });
  } catch (_) {}

  if (!sent) {
    sent = await clickByText(page, ['Send'], {
      tags: ['button'],
      exclude: ['send invitation', 'send without', 'send profile'],
      minY: 100,
    });
  }

  if (!sent) {
    const mod = process.platform === 'darwin' ? 'Meta' : 'Control';
    await page.keyboard.down(mod);
    await page.keyboard.press('Enter');
    await page.keyboard.up(mod);
  }

  await new Promise((r) => setTimeout(r, 1800));

  const blocked = await page.evaluate(() => {
    const t = (document.body.innerText || '').toLowerCase();
    if (t.includes('weekly limit') || t.includes('messaging limit') || t.includes('too many messages')) {
      return 'limit_reached';
    }
    return null;
  }).catch(() => null);
  if (blocked) return { status: blocked, location };

  return { status: 'sent', location };
}

async function main() {
  const template = loadTemplate();
  const log = loadJson(LOG_FILE, []);
  const today = todayStr();
  const sentToday = log.filter((e) => e.date === today && e.status === 'sent').length;
  const already = new Set(
    log
      .filter((e) => ['sent', 'skipped_india'].includes(e.status) && !e.dry_run)
      .map((e) => profileSlug(e.linkedin_url || e.slug))
      .filter(Boolean)
  );

  const remainingDay = Math.max(0, MAX_PER_DAY - sentToday);
  const budget = Math.min(MAX_PER_RUN, remainingDay);

  console.log('== LinkedIn DMs → non-India 1st-degree connections ==');
  console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE SEND'}`);
  console.log(`Variant: ${VARIANT}`);
  console.log(`Already sent today: ${sentToday} | Run budget: ${budget}`);

  if (budget <= 0) {
    console.log('Daily DM cap reached. Increase MAX_DMS_PER_DAY to continue.');
    return;
  }

  const browserURL = connectBrowser();
  console.log(`Connecting to browser at ${browserURL}...`);
  const browser = await puppeteer.connect({
    browserURL,
    defaultViewport: null,
    protocolTimeout: 120000,
  });

  // Prefer an already-authenticated LinkedIn tab (new tabs often hit login wall)
  const pages = await browser.pages();
  let page = null;
  for (const p of pages) {
    const u = p.url();
    if (!/linkedin\.com/i.test(u)) continue;
    if (/\/(login|uas\/login|checkpoint)/i.test(u)) continue;
    try {
      const ok = await p.evaluate(() => {
        const t = document.body?.innerText || '';
        return /My Network|Messaging|Start a post/i.test(t) && !/^Welcome back/i.test(t.trim());
      });
      if (ok) {
        page = p;
        break;
      }
    } catch (_) {}
  }
  if (!page) {
    page = await browser.newPage();
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
    await new Promise((r) => setTimeout(r, 2500));
    const blocked = /\/(login|uas\/login|checkpoint)/i.test(page.url());
    if (blocked) {
      console.error('LinkedIn session requires login. Sign in in the agent-browser window, then re-run.');
      await browser.disconnect();
      process.exit(2);
    }
  }
  page.setDefaultTimeout(45000);
  page.setDefaultNavigationTimeout(45000);
  await page.bringToFront();
  console.log(`Using tab: ${page.url()}`);
  // Soft navigate to feed only if needed
  if (!/linkedin\.com\/(feed|messaging|in\/|search)/i.test(page.url())) {
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
    await new Promise((r) => setTimeout(r, 2000));
  }

  const targets = await collectTargets(page, Math.max(budget * 3, SEARCH_BATCH), already);
  if (!targets.length) {
    console.log('No targets found. Are you logged into LinkedIn?');
    await browser.disconnect();
    return;
  }

  let sent = 0;
  let failed = 0;
  let skipped = 0;
  let attempts = 0;
  let consecutiveFails = 0;
  const maxAttempts = Math.min(targets.length, budget * 4);

  for (const prospect of targets) {
    if (sent >= budget || attempts >= maxAttempts) break;
    attempts += 1;

    const message = renderMessage(template, prospect.name);
    console.log('\n==================================================');
    console.log(`${DRY_RUN ? 'Preview' : 'Messaging'}: ${prospect.name}`);
    console.log(`  ${prospect.title || ''}`);
    console.log(`  ${prospect.linkedin_url} (${prospect.geo || ''})`);
    console.log('==================================================');

    let result;
    try {
      result = await sendMessageOnProfile(page, prospect, message);
    } catch (err) {
      result = { status: 'failed', error: err.message };
    }

    const entry = {
      date: today,
      ts: new Date().toISOString(),
      slug: prospect.slug,
      name: prospect.name,
      title: prospect.title,
      linkedin_url: prospect.linkedin_url,
      geo: prospect.geo,
      variant: VARIANT,
      status: result.status,
      location: result.location || '',
      error: result.error || '',
      dry_run: DRY_RUN,
    };
    appendLog(entry);
    already.add(prospect.slug);

    console.log(`Result: ${result.status}${result.error ? ` (${result.error})` : ''}`);
    if (result.status === 'sent' || result.status === 'dry_run') {
      sent += 1;
      consecutiveFails = 0;
    } else if (result.status === 'skipped_india') {
      skipped += 1;
      consecutiveFails = 0;
    } else {
      failed += 1;
      consecutiveFails += 1;
    }

    if (result.status === 'limit_reached') {
      console.log('LinkedIn messaging limit hit — stopping.');
      break;
    }
    if (consecutiveFails >= 8) {
      console.log('Too many consecutive failures (likely messaging limit/UI block). Stopping.');
      break;
    }

    await dismissOverlays(page);
    if (sent < budget) {
      console.log(`Waiting ${DELAY_MS}ms before next...`);
      await new Promise((r) => setTimeout(r, DELAY_MS));
    }
  }

  console.log('\n== Summary ==');
  console.log(`Sent/previewed: ${sent}`);
  console.log(`Skipped (India): ${skipped}`);
  console.log(`Failed: ${failed}`);
  console.log(`Log: ${LOG_FILE}`);

  await browser.disconnect();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
