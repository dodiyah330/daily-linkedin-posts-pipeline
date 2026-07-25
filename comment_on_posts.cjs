#!/usr/bin/env node
/**
 * Comment on LinkedIn posts that match hiring signals and/or your skill sets.
 * Includes a relevant portfolio link. No Slack approval — posts directly (unless DRY_RUN).
 *
 * Requires: agent-browser --session linkedin_bot open https://www.linkedin.com/feed/
 *
 * Env:
 *   DRY_RUN=1                    Discover/match only, do not comment
 *   MAX_COMMENTS_PER_RUN=15      Cap per script run
 *   MAX_COMMENTS_PER_DAY=15      Cap per calendar day
 *   COMMENT_DELAY_MS=20000       Pause between comments
 *   COMMENT_SCROLLS=6            Scrolls per search results page
 *   COMMENT_SEARCH_BATCH=40      Max posts to collect before filtering
 *   COMMENT_QUERIES=a|b|c        Override search queries (pipe-separated)
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const ROOT = __dirname;
const CONFIG_FILE = path.join(ROOT, 'linkedin_comments_config.json');
const LOG_FILE = path.join(ROOT, 'linkedin-comments-run-log.json');
const CACHE_FILE = path.join(ROOT, 'linkedin-comments-cache.json');

const DRY_RUN = process.env.DRY_RUN === '1';
const DELAY_MS = parseInt(process.env.COMMENT_DELAY_MS || '20000', 10);
const MAX_PER_RUN = parseInt(process.env.MAX_COMMENTS_PER_RUN || '15', 10);
const MAX_PER_DAY = parseInt(process.env.MAX_COMMENTS_PER_DAY || '15', 10);
const SEARCH_SCROLLS = parseInt(process.env.COMMENT_SCROLLS || '6', 10);
const SEARCH_BATCH = parseInt(process.env.COMMENT_SEARCH_BATCH || '40', 10);

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

function loadConfig() {
  const config = loadJson(CONFIG_FILE, null);
  if (!config) throw new Error(`Missing config: ${CONFIG_FILE}`);
  if (process.env.COMMENT_QUERIES) {
    config.search_queries = process.env.COMMENT_QUERIES.split('|')
      .map((q) => q.trim())
      .filter(Boolean);
  }
  return config;
}

function loadPortfolio(config) {
  const rel = config.portfolio_projects_file || 'freelancer-bid-bot/portfolio_projects.json';
  const file = path.isAbsolute(rel) ? rel : path.join(ROOT, rel);
  return loadJson(file, []);
}

function norm(s) {
  return String(s || '')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}

function aliasInText(text, alias) {
  const t = norm(text);
  const a = norm(alias);
  if (!a) return false;
  if (a.length <= 3) {
    return new RegExp(`(?:^|[^a-z0-9])${a.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?:[^a-z0-9]|$)`).test(t);
  }
  return t.includes(a);
}

function matchedSkills(text, config) {
  const skills = config.skills || [];
  const aliases = config.skill_aliases || {};
  const hits = [];
  const seen = new Set();
  for (const skill of skills) {
    const key = norm(skill);
    const list = aliases[key] || [key];
    if (list.some((a) => aliasInText(text, a))) {
      if (!seen.has(key)) {
        seen.add(key);
        hits.push(skill);
      }
    }
  }
  return hits;
}

function coreHits(matched, config) {
  const core = new Set((config.core_skills || []).map(norm));
  if (!core.size) return matched;
  return matched.filter((s) => core.has(norm(s)));
}

function hasHiringSignal(text, config) {
  const t = norm(text);
  return (config.hiring_keywords || []).some((k) => t.includes(norm(k)));
}

function hasRemoteSignal(text, config) {
  const t = norm(text);
  return (config.remote_keywords || ['remote', 'work from home', 'wfh']).some((k) =>
    t.includes(norm(k))
  );
}

function hasOnsiteOnlySignal(text, config) {
  const t = norm(text);
  return (config.onsite_exclude_keywords || []).some((k) => t.includes(norm(k)));
}

function shouldExclude(text, config) {
  const t = norm(text);
  return (config.exclude_keywords || []).some((k) => t.includes(norm(k)));
}

function inferCategories(matched, config) {
  const map = config.category_map || {};
  const cats = [];
  const seen = new Set();
  for (const skill of matched) {
    const cat = map[norm(skill)];
    if (cat && !seen.has(cat)) {
      seen.add(cat);
      cats.push(cat);
    }
  }
  if (!cats.includes('automation')) cats.push('automation');
  return cats;
}

function selectPortfolio(matched, config, projects) {
  const limit = Math.max(1, parseInt(config.portfolio_links_per_comment || 1, 10));
  const cats = inferCategories(matched, config);
  const picked = [];
  const seen = new Set();

  function consider(item) {
    const url = String(item.url || '').trim();
    const title = String(item.title || '').trim();
    if (!url || seen.has(url)) return;
    seen.add(url);
    picked.push({ title: title || url, url, category: item.category });
  }

  for (const cat of cats) {
    for (const item of projects) {
      if (item.category === cat) consider(item);
      if (picked.length >= limit) return picked;
    }
  }
  for (const item of projects) {
    consider(item);
    if (picked.length >= limit) break;
  }
  if (!picked.length && config.portfolio_hub) {
    picked.push({ title: 'Portfolio', url: config.portfolio_hub });
  }
  return picked.slice(0, limit);
}

function sanitizeComment(text) {
  return String(text || '')
    .replace(/\u2014/g, ':')
    .replace(/\u2013/g, ' to ')
    .replace(/--+/g, ':')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();
}

function buildComment(post, config, portfolio) {
  const matched = post.matched_skills || [];
  const hiring = post.is_hiring;
  const skillsLabel = (matched.slice(0, 3).join(', ') || 'web / automation').trim();
  const item = portfolio[0] || { title: 'Portfolio', url: config.portfolio_hub || '' };
  const variants = config.comment_variants || {};
  let key = 'skills';
  if (hiring && matched.length) key = 'both';
  else if (hiring) key = 'hiring';
  const forced = process.env.COMMENT_VARIANT || config.default_variant || 'auto';
  if (forced !== 'auto' && variants[forced]) key = forced;
  const tpl =
    variants[key] ||
    variants.both ||
    'Interested. I work on {{skills}}. Example: {{project}} ({{url}}).';
  return sanitizeComment(
    tpl
      .replace(/\{\{\s*skills\s*\}\}/gi, skillsLabel)
      .replace(/\{\{\s*project\s*\}\}/gi, item.title || 'recent work')
      .replace(/\{\{\s*url\s*\}\}/gi, item.url || config.portfolio_hub || '')
  );
}

function postKey(post) {
  return (
    post.urn ||
    post.activity_id ||
    post.url ||
    `${norm(post.author)}::${norm(post.text).slice(0, 80)}`
  );
}

function getDailyStats(log) {
  const today = todayStr();
  const sentToday = log.filter((e) => e.date === today && e.status === 'sent').length;
  const touched = new Set(
    log
      .filter((e) => ['sent', 'dry_run', 'already_commented'].includes(e.status))
      .map((e) => e.post_key)
      .filter(Boolean)
  );
  return {
    sentToday,
    touched,
    remaining: Math.max(0, Math.min(MAX_PER_DAY - sentToday, MAX_PER_RUN)),
  };
}

function connectBrowser() {
  const tmpRoots = [os.tmpdir(), process.env.TMPDIR, '/var/folders'].filter(Boolean);
  const dirs = [];
  for (const root of tmpRoots) {
    try {
      if (!fs.existsSync(root)) continue;
      for (const name of fs.readdirSync(root)) {
        if (name.startsWith('agent-browser-chrome-') || name.startsWith('agent-browser-profile-')) {
          dirs.push(path.join(root, name));
        }
      }
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

function buildContentSearchUrl(keywords, datePosted) {
  const params = new URLSearchParams();
  params.set('keywords', keywords);
  params.set('origin', 'GLOBAL_SEARCH_HEADER');
  if (datePosted) params.set('datePosted', `"${datePosted}"`);
  return `https://www.linkedin.com/search/results/content/?${params.toString()}`;
}

async function dismissOverlays(page) {
  try {
    await page.evaluate(() => {
      document.querySelectorAll('button').forEach((b) => {
        const t = ((b.getAttribute('aria-label') || '') + ' ' + (b.innerText || '')).toLowerCase();
        if (t.includes('dismiss') || t === 'close' || t.includes('got it') || t.includes('not now')) {
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
  await new Promise((r) => setTimeout(r, 350));
}

async function clickByText(page, texts, opts = {}) {
  const { tags = ['button', 'a', '[role="button"]'], partial = true, exclude = [] } = opts;
  const handle = await page.evaluateHandle(
    (textList, tagList, usePartial, excludeList) => {
      function n(s) {
        return (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
      }
      function excluded(label) {
        return excludeList.some((x) => label.includes(n(x)));
      }
      function matches(el) {
        const label = n(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
        if (!label || excluded(label)) return false;
        return textList.some((t) => {
          const target = n(t);
          return usePartial ? label.includes(target) : label === target;
        });
      }
      for (const tag of tagList) {
        for (const el of document.querySelectorAll(tag)) {
          if (!matches(el)) continue;
          const rect = el.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) return el;
        }
      }
      return null;
    },
    texts,
    tags,
    partial,
    exclude
  );
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

async function extractContentResults(page) {
  return page.evaluate(() => {
    const results = [];
    const seen = new Set();

    function cleanText(t) {
      return (t || '').replace(/\s+/g, ' ').trim();
    }

    function feedPostCount(text) {
      return (String(text || '').match(/Feed post/g) || []).length;
    }

    function smallestCardFor(commentBtn) {
      let el = commentBtn.parentElement;
      let best = null;
      while (el && el !== document.body) {
        const text = el.innerText || '';
        const count = feedPostCount(text);
        if (count === 1 && text.length > 80) best = el;
        if (count > 1 && best) break;
        el = el.parentElement;
      }
      return best;
    }

    function parseCard(card, commentBtn, index) {
      const raw = card.innerText || '';
      const lines = raw
        .split('\n')
        .map((l) => l.trim())
        .filter(Boolean);

      const profileLink = [...card.querySelectorAll('a[href*="/in/"]')].find((a) => {
        const href = a.href || '';
        return /linkedin\.com\/in\/[^/?#]+/i.test(href) && !/miniProfile/i.test(href);
      });
      const profileUrl = profileLink ? (profileLink.href || '').split('?')[0] : '';
      const slugMatch = profileUrl.match(/linkedin\.com\/in\/([^/?#]+)/i);
      const slug = slugMatch ? slugMatch[1].toLowerCase() : '';

      let author = '';
      const aria = commentBtn.getAttribute('aria-label') || '';
      // "Open control menu for post by NAME" is more reliable; Comment aria is often just "Comment"
      const menuBtn = [...card.querySelectorAll('button')].find((b) =>
        /open control menu for post by/i.test(b.getAttribute('aria-label') || '')
      );
      const menuAria = menuBtn ? menuBtn.getAttribute('aria-label') || '' : '';
      const byMatch = menuAria.match(/post by\s+(.+)$/i);
      if (byMatch) author = cleanText(byMatch[1]);
      if (!author) {
        author = cleanText(
          (profileLink && (profileLink.innerText || profileLink.textContent)) || lines[1] || slug || 'Unknown'
        )
          .split('\n')[0]
          .slice(0, 80);
      }

      // Body text: drop chrome lines
      const text = lines
        .filter((l) => {
          if (/^Feed post$/i.test(l)) return false;
          if (/^(Follow|View job|Repost|Comment|\d+|•|\d+[hmwd]|… more|\.\.\.more)$/i.test(l)) return false;
          if (l === author) return false;
          if (/^\d+(st|nd|rd)$/i.test(l)) return false;
          return l.length > 2;
        })
        .join(' ')
        .slice(0, 1400);

      if (!text || text.length < 40) return null;

      const jobLink = [...card.querySelectorAll('a[href*="/jobs/view/"]')][0];
      const url = jobLink
        ? (jobLink.href || '').split('?')[0]
        : profileUrl || '';

      const key = `${slug || author}::${text.slice(0, 90).toLowerCase()}`;
      if (seen.has(key)) return null;
      seen.add(key);

      const rect = commentBtn.getBoundingClientRect();
      return {
        urn: key,
        activity_id: '',
        author,
        profile_url: profileUrl,
        text,
        url,
        comment_index: index,
        comment_y: rect.y,
        query_context: true,
      };
    }

    const commentButtons = [...document.querySelectorAll('button')].filter((b) => {
      const label = ((b.getAttribute('aria-label') || '') + ' ' + (b.innerText || '')).trim().toLowerCase();
      if (!(label === 'comment' || /^comment\s*\d*$/i.test(label.trim()))) return false;
      const r = b.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    });

    commentButtons.forEach((btn, index) => {
      const card = smallestCardFor(btn);
      if (!card) return;
      const parsed = parseCard(card, btn, index);
      if (parsed) results.push(parsed);
    });

    // Fallback: split page text on "Feed post" if button climb failed
    if (!results.length) {
      const body = document.body.innerText || '';
      const chunks = body.split(/\nFeed post\n|\nFeed post$/).slice(1);
      chunks.forEach((chunk, i) => {
        const lines = chunk
          .split('\n')
          .map((l) => l.trim())
          .filter(Boolean);
        if (lines.length < 3) return;
        const author = lines[0].slice(0, 80);
        const text = lines.slice(2).join(' ').slice(0, 1400);
        if (text.length < 40) return;
        const key = `${author}::${text.slice(0, 90).toLowerCase()}`;
        if (seen.has(key)) return;
        seen.add(key);
        results.push({
          urn: key,
          activity_id: '',
          author,
          profile_url: '',
          text,
          url: '',
          comment_index: i,
          comment_y: 0,
          query_context: true,
        });
      });
    }

    return results;
  });
}

function scorePost(post, config) {
  const text = post.text || '';
  if (shouldExclude(text, config)) return null;
  if (hasOnsiteOnlySignal(text, config)) return null;

  const matched = matchedSkills(text, config);
  const core = coreHits(matched, config);
  const hiring = hasHiringSignal(text, config);
  const remote = hasRemoteSignal(text, config);
  const requireRemoteHiring = config.require_remote_hiring !== false;
  const minSkills = Math.max(1, parseInt(config.min_skill_hits || 1, 10));

  // Default: only remote hiring posts that also match skills
  if (requireRemoteHiring) {
    if (!hiring || !remote) return null;
    if (matched.length < minSkills) return null;
    if (core.length < 1 && (config.core_skills || []).length) return null;
  } else {
    if (!hiring && matched.length < minSkills) return null;
    if (!hiring && core.length < 1 && (config.core_skills || []).length) return null;
  }

  let score = matched.length * 2 + core.length * 3;
  if (hiring) score += 5;
  if (remote) score += 5;
  if (hiring && remote && matched.length) score += 6;
  return {
    ...post,
    matched_skills: matched,
    core_skills: core,
    is_hiring: hiring,
    is_remote: remote,
    score,
  };
}

async function collectPosts(page, config, needed, already) {
  const found = [];
  const queries = config.search_queries || [];
  const datePosted = config.date_posted || 'past-week';

  for (const query of queries) {
    if (found.length >= needed) break;
    const url = buildContentSearchUrl(query, datePosted);
    console.log(`\nSearching content: ${query}`);
    console.log(url);
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 35000 });
    } catch (err) {
      console.log(`Nav error: ${err.message}`);
      await new Promise((r) => setTimeout(r, 2000));
    }
    await new Promise((r) => setTimeout(r, 3500));
    await dismissOverlays(page);

    for (let scroll = 0; scroll < SEARCH_SCROLLS && found.length < needed; scroll++) {
      let batch = [];
      try {
        batch = await extractContentResults(page);
      } catch (err) {
        console.log(`Extract error: ${err.message}`);
        await new Promise((r) => setTimeout(r, 1500));
        try {
          batch = await extractContentResults(page);
        } catch (_) {
          break;
        }
      }
      if (scroll === 0) {
        console.log(`  extracted ${batch.length} posts on page`);
      }
      for (const raw of batch) {
        if (found.length >= needed) break;
        const scored = scorePost(raw, config);
        if (!scored) continue;
        const key = postKey(scored);
        if (already.has(key)) continue;
        if (found.some((x) => postKey(x) === key)) continue;
        found.push({ ...scored, query, search_url: url });
      }
      try {
        await page.evaluate(() => window.scrollBy(0, window.innerHeight * 0.9));
      } catch (_) {}
      await new Promise((r) => setTimeout(r, 1600));
    }
  }

  found.sort((a, b) => b.score - a.score);
  console.log(`Collected ${found.length} matching posts`);
  return found;
}

async function getCommentEditor(page) {
  const handle = await page.evaluateHandle(() => {
    function visible(el) {
      if (!el) return false;
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    }
    function find(root) {
      if (!root) return null;
      const selectors = [
        '.comments-comment-box__form div[contenteditable="true"]',
        '.comments-comment-texteditor div[contenteditable="true"]',
        'form.comments-comment-box__form div.ql-editor',
        'div.ql-editor[contenteditable="true"]',
        'div[role="textbox"][contenteditable="true"]',
        'div[data-placeholder*="Add a comment"]',
        'div[aria-label*="Add a comment"]',
        'div[aria-label*="Text editor"]',
        'div[contenteditable="true"]',
      ];
      for (const sel of selectors) {
        for (const el of root.querySelectorAll(sel)) {
          if (!visible(el)) continue;
          const ph = (
            (el.getAttribute('data-placeholder') || '') +
            ' ' +
            (el.getAttribute('aria-label') || '') +
            ' ' +
            (el.getAttribute('aria-placeholder') || '')
          ).toLowerCase();
          if (
            sel === 'div[contenteditable="true"]' &&
            ph &&
            !(ph.includes('comment') || ph.includes('text editor') || ph.includes('write'))
          ) {
            continue;
          }
          return el;
        }
      }
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

async function fillComment(page, text) {
  let editor = await getCommentEditor(page);
  if (!editor) {
    await clickByText(page, ['Comment', 'Add a comment'], {
      tags: ['button', 'a', '[role="button"]', 'div'],
      exclude: ['commented', 'comments on', 'view comments'],
    });
    await new Promise((r) => setTimeout(r, 900));
    editor = await getCommentEditor(page);
  }
  if (!editor) return false;

  await editor.click({ clickCount: 1 }).catch(() => {});
  await new Promise((r) => setTimeout(r, 250));
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
    await page.keyboard.type(text, { delay: 8 });
  }

  const len = await editor.evaluate((el) => (el.innerText || '').trim().length);
  await editor.dispose();
  return len >= Math.min(20, Math.floor(text.length * 0.5));
}

async function submitComment(page) {
  const clicked = await page.evaluate(() => {
    const selectors = [
      'button.comments-comment-box__submit-button:not([disabled])',
      'button.comments-comment-box__submit-button--cr:not([disabled])',
      'form.comments-comment-box__form button[type="submit"]:not([disabled])',
    ];
    for (const sel of selectors) {
      const btn = document.querySelector(sel);
      if (btn) {
        btn.click();
        return true;
      }
    }
    const buttons = [...document.querySelectorAll('button')];
    const postBtn = buttons.find((b) => {
      const t = ((b.innerText || '') + ' ' + (b.getAttribute('aria-label') || '')).trim().toLowerCase();
      const r = b.getBoundingClientRect();
      return t === 'post' || t === 'comment' || t.includes('post comment');
    });
    if (postBtn && !postBtn.disabled) {
      const r = postBtn.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {
        postBtn.click();
        return true;
      }
    }
    return false;
  });
  if (clicked) return true;
  return clickByText(page, ['Post', 'Comment'], {
    tags: ['button'],
    exclude: ['repost', 'previous', 'next', 'add a photo'],
  });
}

async function openPost(page, post) {
  // Prefer reopening the search that found this post, then comment in-place.
  if (post.search_url) {
    try {
      await page.goto(post.search_url, { waitUntil: 'domcontentloaded', timeout: 35000 });
    } catch (err) {
      if (!/ERR_ABORTED/i.test(err.message)) {
        console.log(`  search reopen error: ${err.message}`);
      }
    }
    await new Promise((r) => setTimeout(r, 2800));
    await dismissOverlays(page);

    // Scroll until we see the author / matching card
    for (let i = 0; i < 8; i++) {
      const found = await page.evaluate((author, snippet) => {
        const body = document.body.innerText || '';
        return body.includes(author) || (snippet && body.includes(snippet.slice(0, 40)));
      }, post.author || '', post.text || '');
      if (found) break;
      await page.evaluate(() => window.scrollBy(0, window.innerHeight * 0.8));
      await new Promise((r) => setTimeout(r, 900));
    }
    return true;
  }

  const url =
    post.url ||
    (post.activity_id
      ? `https://www.linkedin.com/feed/update/urn:li:activity:${post.activity_id}/`
      : post.profile_url || '');
  if (!url) return false;
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 35000 });
  } catch (err) {
    if (!/ERR_ABORTED/i.test(err.message)) {
      console.log(`  open error: ${err.message}`);
    }
  }
  await new Promise((r) => setTimeout(r, 2800));
  await dismissOverlays(page);
  return true;
}

async function clickCommentOnMatchedPost(page, post) {
  const handle = await page.evaluateHandle((author, snippet, commentIndex) => {
    function feedPostCount(text) {
      return (String(text || '').match(/Feed post/g) || []).length;
    }
    function smallestCardFor(commentBtn) {
      let el = commentBtn.parentElement;
      let best = null;
      while (el && el !== document.body) {
        const text = el.innerText || '';
        const count = feedPostCount(text);
        if (count === 1 && text.length > 80) best = el;
        if (count > 1 && best) break;
        el = el.parentElement;
      }
      return best;
    }

    const buttons = [...document.querySelectorAll('button')].filter((b) => {
      const label = ((b.getAttribute('aria-label') || '') + ' ' + (b.innerText || '')).trim().toLowerCase();
      if (!(label === 'comment' || /^comment\s*\d*$/i.test(label.trim()))) return false;
      const r = b.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    });

    const needle = (snippet || '').slice(0, 48).toLowerCase();
    for (const btn of buttons) {
      const card = smallestCardFor(btn);
      if (!card) continue;
      const text = (card.innerText || '').toLowerCase();
      const authorHit = author && text.includes(String(author).toLowerCase());
      const snippetHit = needle && text.includes(needle);
      if (authorHit || snippetHit) return btn;
    }

    if (Number.isInteger(commentIndex) && buttons[commentIndex]) return buttons[commentIndex];
    return null;
  }, post.author || '', post.text || '', post.comment_index);

  const el = handle.asElement();
  if (!el) return false;
  await page.evaluate((e) => e.scrollIntoView({ block: 'center', inline: 'center' }), el);
  await new Promise((r) => setTimeout(r, 400));
  const box = await el.boundingBox();
  if (box) {
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  } else {
    await page.evaluate((e) => e.click(), el);
  }
  await el.dispose();
  return true;
}

async function commentOnPost(page, post, comment) {
  const opened = await openPost(page, post);
  if (!opened) return { status: 'failed', error: 'could not open search/post' };

  await clickByText(page, ['…more', '… more', 'see more'], {
    tags: ['button', 'span'],
    exclude: ['see more replies'],
  }).catch(() => false);
  await new Promise((r) => setTimeout(r, 350));

  const clicked = await clickCommentOnMatchedPost(page, post);
  if (!clicked) {
    // fallback generic comment click
    const fallback = await clickByText(page, ['Comment'], {
      tags: ['button'],
      exclude: ['commented', 'comments on'],
    });
    if (!fallback) return { status: 'failed', error: 'comment button not found' };
  }
  await new Promise((r) => setTimeout(r, 900));

  const filled = await fillComment(page, comment);
  if (!filled) return { status: 'failed', error: 'could not fill comment box' };

  if (DRY_RUN) {
    return { status: 'dry_run', preview: comment.slice(0, 160) };
  }

  const sent = await submitComment(page);
  if (!sent) return { status: 'failed', error: 'post button not found' };
  await new Promise((r) => setTimeout(r, 1500));
  return { status: 'sent' };
}

async function main() {
  const config = loadConfig();
  const portfolioProjects = loadPortfolio(config);
  const log = loadJson(LOG_FILE, []);
  const cache = loadJson(CACHE_FILE, { posts: [] });
  const { sentToday, touched, remaining } = getDailyStats(log);

  console.log('== LinkedIn skill/hiring comments ==');
  console.log(
    `dry_run=${DRY_RUN} sent_today=${sentToday} remaining=${remaining} delay=${DELAY_MS}ms portfolio_items=${portfolioProjects.length}`
  );

  if (remaining <= 0) {
    console.log('Daily comment cap reached. Done.');
    return;
  }

  const browserURL = connectBrowser();
  const browser = await puppeteer.connect({ browserURL, defaultViewport: null });
  const pages = await browser.pages();
  const page = pages[0] || (await browser.newPage());
  page.setDefaultTimeout(30000);

  const targets = await collectPosts(page, config, Math.min(SEARCH_BATCH, remaining * 3), touched);
  const toProcess = targets.slice(0, remaining);

  let sent = 0;
  let failed = 0;
  let skipped = 0;

  for (let i = 0; i < toProcess.length; i++) {
    const post = toProcess[i];
    const key = postKey(post);
    const portfolio = selectPortfolio(post.matched_skills || [], config, portfolioProjects);
    const comment = buildComment(post, config, portfolio);

    console.log(`\n[${i + 1}/${toProcess.length}] ${post.author || 'Unknown'} score=${post.score}`);
    console.log(`  remote=${post.is_remote} hiring=${post.is_hiring} skills=${(post.matched_skills || []).join(', ') || '-'}`);
    console.log(`  ${comment.slice(0, 140)}${comment.length > 140 ? '…' : ''}`);

    let result;
    try {
      result = await commentOnPost(page, post, comment);
    } catch (err) {
      result = { status: 'failed', error: err.message };
    }

    const entry = {
      date: todayStr(),
      ts: new Date().toISOString(),
      status: result.status,
      post_key: key,
      activity_id: post.activity_id || '',
      author: post.author || '',
      url: post.url || '',
      query: post.query || '',
      is_hiring: !!post.is_hiring,
      is_remote: !!post.is_remote,
      matched_skills: post.matched_skills || [],
      portfolio: portfolio.map((p) => p.url),
      comment,
      error: result.error || '',
      preview: result.preview || '',
    };
    appendLog(entry);

    cache.posts = [...(cache.posts || []), { key, author: post.author, url: post.url, ts: entry.ts }]
      .reduce((acc, p) => {
        if (!acc.some((x) => x.key === p.key)) acc.push(p);
        return acc;
      }, [])
      .slice(-2000);
    cache.last_run = todayStr();
    saveJson(CACHE_FILE, cache);

    if (result.status === 'sent' || result.status === 'dry_run') {
      sent += 1;
      console.log(`  -> ${result.status}`);
    } else {
      failed += 1;
      console.log(`  -> ${result.status}${result.error ? `: ${result.error}` : ''}`);
    }

    if (i < toProcess.length - 1) {
      await new Promise((r) => setTimeout(r, DELAY_MS));
    }
  }

  if (!toProcess.length) skipped = targets.length;

  console.log(`\nDone. commented/dry=${sent} failed=${failed} collected=${targets.length} skipped_queue=${skipped}`);
  try {
    await browser.disconnect();
  } catch (_) {}
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
