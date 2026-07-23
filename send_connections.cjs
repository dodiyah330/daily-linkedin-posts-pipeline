const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const LOG_FILE = path.join(__dirname, 'connections-run-log.json');
const CACHE_FILE = path.join(__dirname, 'searched-prospects-cache.json');
const DRY_RUN = process.env.DRY_RUN === '1';
const DELAY_MS = parseInt(process.env.CONNECTION_DELAY_MS || '10000', 10);
const RUN_UNTIL_WEEKLY_LIMIT = process.env.RUN_UNTIL_WEEKLY_LIMIT !== '0';
const MAX_PER_RUN = parseInt(process.env.MAX_CONNECTIONS_PER_RUN || '999', 10);
const MAX_PER_DAY = RUN_UNTIL_WEEKLY_LIMIT
  ? 999
  : parseInt(process.env.MAX_CONNECTIONS_PER_DAY || '15', 10);
const SEARCH_BATCH = parseInt(process.env.CONNECTION_SEARCH_BATCH || '30', 10);
const SEARCH_SCROLLS = parseInt(process.env.CONNECTION_SEARCH_SCROLLS || '8', 10);
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

function getTouchedSlugs(log) {
  return new Set(
    log
      .filter((e) => ['sent', 'pending', 'already_connected', 'email_required'].includes(e.status))
      .map((e) => profileSlug(e.linkedin_url || e.prospect_id))
  );
}

function getDailyStats(log) {
  const today = todayStr();
  const sentToday = log.filter((e) => e.date === today && e.status === 'sent').length;
  const touched = getTouchedSlugs(log);
  const remaining = RUN_UNTIL_WEEKLY_LIMIT
    ? SEARCH_BATCH
    : Math.max(0, MAX_PER_DAY - sentToday);
  return { sentToday, touched, remaining };
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
      if (/·\s*1st\b/.test(card.innerText || '')) return null;
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
    await new Promise((r) => setTimeout(r, 4500));

    for (let scroll = 0; scroll < SEARCH_SCROLLS && found.length < needed; scroll++) {
      let batch = [];
      try {
        batch = await extractSearchResults(page);
      } catch (err) {
        console.log(`Search extract error (scroll ${scroll}): ${err.message}`);
        await new Promise((r) => setTimeout(r, 2500));
        continue;
      }
      for (const p of batch) {
        if (found.length >= needed) break;
        if (touchedSlugs.has(p.slug)) continue;
        if (found.some((x) => x.slug === p.slug)) continue;
        found.push({ ...p, search_query: query });
      }
      if (found.length >= needed) break;
      try {
        await page.evaluate(() => window.scrollBy(0, window.innerHeight * 0.9));
      } catch (_) {}
      await new Promise((r) => setTimeout(r, 2500));
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
    const bodyText = document.body.innerText || '';
    if (/·\s*1st\b/.test(bodyText)) return 'connected';

    function walk(root) {
      if (!root) return null;
      for (const el of root.querySelectorAll('a, button, [role="button"]')) {
        const aria = (el.getAttribute('aria-label') || '').trim();
        const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
        const rect = el.getBoundingClientRect();
        if (rect.width < 1 || rect.height < 1 || rect.top > 200) continue;

        const label = `${text} ${aria}`.toLowerCase();
        if (text === 'Pending' || aria.toLowerCase().includes('pending')) return 'pending';
        if (/^invite .+ to connect$/i.test(aria)) return 'can_connect';
        if (text === 'Connect' && aria.toLowerCase().includes('invite')) return 'can_connect';
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = walk(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return walk(document.body) || 'unknown';
  });
}

async function clickInviteToConnect(page) {
  const clicked = await page.evaluate(() => {
    function walk(root) {
      if (!root) return null;
      for (const el of root.querySelectorAll('a, button, [role="button"]')) {
        const aria = (el.getAttribute('aria-label') || '').trim();
        const rect = el.getBoundingClientRect();
        if (rect.width < 1 || rect.height < 1 || rect.top > 200) continue;
        if (/^invite .+ to connect$/i.test(aria)) {
          el.click();
          return aria;
        }
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = walk(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return walk(document.body);
  });
  if (clicked) console.log(`Clicked: ${clicked}`);
  return !!clicked;
}

async function clickSendWithoutNote(page) {
  const clicked = await page.evaluate(() => {
    function walk(root) {
      if (!root) return false;
      for (const el of root.querySelectorAll('button, [role="button"]')) {
        const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().toLowerCase();
        if (text === 'send without a note') {
          el.click();
          return true;
        }
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot && walk(node.shadowRoot)) return true;
      }
      return false;
    }
    return walk(document.body);
  });
  if (clicked) console.log('Clicked: Send without a note');
  return clicked;
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
  await new Promise((r) => setTimeout(r, 2500));

  let limit = await checkLimits(page);
  if (limit === 'limit_reached') return 'limit_reached';

  if ((await getProfileStatus(page)) === 'pending') return true;

  if (await clickSendWithoutNote(page)) {
    await new Promise((r) => setTimeout(r, 2500));
    limit = await checkLimits(page);
    if (limit === 'limit_reached') return 'limit_reached';
    if ((await getProfileStatus(page)) === 'pending') return true;
    return true;
  }

  // Instant connect (no note modal)
  if ((await getProfileStatus(page)) === 'pending') return true;

  try {
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 20000 });
    await dismissOverlays(page);
    await new Promise((r) => setTimeout(r, 3000));
  } catch (_) {}

  limit = await checkLimits(page);
  if (limit === 'limit_reached') return 'limit_reached';

  return (await getProfileStatus(page)) === 'pending';
}

async function clickConnectOnSearchCard(page, slug) {
  return page.evaluate((targetSlug) => {
    const selectors = 'li.reusable-search__result-container, .entity-result, div[data-view-name="search-entity-result-universal-template"]';
    for (const card of document.querySelectorAll(selectors)) {
      const link = card.querySelector('a[href*="/in/"]');
      if (!link) continue;
      const m = (link.href || '').match(/\/in\/([^/?#]+)/i);
      if (!m || m[1].toLowerCase() !== targetSlug.toLowerCase()) continue;
      card.scrollIntoView({ block: 'center', inline: 'nearest' });
      for (const el of card.querySelectorAll('a, button, [role="button"]')) {
        const aria = (el.getAttribute('aria-label') || '').trim();
        const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
        if (/^invite .+ to connect$/i.test(aria) || text === 'Connect') {
          el.click();
          return true;
        }
      }
    }
    return false;
  }, slug);
}

async function sendFromSearchCard(page, prospect, searchQuery, searchUrl) {
  const result = {
    prospect_id: prospect.slug,
    name: prospect.name,
    title: prospect.title,
    linkedin_url: prospect.linkedin_url,
    search_query: searchQuery,
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

  let clicked = false;
  try {
    clicked = await clickConnectOnSearchCard(page, prospect.slug);
  } catch (err) {
    console.log(`Search card click error: ${err.message}`);
  }
  if (!clicked) {
    console.log('Search card Connect not found — opening profile...');
    try {
      const res = await sendConnectionWithoutNote(page, { ...prospect, search_query: searchQuery });
      try {
        await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 25000 });
        await dismissOverlays(page);
        await new Promise((r) => setTimeout(r, 3500));
      } catch (_) {}
      return res;
    } catch (err) {
      result.error = err.message;
      appendLog(result);
      return result;
    }
  }
  console.log('Clicked Connect on search card');
  await new Promise((r) => setTimeout(r, 2000));

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
  if (confirmed === 'limit_reached') {
    result.status = 'limit_reached';
    result.error = 'LinkedIn weekly invitation limit';
    appendLog(result);
    return result;
  }
  if (!confirmed) {
    result.error = 'Could not confirm invitation sent';
    appendLog(result);
    return result;
  }

  result.status = 'sent';
  appendLog(result);
  console.log(`✓ Sent connection request to ${prospect.name}`);
  try {
    await page.keyboard.press('Escape');
  } catch (_) {}
  await dismissOverlays(page);
  return result;
}

async function processSearchQuery(page, query, touched, summary, sentThisRun, sentToday) {
  console.log(`\nSearching: "${query}" (US)`);
  console.log(buildSearchUrl(query));

  let prospects = [];
  try {
    prospects = await searchProspects(page, SEARCH_BATCH, touched);
  } catch (err) {
    console.log(`Search failed: ${err.message}`);
    return sentThisRun;
  }

  if (!prospects.length) {
    console.log('No new prospects for this query.');
    return sentThisRun;
  }

  for (const prospect of prospects) {
    if (summary.limit) break;
    if (!RUN_UNTIL_WEEKLY_LIMIT && sentThisRun >= MAX_PER_RUN) return sentThisRun;
    if (!RUN_UNTIL_WEEKLY_LIMIT && sentToday + sentThisRun >= MAX_PER_DAY) return sentThisRun;

    try {
      const res = await sendConnectionWithoutNote(page, { ...prospect, search_query: query });

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
        return sentThisRun;
      }

      if (!summary.limit) {
        console.log(`Waiting ${DELAY_MS}ms before next request...`);
        await new Promise((r) => setTimeout(r, DELAY_MS));
      }
    } catch (err) {
      console.log(`Error on ${prospect.name}: ${err.message}`);
      summary.failed++;
    }
  }

  return sentThisRun;
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
    await page.goto(prospect.linkedin_url, { waitUntil: 'domcontentloaded', timeout: 25000 });
  } catch (err) {
    result.error = `navigation: ${err.message}`;
    appendLog(result);
    return result;
  }
  await dismissOverlays(page);
  await new Promise((r) => setTimeout(r, 4000));

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
  if (status !== 'can_connect') {
    result.status = 'already_connected';
    result.error = `No invite button (${status})`;
    appendLog(result);
    return result;
  }

  const clicked = await clickInviteToConnect(page);
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
  if (confirmed === 'limit_reached') {
    result.status = 'limit_reached';
    result.error = 'LinkedIn weekly invitation limit';
    appendLog(result);
    return result;
  }
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
  const { sentToday } = getDailyStats(log);

  console.log(`Target audience: US SaaS founders & ops leaders`);
  if (RUN_UNTIL_WEEKLY_LIMIT) {
    console.log('Mode: send until LinkedIn weekly invitation limit');
  } else {
    console.log(`Mode: capped run (${MAX_PER_RUN}/run, ${MAX_PER_DAY}/day)`);
    if (sentToday >= MAX_PER_DAY) {
      console.log(`Daily limit reached (${sentToday}/${MAX_PER_DAY} sent today).`);
      process.exit(0);
    }
  }
  console.log(`Already sent today: ${sentToday}`);
  if (DRY_RUN) console.log('DRY_RUN=1 — no invites will be sent');

  const browserURL = connectBrowser();
  console.log(`Connecting to browser at ${browserURL}...`);
  const browser = await puppeteer.connect({ browserURL });
  let page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1200 });
  try {
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await new Promise((r) => setTimeout(r, 3000));
  } catch (err) {
    console.error('Could not open LinkedIn feed:', err.message);
    process.exit(1);
  }

  const summary = { sent: 0, skipped: 0, failed: 0, limit: false };
  let sentThisRun = 0;
  let queryRound = 0;
  const maxQueryRounds = 20;

  while (!summary.limit && queryRound < maxQueryRounds) {
    if (!RUN_UNTIL_WEEKLY_LIMIT && sentThisRun >= MAX_PER_RUN) break;
    if (!RUN_UNTIL_WEEKLY_LIMIT && sentToday + sentThisRun >= MAX_PER_DAY) break;

    const touched = getTouchedSlugs(loadLog());
    const beforeSent = sentThisRun;

    for (const query of SEARCH_QUERIES) {
      if (summary.limit) break;
      if (!RUN_UNTIL_WEEKLY_LIMIT && sentThisRun >= MAX_PER_RUN) break;
      sentThisRun = await processSearchQuery(page, query, touched, summary, sentThisRun, sentToday);
    }

    if (sentThisRun === beforeSent && !summary.limit) {
      queryRound++;
      console.log(`No new sends this round (${queryRound}/${maxQueryRounds}). Retrying searches...`);
      await new Promise((r) => setTimeout(r, 5000));
    } else {
      queryRound = 0;
    }
  }

  const sentList = loadLog()
    .filter((e) => e.date === todayStr() && e.status === 'sent')
    .map((e) => `- ${e.name} (${e.linkedin_url})`);

  console.log('\n' + '='.repeat(50));
  console.log('CONNECTION RUN SUMMARY');
  console.log(`  Sent:    ${summary.sent}`);
  console.log(`  Skipped: ${summary.skipped}`);
  console.log(`  Failed:  ${summary.failed}`);
  if (summary.limit) console.log('  Stopped: weekly limit hit');
  if (sentList.length) {
    console.log('\nSent today:');
    sentList.forEach((line) => console.log(line));
  }
  console.log('='.repeat(50));

  process.exit(summary.failed > 0 && summary.sent === 0 ? 1 : 0);
})().catch((err) => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
