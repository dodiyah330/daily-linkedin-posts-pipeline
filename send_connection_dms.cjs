#!/usr/bin/env node
/**
 * Send LinkedIn DMs to 1st-degree connections outside India.
 *
 * Requires: agent-browser --session linkedin_bot open https://www.linkedin.com/feed/
 *
 * SAFETY (Jul 2026): LinkedIn restricted this account for high profile-data volume
 * after ~77–145 DMs/day + aggressive search. Caps below are non-bypassable.
 *
 * Env:
 *   DRY_RUN=1                 Discover/filter only, do not send
 *   MAX_DMS_PER_RUN=3          Cap per script run (absolute max 5; prefer 2–3)
 *   MAX_DMS_PER_DAY=15         Cap per calendar day (absolute max 15)
 *   MAX_DMS_PER_HOUR=2         Cap per rolling hour (absolute max 3)
 *   MAX_DMS_PER_WEEK=60        Cap per rolling 7 days (absolute max 70)
 *   DM_DELAY_MS=180000         Base pause between sends (min 120s)
 *   DM_DELAY_JITTER_MS=120000  Random extra wait 0..N ms
 *   DM_HUMANIZE=1              Human-like browse/type/mouse (default on)
 *   DM_VARIANT=auto           auto|founder|ops|sales|...
 *   DM_SCROLLS=4              Scrolls while collecting search results
 *   DM_SEARCH_BATCH=25        Max prospects to collect before filtering
 *   DM_MAX_GEO_SEARCHES=3     Max countries to search per run (cache preferred)
 *   DM_USE_CACHE=1            Prefer cached remaining targets (default on)
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const LOG_FILE = path.join(__dirname, 'connection-dms-run-log.json');
const CACHE_FILE = path.join(__dirname, 'connection-dms-targets-cache.json');
const TEMPLATES_FILE = path.join(__dirname, 'connection_dm_templates.json');

const DRY_RUN = process.env.DRY_RUN === '1';
const DELAY_MS = parseInt(process.env.DM_DELAY_MS || '180000', 10);
const DELAY_JITTER_MS = parseInt(process.env.DM_DELAY_JITTER_MS || '120000', 10);
const MAX_PER_RUN = parseInt(process.env.MAX_DMS_PER_RUN || '3', 10);
const MAX_PER_DAY = parseInt(process.env.MAX_DMS_PER_DAY || '15', 10);
const MAX_PER_HOUR = parseInt(process.env.MAX_DMS_PER_HOUR || '2', 10);
const MAX_PER_WEEK = parseInt(process.env.MAX_DMS_PER_WEEK || '60', 10);
const VARIANT = process.env.DM_VARIANT || 'auto';
const SEARCH_SCROLLS = parseInt(process.env.DM_SCROLLS || '4', 10);
const SEARCH_BATCH = parseInt(process.env.DM_SEARCH_BATCH || '25', 10);
const MAX_GEO_SEARCHES = parseInt(process.env.DM_MAX_GEO_SEARCHES || '3', 10);
const USE_CACHE = process.env.DM_USE_CACHE !== '0';
const HUMANIZE = process.env.DM_HUMANIZE !== '0';

// Absolute ceilings — cannot be raised via env (past ALLOW_UNSAFE caused restrictions).
// LinkedIn cited "unusually high volume of LinkedIn profile data" at ~77+/day.
// Sustain by looking human + spreading volume, not by blasting.
const ABSOLUTE_MAX_RUN = 5;
const ABSOLUTE_MAX_DAY = 15;
const ABSOLUTE_MAX_HOUR = 3;
const ABSOLUTE_MAX_WEEK = 70;
const HARD_MIN_DELAY_MS = 120000;
const RECOVERY_STRICT_DAY = 8;
const RECOVERY_STRICT_RUN = 2;
const RECOVERY_STRICT_HOUR = 2;
const RECOVERY_EASING_DAY = 12;
const RECOVERY_EASING_RUN = 3;
const RECOVERY_EASING_HOUR = 2;
const RECOVERY_DAYS = 14;
const RECOVERY_STRICT_DAYS = 7;

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

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function chance(p) {
  return Math.random() < p;
}

function nextDelayMs(baseDelayMs) {
  const base = Math.max(baseDelayMs || DELAY_MS, HARD_MIN_DELAY_MS);
  const jitter = DELAY_JITTER_MS > 0 ? Math.floor(Math.random() * (DELAY_JITTER_MS + 1)) : 0;
  // Occasional "got distracted" pause: longer gap like a real session break
  const longBreak = HUMANIZE && chance(0.18) ? randInt(45000, 120000) : 0;
  return base + jitter + longBreak;
}

async function humanIdle(minMs = 400, maxMs = 1400) {
  await sleep(randInt(minMs, maxMs));
}

async function humanMouseWander(page) {
  if (!HUMANIZE) return;
  try {
    const vp = page.viewport() || { width: 1280, height: 800 };
    const steps = randInt(2, 5);
    for (let i = 0; i < steps; i++) {
      const x = randInt(80, Math.max(120, vp.width - 80));
      const y = randInt(120, Math.max(200, vp.height - 100));
      await page.mouse.move(x, y, { steps: randInt(8, 22) });
      await sleep(randInt(80, 280));
    }
  } catch (_) {}
}

async function humanScrollRead(page) {
  if (!HUMANIZE) {
    await sleep(1200);
    return;
  }
  await humanMouseWander(page);
  const scrolls = randInt(1, 3);
  for (let i = 0; i < scrolls; i++) {
    const delta = randInt(220, 520) * (chance(0.15) ? -1 : 1);
    try {
      await page.mouse.wheel({ deltaY: delta });
    } catch (_) {
      try {
        await page.evaluate((dy) => window.scrollBy(0, dy), Math.abs(delta));
      } catch (_) {}
    }
    await sleep(randInt(700, 2200));
  }
  // Settle on upper profile before Message CTA
  try {
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  } catch (_) {}
  await sleep(randInt(900, 2200));
}

async function humanClickElement(page, el) {
  const box = await el.boundingBox().catch(() => null);
  if (box) {
    const x = box.x + box.width * (0.3 + Math.random() * 0.4);
    const y = box.y + box.height * (0.3 + Math.random() * 0.4);
    if (HUMANIZE) {
      await page.mouse.move(x, y, { steps: randInt(10, 28) });
      await sleep(randInt(80, 320));
    }
    await page.mouse.click(x, y, { delay: HUMANIZE ? randInt(40, 120) : 40 });
    return true;
  }
  try {
    await el.click({ delay: HUMANIZE ? randInt(40, 120) : 40 });
    return true;
  } catch {
    await page.evaluate((e) => e.click(), el);
    return true;
  }
}

async function betweenDmBrowse(page) {
  if (!HUMANIZE || !chance(0.55)) return;
  const mode = chance(0.55) ? 'feed' : 'messaging';
  console.log(`  human browse: ${mode} (looks like a real session)...`);
  try {
    if (mode === 'feed') {
      await page.goto('https://www.linkedin.com/feed/', {
        waitUntil: 'domcontentloaded',
        timeout: 35000,
      }).catch(() => {});
      await sleep(randInt(2000, 4500));
      await humanScrollRead(page);
      await humanIdle(1500, 5000);
    } else {
      await page.goto('https://www.linkedin.com/messaging/', {
        waitUntil: 'domcontentloaded',
        timeout: 35000,
      }).catch(() => {});
      await sleep(randInt(2000, 4000));
      await humanMouseWander(page);
      await humanIdle(1200, 3500);
    }
  } catch (_) {}
}

function lastRestrictionTs(log) {
  let latest = 0;
  for (const e of log) {
    const ts = e.ts ? Date.parse(e.ts) : 0;
    if (!ts) continue;
    if (['restricted', 'limit_reached'].includes(e.status)) {
      latest = Math.max(latest, ts);
      continue;
    }
    const err = String(e.error || '').toLowerCase();
    if (/restrict|checkpoint|unusual activity|messaging limit|too many messages/.test(err)) {
      latest = Math.max(latest, ts);
    }
  }
  // Burst days also count as restriction signal
  const byDay = {};
  for (const e of log) {
    if (e.status !== 'sent' || e.dry_run || !e.date || !e.ts) continue;
    byDay[e.date] = byDay[e.date] || { n: 0, ts: 0 };
    byDay[e.date].n += 1;
    byDay[e.date].ts = Math.max(byDay[e.date].ts, Date.parse(e.ts) || 0);
  }
  for (const d of Object.values(byDay)) {
    if (d.n >= 40) latest = Math.max(latest, d.ts);
  }
  return latest || 0;
}

function recoveryStage(log) {
  const ts = lastRestrictionTs(log);
  if (!ts) return null;
  const daysAgo = (Date.now() - ts) / (24 * 60 * 60 * 1000);
  if (daysAgo > RECOVERY_DAYS) return null;
  if (daysAgo <= RECOVERY_STRICT_DAYS) return 'strict';
  return 'easing';
}

function recentlyRestricted(log) {
  return Boolean(recoveryStage(log));
}

function countSentInLastDays(log, days, opts = {}) {
  const since = Date.now() - days * 24 * 60 * 60 * 1000;
  const byDay = {};
  for (const e of log) {
    if (e.status !== 'sent' || e.dry_run) continue;
    if (!e.ts || Date.parse(e.ts) < since) continue;
    const d = e.date || String(e.ts).slice(0, 10);
    byDay[d] = (byDay[d] || 0) + 1;
  }
  // Past burst days (≥40) already caused restriction — don't let them block safe resume.
  if (opts.excludeBurstDays) {
    return Object.values(byDay).reduce((sum, n) => sum + (n >= 40 ? 0 : n), 0);
  }
  return Object.values(byDay).reduce((sum, n) => sum + n, 0);
}

function enforceSafeLimits(log) {
  const stage = recoveryStage(log);
  if (stage === 'strict') {
    console.log(
      `Recovery STRICT (≤${RECOVERY_STRICT_DAYS}d since restriction signal): tight caps`
    );
  } else if (stage === 'easing') {
    console.log(
      `Recovery EASING (${RECOVERY_STRICT_DAYS + 1}–${RECOVERY_DAYS}d): raising toward ~${ABSOLUTE_MAX_DAY}/day`
    );
  }

  // Absolute ceilings always apply — ALLOW_UNSAFE_DM_LIMITS is ignored for max volume.
  if (process.env.ALLOW_UNSAFE_DM_LIMITS === '1') {
    console.log(
      'NOTE: ALLOW_UNSAFE_DM_LIMITS is ignored. Absolute caps always apply to protect the account.'
    );
  }

  let dayCap = ABSOLUTE_MAX_DAY;
  let runCap = ABSOLUTE_MAX_RUN;
  let hourCap = ABSOLUTE_MAX_HOUR;
  if (stage === 'strict') {
    dayCap = RECOVERY_STRICT_DAY;
    runCap = RECOVERY_STRICT_RUN;
    hourCap = RECOVERY_STRICT_HOUR;
  } else if (stage === 'easing') {
    dayCap = RECOVERY_EASING_DAY;
    runCap = RECOVERY_EASING_RUN;
    hourCap = RECOVERY_EASING_HOUR;
  } else {
    // Healthy: prefer small human sessions even when day cap is 15
    runCap = Math.min(runCap, 3);
    hourCap = Math.min(hourCap, 2);
  }

  const clamped = {
    maxRun: Math.min(MAX_PER_RUN, runCap),
    maxDay: Math.min(MAX_PER_DAY, dayCap),
    maxHour: Math.min(MAX_PER_HOUR, hourCap),
    maxWeek: Math.min(MAX_PER_WEEK, ABSOLUTE_MAX_WEEK),
    delayMs: Math.max(DELAY_MS, HARD_MIN_DELAY_MS),
    recovery: Boolean(stage),
    stage: stage || 'healthy',
  };

  if (
    clamped.maxRun !== MAX_PER_RUN ||
    clamped.maxDay !== MAX_PER_DAY ||
    clamped.maxHour !== MAX_PER_HOUR ||
    clamped.maxWeek !== MAX_PER_WEEK ||
    clamped.delayMs !== DELAY_MS
  ) {
    console.log(
      `Safety clamp: run=${clamped.maxRun}/day=${clamped.maxDay}/hour=${clamped.maxHour}/week=${clamped.maxWeek} delay>=${clamped.delayMs}ms`
    );
  }
  console.log(
    `Humanize: ${HUMANIZE ? 'ON' : 'OFF'} | stage=${clamped.stage} | tip: 4–6 tiny sessions/day beats one burst`
  );
  return clamped;
}

function countSentSince(log, sinceMs) {
  return log.filter(
    (e) =>
      e.status === 'sent' &&
      !e.dry_run &&
      e.ts &&
      Date.parse(e.ts) >= sinceMs
  ).length;
}

async function detectRestriction(page) {
  const url = page.url() || '';
  if (/\/(checkpoint|challenge|uas\/login|login)/i.test(url)) {
    return 'checkpoint_or_login';
  }
  return page
    .evaluate(() => {
      const t = (document.body?.innerText || '').toLowerCase();
      const patterns = [
        'we restricted your account',
        'your account has been restricted',
        'temporarily restricted',
        'unusual activity',
        'verify your identity',
        'confirm your identity',
        'weekly invitation limit',
        'weekly limit',
        'messaging limit',
        'too many messages',
        "you've reached the weekly",
        'try again later',
        'action blocked',
        'security verification',
      ];
      for (const p of patterns) {
        if (t.includes(p)) return p;
      }
      return null;
    })
    .catch(() => null);
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

function loadTemplates() {
  const data = loadJson(TEMPLATES_FILE, { variants: {}, role_rules: [] });
  if (!data.variants || !Object.keys(data.variants).length) {
    throw new Error('No DM templates found in connection_dm_templates.json');
  }
  return data;
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

function cleanHeadline(text, name) {
  let t = String(text || '')
    .replace(/\s+/g, ' ')
    .replace(/[•·].*$/, '')
    .trim();
  if (!t) return '';
  if (/skip to|notifications?|followers|connections|^home$|^messaging$/i.test(t)) return '';
  const nameNorm = String(name || '').replace(/\s+/g, ' ').trim().toLowerCase();
  if (nameNorm && t.toLowerCase() === nameNorm) return '';
  // Keep a short role phrase for the generic template; don't truncate mid-word harshly
  if (t.length > 90) t = t.slice(0, 87).replace(/\s+\S*$/, '').trim() + '...';
  return t;
}

function detectRole(templates, prospect) {
  const blob = `${prospect.title || ''} ${prospect.headline || ''} ${prospect.location || ''}`.toLowerCase();
  const rules = templates.role_rules || [];
  for (const rule of rules) {
    const kws = rule.keywords || [];
    if (kws.some((k) => blob.includes(String(k).toLowerCase()))) {
      return { variant: rule.variant, label: rule.label || rule.variant };
    }
  }
  return { variant: 'generic', label: 'your space' };
}

function pickVariant(templates, prospect) {
  const requested = (VARIANT || templates.default_variant || 'auto').toLowerCase();
  if (requested && requested !== 'auto' && templates.variants[requested]) {
    return {
      variant: requested,
      label: (templates.role_rules || []).find((r) => r.variant === requested)?.label || requested,
    };
  }
  const detected = detectRole(templates, prospect);
  if (templates.variants[detected.variant]) return detected;
  return { variant: 'generic', label: 'your space' };
}

function renderMessage(templates, prospect) {
  const picked = pickVariant(templates, prospect);
  const template =
    templates.variants[picked.variant] ||
    templates.variants.generic ||
    Object.values(templates.variants)[0];
  const headline = cleanHeadline(prospect.headline || prospect.title, prospect.name);
  const headlineBit = headline ? ` (${headline})` : '';
  const text = String(template)
    .replace(/\{\{\s*FirstName\s*\}\}/g, firstName(prospect.name))
    .replace(/\{\{\s*RoleLabel\s*\}\}/g, picked.label || 'your space')
    .replace(/\{\{\s*HeadlineBit\s*\}\}/g, headlineBit)
    .replace(/\{\{\s*Headline\s*\}\}/g, headline || 'your work');
  return {
    message: sanitizeMessage(text),
    variant: picked.variant,
    label: picked.label,
    headline,
  };
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
  await humanClickElement(page, el);
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

async function collectTargets(page, needed, already, opts = {}) {
  const found = [];
  const cache = loadJson(CACHE_FILE, { profiles: [] });
  const useCache = opts.forceSearch ? false : USE_CACHE;

  // Prefer cache (remaining targets) to avoid aggressive search scraping.
  if (useCache && (cache.profiles || []).length) {
    for (const p of cache.profiles) {
      if (found.length >= needed) break;
      if (already.has(p.slug)) continue;
      if (isIndiaLocation(p.location) || isIndiaLocation(p.title)) continue;
      found.push(p);
    }
    if (found.length) {
      console.log(`Using cache: ${found.length} remaining targets (set DM_USE_CACHE=0 to re-search)`);
      return found;
    }
    console.log('Cache has no unused targets — searching LinkedIn...');
  }

  // Limit country searches — sweeping all geos looks like bulk profile-data scraping.
  const geoLimit = Math.max(1, Math.min(MAX_GEO_SEARCHES, GEO_TARGETS.length));
  const geos = GEO_TARGETS.slice(0, geoLimit);
  console.log(`Live search limited to ${geos.length} geo(s) this run (DM_MAX_GEO_SEARCHES)`);

  for (const geo of geos) {
    if (found.length >= needed) break;
    const url = buildSearchUrl(geo.urn);
    console.log(`\nSearching 1st-degree in ${geo.name}`);
    console.log(url);

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    } catch (err) {
      console.log(`Nav error: ${err.message}`);
      await sleep(2000);
    }
    await sleep(3500);
    await dismissOverlays(page);

    for (let scroll = 0; scroll < SEARCH_SCROLLS && found.length < needed; scroll++) {
      let batch = [];
      try {
        batch = await extractSearchResults(page);
      } catch (err) {
        console.log(`Extract error (retrying): ${err.message}`);
        await sleep(2000);
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
      await sleep(2200);
    }
    // Pause between geo searches to reduce profile-data velocity
    if (found.length < needed) await sleep(4000);
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

async function readProfileContext(page) {
  return page.evaluate(() => {
    function clean(s) {
      return (s || '').replace(/\s+/g, ' ').trim();
    }

    const pronoun = /^(he\/him|she\/her|they\/them|he\/they|she\/they)$/i;
    const degree = /^[·•]?\s*\d+(st|nd|rd|th)$/i;
    const stopSection = /^(about|activity|experience|education|skills|featured|interests|message|connect|more|contact info|highlights|services)$/i;
    const junkLine =
      /skip to|notifications?|followers|connections|mutual connection|get verified|premium|open to|contact info/i;

    const main = document.querySelector('main') || document.body;
    const lines = (main.innerText || '')
      .split('\n')
      .map((l) => clean(l))
      .filter(Boolean)
      .slice(0, 35);

    // Name is usually the first real profile heading line
    let nameIdx = lines.findIndex(
      (l) =>
        l.length > 1 &&
        l.length < 80 &&
        !junkLine.test(l) &&
        !stopSection.test(l) &&
        !pronoun.test(l) &&
        !degree.test(l)
    );
    if (nameIdx < 0) nameIdx = 0;

    let headline = '';
    let location = '';
    for (let i = nameIdx + 1; i < Math.min(lines.length, nameIdx + 12); i++) {
      const l = lines[i];
      if (!l || stopSection.test(l) || junkLine.test(l)) {
        if (stopSection.test(l)) break;
        continue;
      }
      if (pronoun.test(l) || degree.test(l) || l === '·' || l === '•') continue;
      if (!location && (/,/.test(l) || /\b(Area|Remote|United|Kingdom|States|Canada|Australia|Emirates|Germany|France|Ireland|Netherlands)\b/i.test(l)) && l.length < 100) {
        location = l;
        continue;
      }
      if (!headline && l.length >= 3 && l.length <= 160 && !/,/.test(l)) {
        headline = l;
      }
      if (headline && location) break;
    }

    // CSS fallbacks for older LinkedIn markup
    if (!headline) {
      const el =
        document.querySelector('[data-anonymize="headline"]') ||
        document.querySelector('.pv-text-details__left-panel .text-body-medium') ||
        document.querySelector('.text-body-medium.break-words');
      const t = clean(el?.innerText);
      if (t && t.length < 180 && !junkLine.test(t)) headline = t;
    }
    if (!location) {
      const el =
        document.querySelector('[data-anonymize="location"]') ||
        document.querySelector('.text-body-small.inline.t-black--light.break-words');
      const t = clean(el?.innerText);
      if (t && t.length < 120 && !junkLine.test(t)) location = t;
    }

    return { location, headline };
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

  await humanClickElement(page, editor);
  await humanIdle(250, 700);
  await page.evaluate((el) => {
    el.focus();
    el.innerHTML = '<p><br></p>';
    el.dispatchEvent(new InputEvent('input', { bubbles: true }));
  }, editor);

  if (HUMANIZE) {
    // Type like a person: variable key delay, pauses at punctuation / newlines
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      await page.keyboard.type(ch, { delay: 0 });
      let pause = randInt(28, 95);
      if (ch === '\n') pause = randInt(220, 700);
      else if (/[,.;:?]/.test(ch)) pause = randInt(120, 380);
      else if (ch === ' ' && chance(0.08)) pause = randInt(180, 520);
      else if (chance(0.03)) pause = randInt(250, 900); // think / typo hesitation
      await sleep(pause);
    }
  } else {
    try {
      const client = await page.createCDPSession();
      await client.send('Input.insertText', { text });
      await client.detach();
    } catch (_) {
      await page.keyboard.type(text, { delay: 5 });
    }
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

async function sendMessageOnProfile(page, prospect, templates) {
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
  await sleep(HUMANIZE ? randInt(2200, 4800) : 2800);
  await dismissOverlays(page);
  await humanScrollRead(page);

  let location = '';
  let headline = prospect.headline || prospect.title || '';
  try {
    const ctx = await withTimeout(readProfileContext(page), 10000, 'profile context');
    location = ctx.location || '';
    if (ctx.headline) headline = ctx.headline;
  } catch (_) {}
  if (isIndiaLocation(location) || isIndiaLocation(headline)) {
    return { status: 'skipped_india', location, headline };
  }

  const personalized = renderMessage(templates, {
    ...prospect,
    title: prospect.title || headline,
    headline,
  });
  const message = personalized.message;

  let opened = false;
  try {
    opened = await withTimeout(openCompose(page), 25000, 'open compose');
  } catch (err) {
    return { status: 'failed', error: err.message, location, headline, variant: personalized.variant };
  }
  if (!opened) {
    return { status: 'failed', error: 'Message button not found', location, headline, variant: personalized.variant };
  }

  await sleep(HUMANIZE ? randInt(900, 2200) : 1200);
  const editorReady = await waitForEditor(page, 10000);
  if (!editorReady) {
    return { status: 'failed', error: 'Message editor not ready', location, headline, variant: personalized.variant };
  }

  const filled = await fillMessage(page, message);
  if (!filled) {
    return { status: 'failed', error: 'Could not fill message editor', location, headline, variant: personalized.variant };
  }

  // Re-read draft before send (humans pause here)
  await sleep(HUMANIZE ? randInt(1800, 5200) : 600);
  await humanMouseWander(page);

  if (DRY_RUN) {
    return {
      status: 'dry_run',
      location,
      headline,
      variant: personalized.variant,
      preview: message.slice(0, 160),
    };
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

  await sleep(HUMANIZE ? randInt(1500, 3200) : 1800);

  const blocked = await detectRestriction(page);
  if (blocked) {
    if (/limit|too many messages|try again later/i.test(blocked)) {
      return { status: 'limit_reached', location, headline, error: blocked, variant: personalized.variant };
    }
    return { status: 'restricted', location, headline, error: blocked, variant: personalized.variant };
  }

  return { status: 'sent', location, headline, variant: personalized.variant, label: personalized.label };
}

async function main() {
  const log = loadJson(LOG_FILE, []);
  const limits = enforceSafeLimits(log);
  const templates = loadTemplates();
  const today = todayStr();
  const now = Date.now();
  const sentToday = log.filter((e) => e.date === today && e.status === 'sent' && !e.dry_run).length;
  const sentLastHour = countSentSince(log, now - 60 * 60 * 1000);
  const sentLastWeek = countSentInLastDays(log, 7, { excludeBurstDays: true });
  const already = new Set(
    log
      .filter((e) => ['sent', 'skipped_india'].includes(e.status) && !e.dry_run)
      .map((e) => profileSlug(e.linkedin_url || e.slug) || String(e.slug || '').toLowerCase())
      .filter(Boolean)
  );

  const remainingDay = Math.max(0, limits.maxDay - sentToday);
  const remainingHour = Math.max(0, limits.maxHour - sentLastHour);
  const remainingWeek = Math.max(0, limits.maxWeek - sentLastWeek);
  const budget = Math.min(limits.maxRun, remainingDay, remainingHour, remainingWeek);

  console.log('== LinkedIn DMs → non-India 1st-degree connections ==');
  console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE SEND'}`);
  console.log(`Variant mode: ${VARIANT} (role-personalized when auto)`);
  console.log(
    `Caps: run=${limits.maxRun} day=${limits.maxDay} hour=${limits.maxHour} week=${limits.maxWeek} | delay≈${limits.delayMs}+0..${DELAY_JITTER_MS}ms`
  );
  console.log(
    `Already sent today: ${sentToday} | last hour: ${sentLastHour} | last 7d: ${sentLastWeek} | Run budget: ${budget}`
  );
  console.log(`Already messaged (all time): ${already.size}`);
  console.log(
    `Safe guidance: ${limits.maxDay}/day via short sessions (≤${limits.maxHour}/hour). Absolute max ${ABSOLUTE_MAX_DAY}/day — 50–200/day caused restriction.`
  );

  if (budget <= 0) {
    if (remainingDay <= 0) {
      console.log('Daily DM cap reached. Resume tomorrow (safe default).');
    } else if (remainingHour <= 0) {
      console.log('Hourly DM cap reached. Wait ~1 hour, then re-run.');
    } else if (remainingWeek <= 0) {
      console.log('Weekly DM cap reached. Resume next week.');
    } else {
      console.log('Run budget is 0.');
    }
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
    await sleep(2000);
  }

  const preRestrict = await detectRestriction(page);
  if (preRestrict) {
    console.error(`LinkedIn restriction/challenge detected before sending: ${preRestrict}`);
    console.error('Resolve it in the browser, wait if needed, then re-run with low caps.');
    await browser.disconnect();
    process.exit(3);
  }

  // Only collect what we need for this small budget — avoid bulk profile-data scraping.
  const need = Math.min(Math.max(budget + 8, budget * 2), SEARCH_BATCH);
  let targets = await collectTargets(page, need, already);
  if (targets.length < budget) {
    console.log(`Only ${targets.length} cached targets (need ${budget}) — light search for more...`);
    const more = await collectTargets(page, need, already, { forceSearch: true });
    const seen = new Set(targets.map((t) => t.slug));
    for (const p of more) {
      if (seen.has(p.slug)) continue;
      targets.push(p);
      seen.add(p.slug);
    }
  }
  if (!targets.length) {
    console.log('No remaining targets in cache/search. Done, or wait for new connections.');
    await browser.disconnect();
    return;
  }
  console.log(`Queue ready: ${Math.min(targets.length, need)} targets for budget ${budget}`);
  targets = targets.slice(0, Math.max(need, budget * 2));

  let sent = 0;
  let failed = 0;
  let skipped = 0;
  let attempts = 0;
  let consecutiveFails = 0;
  const maxAttempts = Math.min(targets.length, Math.max(budget * 3, budget + 20));
  const variantCounts = {};

  for (const prospect of targets) {
    if (sent >= budget || attempts >= maxAttempts) break;
    attempts += 1;

    console.log('\n==================================================');
    console.log(`${DRY_RUN ? 'Preview' : 'Messaging'}: ${prospect.name}`);
    console.log(`  ${prospect.title || ''}`);
    console.log(`  ${prospect.linkedin_url} (${prospect.geo || ''})`);
    console.log('==================================================');

    let result;
    try {
      result = await sendMessageOnProfile(page, prospect, templates);
    } catch (err) {
      result = { status: 'failed', error: err.message };
    }

    const usedVariant = result.variant || VARIANT;
    variantCounts[usedVariant] = (variantCounts[usedVariant] || 0) + (result.status === 'sent' ? 1 : 0);

    const entry = {
      date: today,
      ts: new Date().toISOString(),
      slug: prospect.slug,
      name: prospect.name,
      title: prospect.title,
      headline: result.headline || '',
      linkedin_url: prospect.linkedin_url,
      geo: prospect.geo,
      variant: usedVariant,
      status: result.status,
      location: result.location || '',
      error: result.error || '',
      dry_run: DRY_RUN,
    };
    appendLog(entry);
    already.add(prospect.slug);

    console.log(
      `Result: ${result.status}${result.error ? ` (${result.error})` : ''}` +
        (usedVariant ? ` [${usedVariant}]` : '') +
        (result.headline ? ` | ${String(result.headline).slice(0, 70)}` : '')
    );
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

    if (result.status === 'limit_reached' || result.status === 'restricted') {
      console.log(`Stopping for account safety (${result.status}: ${result.error || ''}).`);
      break;
    }
    // Fail fast vs previous run (8) — LinkedIn often blocks quietly via missing Message UI.
    if (consecutiveFails >= 3) {
      console.log('Too many consecutive failures (likely messaging limit/UI block). Stopping.');
      break;
    }

    await dismissOverlays(page);
    if (sent < budget) {
      await betweenDmBrowse(page);
      const waitMs = nextDelayMs(limits.delayMs);
      console.log(
        `Waiting ${Math.round(waitMs / 1000)}s before next (human gap ${limits.delayMs}+jitter)...`
      );
      await sleep(waitMs);
    }
  }

  console.log('\n== Summary ==');
  console.log(`Sent/previewed: ${sent}`);
  console.log(`Skipped (India): ${skipped}`);
  console.log(`Failed: ${failed}`);
  console.log(`Variants used: ${JSON.stringify(variantCounts)}`);
  console.log(`Log: ${LOG_FILE}`);

  await browser.disconnect();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
