const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const LOG_FILE = path.join(__dirname, 'connections-run-log.json');
const CACHE_FILE = path.join(__dirname, 'searched-prospects-cache.json');
const DRY_RUN = process.env.DRY_RUN === '1';
const DELAY_MS = parseInt(process.env.CONNECTION_DELAY_MS || '12000', 10);
const MAX_PER_RUN = parseInt(process.env.MAX_CONNECTIONS_PER_RUN || '10', 10);
const MAX_PER_DAY = parseInt(process.env.MAX_CONNECTIONS_PER_DAY || '15', 10);
const US_GEO_URN = '103644278';

const SEARCH_QUERIES = (process.env.CONNECTION_SEARCH_QUERIES || [
  'SaaS founder CEO',
  'VP Operations SaaS',
  'Head of RevOps B2B',
  'COO software startup',
  'Director of Operations SaaS',
].join('|')).split('|').map((q) => q.trim()).filter(Boolean);

function loadLog() {
  if (!fs.existsSync(LOG_FILE)) return [];
  try {
    return JSON.parse(fs.readFileSync(LOG_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function appendLog(entry) {
  const log = loadLog();
  log.push(entry);
  fs.writeFileSync(LOG_FILE, JSON.stringify(log.slice(-500), null, 2));
}

function loadCache() {
  if (!fs.existsSync(CACHE_FILE)) return { profiles: [] };
  try {
    return JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
  } catch {
    return { profiles: [] };
  }
}

function saveCache(cache) {
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2));
}

function profileSlug(url) {
  const m = (url || '').match(/linkedin\.com\/in\/([^/?#]+)/i);
  return m ? m[1].toLowerCase() : url;
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function getDailyStats(log) {
  const today = todayStr();
  const sentToday = log.filter((e) => e.date === today && e.status === 'sent').length;
  const touched = new Set(
    log.filter((e) => ['sent', 'pending', 'already_connected', 'email_required', 'failed'].includes(e.status))
      .map((e) => profileSlug(e.linkedin_url || e.prospect_id))
  );
  return { sentToday, touched, remaining: Math.max(0, MAX_PER_DAY - sentToday) };
}

function connectBrowser() {
  const tmpDir = os.tmpdir();
  const dirs = fs.readdirSync(tmpDir).filter(
    (name) => name.startsWith('agent-browser-chrome-') || name.startsWith('agent-browser-profile-')
  );
  if (dirs.length === 0) {
    throw new Error('No agent-browser profile found. Launch: agent-browser --session linkedin_bot open https://www.linkedin.com/feed/');
  }
  const latestDir = dirs
    .map((name) => ({ path: path.join(tmpDir, name), mtime: fs.statSync(path.join(tmpDir, name)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime)[0].path;
  const port = fs.readFileSync(path.join(latestDir, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
  return `http://127.0.0.1:${port}`;
}

function buildSearchUrl(keywords) {
  const params = new URLSearchParams();
  params.set('keywords', keywords);
  params.set('origin', 'GLOBAL_SEARCH_HEADER');
  params.set('geoUrn', `["${US_GEO_URN}"]`);
  return `https://www.linkedin.com/search/results/people/?${params.toString()}`;
}

async function clickByText(page, texts, opts = {}) {
  const { tags = ['button', 'a', '[role="button"]'], partial = true, exclude = [] } = opts;
  const handle = await page.evaluateHandle((textList, tagList, usePartial, excludeList) => {
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
    function search(root) {
      if (!root) return null;
      for (const tag of tagList) {
        for (const el of root.querySelectorAll(tag)) {
          if (!matches(el)) continue;
          const rect = el.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) return el;
        }
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = search(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return search(document.body);
  }, texts, tags, partial, exclude);

  const el = handle.asElement();
  if (!el) return false;
  await page.evaluate((e) => {
    e.scrollIntoView({ block: 'center', inline: 'center' });
    e.focus();
  }, el);
  await new Promise((r) => setTimeout(r, 300));
  try {
    await el.click();
  } catch {
    await page.evaluate((e) => e.click(), el);
  }
  await el.dispose();
  return true;
}

async function dismissOverlays(page) {
  await page.evaluate(() => {
    document.querySelectorAll('.msg-overlay-container, [class*="msg-overlay"]').forEach((el) => el.remove());
    // Close jump menus / sticky promo overlays that block Connect clicks
    document.querySelectorAll('button').forEach((b) => {
      const t = ((b.getAttribute('aria-label') || '') + ' ' + (b.innerText || '')).toLowerCase();
      if (t.includes('close jump') || t.includes('dismiss') || t === 'close') {
        try { b.click(); } catch (_) {}
      }
    });
  });
  try {
    await page.keyboard.press('Escape');
  } catch (_) {}
  await new Promise((r) => setTimeout(r, 500));
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
      const title = lines.find(
        (l) => l !== name && l.length < 120 && !/connect|message|mutual|• \d/i.test(l)
      ) || '';

      return { slug, name, title, location: '', linkedin_url: `${href}/` };
    }

    const containerSelectors = [
      'li.reusable-search__result-container',
      'div[data-view-name="search-entity-result-universal-template"]',
      '.entity-result',
    ];
    for (const sel of containerSelectors) {
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

async function searchProspects(page, needed, touchedSlugs) {
  const found = [];
  const cache = loadCache();

  for (const query of SEARCH_QUERIES) {
    if (found.length >= needed) break;

    const url = buildSearchUrl(query);
    console.log(`\nSearching: "${query}" (US)`);
    console.log(url);

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 25000 });
    } catch (err) {
      console.log(`Search navigation error: ${err.message}`);
      continue;
    }
    await dismissOverlays(page);
    await new Promise((r) => setTimeout(r, 3500));

    for (let scroll = 0; scroll < 4 && found.length < needed; scroll++) {
      const batch = await extractSearchResults(page);
      for (const p of batch) {
        if (found.length >= needed) break;
        if (touchedSlugs.has(p.slug)) continue;
        if (found.some((x) => x.slug === p.slug)) continue;
        found.push({ ...p, search_query: query });
      }
      if (found.length >= needed) break;
      await page.evaluate(() => window.scrollBy(0, window.innerHeight * 0.9));
      await new Promise((r) => setTimeout(r, 2000));
    }
  }

  cache.profiles = [...(cache.profiles || []), ...found].slice(-1000);
  cache.last_search = todayStr();
  saveCache(cache);

  console.log(`Found ${found.length} new prospects from search`);
  return found;
}

async function getProfileStatus(page) {
  return page.evaluate(() => {
    function collect(root, out) {
      if (!root) return;
      root.querySelectorAll('button, a, span, [role="button"]').forEach((el) => {
        const t = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim();
        if (t) out.push(t);
      });
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) collect(node.shadowRoot, out);
      }
    }
    const labels = [];
    collect(document.body, labels);
    const joined = labels.join(' | ').toLowerCase();
    if (joined.includes('pending')) return 'pending';
    if (joined.includes('invitation sent')) return 'pending';
    if (joined.includes('message') && !joined.includes('connect')) return 'connected';
    if (joined.includes('connect')) return 'can_connect';
    return 'unknown';
  });
}

async function checkLimits(page) {
  return page.evaluate(() => {
    const body = document.body.innerText.toLowerCase();
    if (body.includes('weekly invitation limit') || body.includes('invitation limit')) {
      return 'limit_reached';
    }
    if (body.includes('email address') && body.includes('connect')) {
      return 'email_required';
    }
    return null;
  });
}

async function confirmInvitation(page) {
  await new Promise((r) => setTimeout(r, 2000));
  if ((await getProfileStatus(page)) === 'pending') return true;

  const clicked = await page.evaluate(() => {
    function tryClick(root) {
      if (!root) return null;
      for (const btn of root.querySelectorAll('button, [role="button"]')) {
        const text = (btn.innerText || btn.textContent || btn.getAttribute('aria-label') || '')
          .replace(/\s+/g, ' ')
          .trim()
          .toLowerCase();
        if (!text) continue;
        if (text.includes('add a note') || text.includes('add note') || text.includes('personalize')) continue;
        if (
          text.includes('send without')
          || text.includes('send invitation')
          || text.includes('send invite')
          || text === 'send'
        ) {
          btn.click();
          return text;
        }
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = tryClick(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return tryClick(document.body);
  });

  if (clicked) {
    console.log(`Clicked invite button: "${clicked}"`);
    await new Promise((r) => setTimeout(r, 2500));
  }

  // Toast / modal success signals (LinkedIn often doesn't flip to Pending immediately)
  const successUi = await page.evaluate(() => {
    const body = (document.body.innerText || '').toLowerCase();
    return (
      body.includes('invitation sent')
      || body.includes('invite sent')
      || body.includes('pending')
      || !!document.querySelector('[data-test-modal], .artdeco-toast-item, .artdeco-inline-feedback--success')
    );
  });

  if ((await getProfileStatus(page)) === 'pending') return true;
  if (successUi) return true;

  // Optimistic: if we clicked Send / Send without a note, treat as sent.
  // LinkedIn UI often stays on Connect until a full reload.
  if (clicked && (clicked.includes('send without') || clicked === 'send' || clicked.includes('send invitation') || clicked.includes('send invite'))) {
    console.log('Invite click confirmed; treating as sent (Pending badge not yet visible).');
    return true;
  }

  // Last resort: reload profile once and re-check
  try {
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 15000 });
    await new Promise((r) => setTimeout(r, 3000));
    if ((await getProfileStatus(page)) === 'pending') return true;
  } catch (_) {}

  return false;
}

async function sendConnectionWithoutNote(page, prospect) {
  const result = {
    prospect_id: prospect.slug,
    name: prospect.name,
    title: prospect.title,
    linkedin_url: prospect.linkedin_url,
    search_query: prospect.search_query,
    date: todayStr(),
    status: 'failed',
    error: null,
  };

  console.log(`\n${'='.repeat(50)}`);
  console.log(`Connecting: ${prospect.name}`);
  if (prospect.title) console.log(`  ${prospect.title}`);
  console.log(`  ${prospect.linkedin_url}`);
  console.log(`${'='.repeat(50)}`);

  if (DRY_RUN) {
    console.log('[DRY RUN] Would send connection (no note)');
    result.status = 'dry_run';
    appendLog(result);
    return result;
  }

  try {
    await page.goto(prospect.linkedin_url, { waitUntil: 'domcontentloaded', timeout: 20000 });
  } catch (err) {
    result.error = `navigation: ${err.message}`;
    appendLog(result);
    return result;
  }
  await dismissOverlays(page);
  await new Promise((r) => setTimeout(r, 3500));

  const status = await getProfileStatus(page);
  console.log(`Profile status: ${status}`);

  if (status === 'connected') {
    result.status = 'already_connected';
    appendLog(result);
    return result;
  }
  if (status === 'pending') {
    result.status = 'pending';
    appendLog(result);
    return result;
  }

  let clicked = await clickByText(page, ['Invite', 'Connect'], {
    exclude: ['disconnect', 'remove', 'mutual', 'people similar', 'more profiles'],
  });
  if (!clicked) {
    await clickByText(page, ['More', 'More actions']);
    await new Promise((r) => setTimeout(r, 1200));
    clicked = await clickByText(page, ['Invite', 'Connect'], { exclude: ['disconnect', 'mutual'] });
  }
  if (!clicked) {
    // Direct aria/href match for "Invite {Name} to connect"
    clicked = await page.evaluate(() => {
      function find(root) {
        if (!root) return null;
        for (const el of root.querySelectorAll('a, button, [role="button"]')) {
          const label = ((el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '')).toLowerCase();
          if (/invite .+ to connect/.test(label) || label.trim() === 'connect') {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0 && rect.top < 700) {
              el.click();
              return label.trim().slice(0, 60);
            }
          }
        }
        const w = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
        let n;
        while (n = w.nextNode()) {
          if (n.shadowRoot) {
            const f = find(n.shadowRoot);
            if (f) return f;
          }
        }
        return null;
      }
      return find(document.body);
    });
    if (clicked) console.log(`Clicked connect control: "${clicked}"`);
  }
  if (!clicked) {
    result.error = 'Connect button not found';
    appendLog(result);
    return result;
  }
  await new Promise((r) => setTimeout(r, 1500));

  let limit = await checkLimits(page);
  if (limit === 'limit_reached') {
    result.status = 'limit_reached';
    result.error = 'LinkedIn weekly invitation limit';
    appendLog(result);
    return result;
  }
  if (limit === 'email_required') {
    result.status = 'email_required';
    result.error = 'LinkedIn requires email to connect';
    appendLog(result);
    return result;
  }

  const confirmed = await confirmInvitation(page);
  if (!confirmed) {
    result.error = 'Could not confirm invitation sent';
    appendLog(result);
    return result;
  }

  result.status = 'sent';
  appendLog(result);
  console.log(`✓ Sent connection request to ${prospect.name}`);
  return result;
}

(async () => {
  const log = loadLog();
  const { sentToday, touched, remaining } = getDailyStats(log);

  if (remaining <= 0) {
    console.log(`Daily limit reached (${sentToday}/${MAX_PER_DAY} sent today).`);
    process.exit(0);
  }

  const batchSize = Math.min(MAX_PER_RUN, remaining);
  console.log(`Target audience: US SaaS founders & ops leaders`);
  console.log(`Limits: ${batchSize} this run, ${remaining} remaining today (${sentToday}/${MAX_PER_DAY} sent)`);
  if (DRY_RUN) console.log('DRY_RUN=1 — no invites will be sent');

  const browserURL = connectBrowser();
  console.log(`Connecting to browser at ${browserURL}...`);
  const browser = await puppeteer.connect({ browserURL });
  const pages = await browser.pages();
  const page = pages.find((p) => p.url().includes('linkedin.com'));
  if (!page) {
    console.error('LinkedIn tab not found. Open LinkedIn in agent-browser first.');
    process.exit(1);
  }
  await page.bringToFront();
  await page.setViewport({ width: 1280, height: 1200 });

  // Search for more than needed — some will be skipped (connected, email required, etc.)
  const searchCount = Math.min(batchSize * 3, 30);
  const prospects = await searchProspects(page, searchCount, touched);

  if (prospects.length === 0) {
    console.log('No new prospects found from search. Try again later or rotate search queries.');
    process.exit(1);
  }

  const summary = { sent: 0, skipped: 0, failed: 0, limit: false };
  let sentThisRun = 0;

  for (const prospect of prospects) {
    if (sentThisRun >= batchSize) break;

    const res = await sendConnectionWithoutNote(page, prospect);

    if (res.status === 'sent' || res.status === 'dry_run') {
      summary.sent++;
      sentThisRun++;
    } else if (['already_connected', 'pending', 'email_required'].includes(res.status)) {
      summary.skipped++;
    } else {
      summary.failed++;
    }

    if (res.status === 'limit_reached') {
      summary.limit = true;
      console.log('\nWeekly limit reached — stopping run.');
      break;
    }

    if (sentThisRun < batchSize && prospects.indexOf(prospect) < prospects.length - 1) {
      console.log(`Waiting ${DELAY_MS}ms before next request...`);
      await new Promise((r) => setTimeout(r, DELAY_MS));
    }
  }

  console.log('\n' + '='.repeat(50));
  console.log('CONNECTION RUN SUMMARY');
  console.log(`  Sent:    ${summary.sent}`);
  console.log(`  Skipped: ${summary.skipped}`);
  console.log(`  Failed:  ${summary.failed}`);
  if (summary.limit) console.log('  Stopped: weekly limit hit');
  console.log('='.repeat(50));

  process.exit(summary.failed > 0 && summary.sent === 0 ? 1 : 0);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
