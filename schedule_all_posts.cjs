const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

async function getElementShadow(page, selector) {
  const handle = await page.evaluateHandle((sel) => {
    function findEl(root, allowHidden) {
      if (!root) return null;
      const els = root.querySelectorAll(sel);
      let fallback = null;
      for (const el of els) {
        if (!fallback) fallback = el;
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        if (rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none') {
          return el;
        }
      }
      if (allowHidden && fallback) return fallback;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = findEl(node.shadowRoot, allowHidden);
          if (found) return found;
        }
      }
      return null;
    }
    return findEl(document.body, true);
  }, selector);
  return handle.asElement();
}

async function waitForSelectorShadow(page, selector, timeout = 15000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const el = await getElementShadow(page, selector);
    if (el) {
      await el.dispose();
      return true;
    }
    await new Promise(r => setTimeout(r, 500));
  }
  throw new Error(`Timeout waiting for shadow selector: ${selector}`);
}

// finderArg is serialized and passed as the finder's second parameter, since
// finderFn is stringified and cannot close over local variables.
async function clickNativelyShadow(page, finderFn, finderArg = null) {
  try {
    await page.evaluate(() => {
      document.querySelectorAll('.msg-overlay-container, [class*="msg-overlay"], #msg-overlay').forEach(el => el.remove());
    });

    const handle = await page.evaluateHandle((finder, arg) => {
      const fn = new Function('return ' + finder)();
      function findInShadow(root) {
        if (!root) return null;
        const res = fn(root, arg);
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
    }, finderFn.toString(), finderArg);

    const el = handle.asElement();
    if (el) {
      const tagAndClass = await page.evaluate(e => {
        return `${e.tagName} class="${e.className}" text="${e.innerText ? e.innerText.trim().substring(0,30) : ''}"`;
      }, el);
      console.log(`clickNativelyShadow: Found element: <${tagAndClass}>`);
      try {
        await page.evaluate(e => {
          e.focus();
          e.scrollIntoView({ block: 'center', inline: 'center' });
        }, el);
        await new Promise(r => setTimeout(r, 200));
        await el.click();
      } catch (clickErr) {
        console.log("Puppeteer native click failed, falling back to programmatic event sequence:", clickErr.message);
        await page.evaluate(e => {
          const rect = e.getBoundingClientRect();
          const x = rect.left + rect.width / 2;
          const y = rect.top + rect.height / 2;
          const opts = { bubbles: true, cancelable: true, view: window, screenX: x, screenY: y, clientX: x, clientY: y };
          e.dispatchEvent(new PointerEvent('pointerdown', opts));
          e.dispatchEvent(new MouseEvent('mousedown', opts));
          e.focus();
          e.dispatchEvent(new PointerEvent('pointerup', opts));
          e.dispatchEvent(new MouseEvent('mouseup', opts));
          e.dispatchEvent(new MouseEvent('click', opts));
        }, el);
      }
      await el.dispose();
      return true;
    }
    return false;
  } catch (err) {
    console.error("clickNativelyShadow error:", err);
    return false;
  }
}

async function clickNativelyShadowRetry(page, finderFn, timeout = 15000, finderArg = null) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const clicked = await clickNativelyShadow(page, finderFn, finderArg);
    if (clicked) return true;
    await new Promise(r => setTimeout(r, 1000));
  }
  return false;
}

async function fillFieldShadow(page, selector, value) {
  const el = await getElementShadow(page, selector);
  if (!el) throw new Error(`Could not find element to fill: ${selector}`);
  
  await page.evaluate((input) => {
    input.focus();
    input.select();
  }, el);
  
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.press('Backspace');
  
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.type(value);
  await page.keyboard.press('Enter');
  await new Promise(r => setTimeout(r, 200));
  await page.keyboard.press('Escape');
  await new Promise(r => setTimeout(r, 200));
  await page.keyboard.press('Tab');
  await el.dispose();
  await new Promise(r => setTimeout(r, 1000));
}

async function fillCaptionShadow(page, caption) {
  const editorEl = await getElementShadow(page, '.ql-editor');
  if (!editorEl) {
    console.log("fillCaption: editor element not found");
    return false;
  }
  await editorEl.click();
  await new Promise(r => setTimeout(r, 400));

  // Strategy 1: CDP insertText (works with Quill/contenteditable)
  try {
    const client = await page.createCDPSession();
    await client.send('Input.insertText', { text: caption });
    await client.detach();
  } catch (e) {
    console.log("fillCaption: CDP insertText failed:", e.message);
  }

  let len = await editorEl.evaluate((el) => (el.innerText || '').trim().length);

  // Strategy 2: direct DOM on the located editor node
  if (len <= 5) {
    len = await editorEl.evaluate((el, text) => {
      el.focus();
      el.innerHTML = '';
      text.split('\n').forEach((line) => {
        const p = document.createElement('p');
        p.textContent = line || ' ';
        el.appendChild(p);
      });
      el.dispatchEvent(new InputEvent('input', { bubbles: true, data: text }));
      return (el.innerText || '').trim().length;
    }, caption);
  }

  // Strategy 3: slow keyboard typing after re-focus
  if (len <= 5) {
    await editorEl.click();
    await page.keyboard.type(caption.replace(/\n/g, '\n'), { delay: 8 });
    len = await editorEl.evaluate((el) => (el.innerText || '').trim().length);
  }

  console.log(`fillCaption: inserted length=${len}`);
  await editorEl.dispose();
  return len > 5;
}

async function getEditorTextShadow(page) {
  const editorEl = await getElementShadow(page, '.ql-editor');
  if (!editorEl) return null;
  const text = await editorEl.evaluate((el) => (el.innerText || '').trim());
  await editorEl.dispose();
  return text;
}

async function fillTimeComboboxShadow(page, selector, value) {
  const el = await getElementShadow(page, selector);
  if (!el) throw new Error(`Could not find combobox element to fill: ${selector}`);
  
  await page.evaluate((input) => {
    input.focus();
    input.select();
  }, el);
  
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.press('Backspace');
  
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.type(value);
  console.log(`Typed ${value} into time combobox, waiting for suggestions...`);
  await new Promise(r => setTimeout(r, 1500));
  
  await page.keyboard.press('ArrowDown');
  await new Promise(r => setTimeout(r, 500));
  await page.keyboard.press('Enter');
  await el.dispose();
  await new Promise(r => setTimeout(r, 1000));
}

// ==========================================
// ALL 11 POSTS — 4 per day across 3 days
// Schedule: 9:00 AM, 12:00 PM, 3:00 PM, 6:00 PM IST
// ==========================================

(async () => {
  const scheduleFile = process.env.SCHEDULE_FILE
    ? path.resolve(__dirname, process.env.SCHEDULE_FILE)
    : path.join(__dirname, 'schedule_today.json');
  const pauseMarker = path.join(__dirname, '.general_batch_paused');
  if (
    fs.existsSync(pauseMarker) &&
    path.basename(scheduleFile) === 'schedule_today.json' &&
    process.env.FORCE_GENERAL_BATCH !== '1'
  ) {
    console.error('General 16-post batch is paused (.general_batch_paused exists).');
    console.error('Use SCHEDULE_FILE=schedule_automation_leads.json for automation posts,');
    console.error('or FORCE_GENERAL_BATCH=1 to override.');
    process.exit(1);
  }
  let posts;
  if (fs.existsSync(scheduleFile)) {
    posts = JSON.parse(fs.readFileSync(scheduleFile, 'utf8')).posts;
    console.log(`Loaded ${posts.length} posts from ${path.basename(scheduleFile)}`);
  } else {
  posts = [
    // ===== DAY 1 — June 13, 2026 =====
    {
      id: 1,
      type: 'carousel',
      date: '06/13/2026',
      time: '9:00 AM',
      caption: `Spending weeks building an idea without validation leads to wasted time. Successful founders check demand, supply, and saturation before writing code. Autocomplete searches and shopping trends offer free, reliable indicators of buying intent.

How do you validate a new product idea before building?

Follow me.`,
      assetPath: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/linkedin-carousel-2026-06-12.pdf',
      title: 'The validation mistake that kills startups'
    },
    {
      id: 2,
      type: 'infographic',
      date: '06/13/2026',
      time: '12:00 PM',
      caption: `Mistral is rumored to be raising a new funding round at a twenty billion dollar valuation. This is nearly double its series C valuation from last year. The rapid rise of European AI model developers highlights how fast capital is shifting to compete with US firms. Shifting from seed stage to a multi billion dollar player in under three years is a massive growth timeline.

What is the biggest hurdle for new AI firms raising capital at high valuations?

Follow me.`,
      assetPath: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/linkedin-infographic.png'
    },
    {
      id: 3,
      type: 'regular',
      date: '06/13/2026',
      time: '3:00 PM',
      caption: `A silent crisis is happening across the startup community that nobody discusses on social media feeds. The founders who are actually struggling the most stay completely silent.

They carry the weight of failing metrics, cash runway issues, and operational bottlenecks alone. They cannot share their fears online because their team, their investors, and their competitors are all watching. They perform success publicly while handling the real pressure privately.

Building a closed circle of three peer founders who share no overlap in markets provides a safe release. Having weekly checkout calls to share raw numbers and worries removes the isolation of the founder role.

Moving from isolation to shared reality lowers the mental load and prevents burnout. Founders get practical advice from peers who face the same pressure, leading to better decisions.

How do solo founders build a safe support network that does not compromise their business reputation?

Follow me.`
    },
    {
      id: 4,
      type: 'poll',
      date: '06/13/2026',
      time: '6:00 PM',
      caption: `Most businesses copy what everyone else is doing, and very few are willing to step into uncharted territory. Innovation suffers when founders focus entirely on immediate cash pressure. They ignore building a unique connection.

When teams operate from a stress mindset, they replicate existing models. They spend their energy trying to win a price war. They do not make their clients feel amazing.

Shifting from a transaction focus to an emotional design focus reveals gaps that competitors ignore.

Creating an experience that customers love builds natural loyalty. The business stands out in a crowded market, making competition irrelevant.

Share a story of how your team breaks out of copycat cycles in the comments.`,
      title: 'What is the biggest barrier to innovation in early stage startups?',
      pollOptionsStr: 'Pure money panic mindset|Slow execution by teams|Fear of competitor copycats|Lack of customer feedback'
    },

    // ===== DAY 2 — June 14, 2026 =====
    {
      id: 5,
      type: 'regular',
      date: '06/14/2026',
      time: '9:00 AM',
      caption: `A new video generation tool is targeting regional markets by lowering production costs to a fraction of a cent. Distilled video models are making high quality content accessible for local businesses.

Small business owners struggle to afford expensive commercial video generation. Standard tools cost too much for businesses operating at regional scale.

Using specialized, distilled models reduces the cost of video creation to half a cent per second. Businesses can generate localized marketing assets without high software costs.

Local brands can launch video campaigns on social platforms, reaching new customers without a large marketing budget.

Will ultra cheap video tools help small local shops compete with national brands?

Follow me.`
    },
    {
      id: 6,
      type: 'regular',
      date: '06/14/2026',
      time: '12:00 PM',
      caption: `Major funding rounds are reshaping the technology sector this week. Physical AI, space systems, and model developers are securing billions from public and private investors.

Following every individual funding announcement takes hours of reading. The rapid pace of deals makes it hard to see where the capital is actually flowing.

Focus on the largest movements. Mistral is raising three billion euros. Jeff Bezos is backing physical AI with a twelve billion dollar round. SpaceX officially priced its shares for its public market entry.

Understanding where the billions are going helps founders spot emerging hardware and infrastructure opportunities early.

Which of these massive funding rounds will have the biggest long term impact?

Save this post to track today's funding trends.`
    },
    {
      id: 7,
      type: 'regular',
      date: '06/14/2026',
      time: '3:00 PM',
      caption: `A physical AI company just raised twelve billion dollars to automate heavy engineering tasks. The goal is to build a system that acts as a general engineer for the physical world and medicine design.

Software AI cannot interact with real factories or labs. Replicating human physical coordination requires massive compute and hardware integration.

The company is training systems on physical world physics and chemical properties. This allows the AI to predict how molecules and materials behave in real situations.

Heavy industries and drug developers can automate designs in weeks instead of years, lowering the cost of physical innovation.

The main limitation is that real world testing still requires physical validation, meaning software speed will always hit a hardware bottleneck.

How soon will physical AI systems run manufacturing plants without human supervision?

Follow me.`
    },
    {
      id: 8,
      type: 'regular',
      date: '06/14/2026',
      time: '6:00 PM',
      caption: `Generating video content at half a cent per second is a massive advantage for bootstrapped startups. Distilled video models are removing the financial barrier to visual marketing.

Most visual tools charge high monthly subscription fees before a startup has any paying users. This burns through early capital.

Startups can use pay-as-you-go distilled models to generate ads without locking into expensive monthly contracts.

Solo founders can run video ad campaigns, test different messages, and find product market fit without software debt.

What is your preferred budget-friendly tool for creating startup marketing videos?

Follow me.`
    },

    // ===== DAY 3 — June 15, 2026 =====
    {
      id: 9,
      type: 'regular',
      date: '06/15/2026',
      time: '9:00 AM',
      caption: `The rise of factory robots that do not specialize in single tasks is shifting manufacturing roles. Reconfigurable machines are changing how physical production is managed.

Traditional assembly lines require expensive reprogramming for every new product. This keeps manufacturing out of reach for small hardware startups.

Workers are moving from manual assembly to robot fleet management. Learning how to configure and monitor general purpose robots creates a high paying career path.

Hardware startups can launch products from local micro-factories, lowering shipping costs and scaling production dynamically.

Will general purpose robots bring manufacturing back to local communities?

Save this post to reference hardware trends.`
    },
    {
      id: 10,
      type: 'regular',
      date: '06/15/2026',
      time: '12:00 PM',
      caption: `The upcoming public market listings for massive space and AI firms is a stress test for private valuations. The era of high private markups without public scrutiny is ending.

Private investors have marked up company valuations for years. When these firms list publicly, the market often corrects these numbers down.

Watch how public markets value AI companies and how those listings affect early stage startup valuations and VC funding access.

More realistic valuations bring stability to the startup market, making it easier for founders to raise rounds based on actual revenue.

Will public market listings lower the inflated valuations of private AI firms?

Follow me.`
    },
    {
      id: 11,
      type: 'regular',
      date: '06/15/2026',
      time: '3:00 PM',
      caption: `Use this three-step prompt workflow to validate your startup ideas using search autocomplete data. Stop building products before you know if anyone is searching for them.

Founders spend months building software that nobody wants. They rely on vibes instead of search data.

Run this analysis before writing code:

"Act as a market researcher. Analyze this startup idea: [Insert Idea].
1. Identify 5 autocomplete search terms related to this idea.
2. List 3 niche variations that target a specific audience.
3. Outline the search interest trend for these variations."

You find a specific, uncrowded niche with active search volume, turning a guess into a product strategy.

What niche variation will you test using this validation prompt today?

Save this prompt to use on your next idea.`
    }
  ];
  }

  const screenshotDir = path.join(__dirname, 'slack_downloads');

  try {
    console.log("Locating active devtools port dynamically...");
    const tmpDir = os.tmpdir();
    const dirs = fs.readdirSync(tmpDir).filter(name =>
      name.startsWith('agent-browser-chrome-') || name.startsWith('agent-browser-profile-')
    );
    if (dirs.length === 0) {
      throw new Error('No agent-browser profile directories found in tmp. Launch agent-browser first.');
    }
    const latestDir = dirs.map(name => {
      const fullPath = path.join(tmpDir, name);
      return { path: fullPath, mtime: fs.statSync(fullPath).mtimeMs };
    }).sort((a, b) => b.mtime - a.mtime)[0].path;
    const portFile = path.join(latestDir, 'DevToolsActivePort');
    const content = fs.readFileSync(portFile, 'utf8');
    const port = content.split('\n')[0].trim();
    console.log(`Connecting to browser on port ${port}...`);
    const browser = await puppeteer.connect({
      browserURL: `http://127.0.0.1:${port}`,
      protocolTimeout: 180000,
    });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com'));
    if (!page) {
      console.error("LinkedIn page not found! Make sure LinkedIn is open in the agent-browser.");
      process.exit(1);
    }
    await page.bringToFront();
    // Real Chrome window can stay tiny (~700px) even after setViewport — resize via CDP.
    try {
      const cdp = await page.createCDPSession();
      const { windowId } = await cdp.send('Browser.getWindowForTarget');
      await cdp.send('Browser.setWindowBounds', {
        windowId,
        bounds: { width: 1440, height: 1000, windowState: 'normal' },
      });
      await cdp.detach().catch(() => {});
    } catch (resizeErr) {
      console.log('Window resize skipped:', resizeErr.message);
    }
    await page.setViewport({ width: 1280, height: 1200 });
    console.log('Viewport:', await page.evaluate(() => ({ w: innerWidth, h: innerHeight })));

    const startFrom = parseInt(process.env.START_POST_ID || '1', 10);
    const queue = posts.filter(p => p.id >= startFrom);
    if (startFrom > 1) {
      console.log(`Resuming from post ${startFrom} (${queue.length} remaining)`);
    }

    console.log(`\n${'='.repeat(60)}`);
    console.log(`SCHEDULING ${queue.length} POSTS (4 per day, 3 days)`);
    console.log(`${'='.repeat(60)}\n`);

    const failedPosts = [];
    const okPosts = [];

    for (const post of queue) {
      console.log(`\n${'='.repeat(50)}`);
      console.log(`Scheduling Post ${post.id}/${posts.length} (${post.type}): Date=${post.date}, Time=${post.time}`);
      console.log(`${'='.repeat(50)}`);
      const prefix = `${screenshotDir}/post_${post.id}_${post.type}`;

      try {
      // Navigate to feed (or company admin page for company streams)
      const scheduleMeta = (() => {
        try {
          return JSON.parse(fs.readFileSync(scheduleFile, 'utf8'));
        } catch (_) {
          return {};
        }
      })();
      const companyStart =
        process.env.LINKEDIN_START_URL ||
        scheduleMeta.startUrl ||
        (scheduleMeta.stream && String(scheduleMeta.stream).includes('openxcode')
          ? 'https://www.linkedin.com/company/open-xcode/admin/'
          : null) ||
        (scheduleMeta.companyPage
          ? String(scheduleMeta.companyPage).replace(/\/?$/, '/') + 'admin/'
          : null);
      const startUrl = companyStart || 'https://www.linkedin.com/feed/';
      console.log(`Navigating to ${startUrl}...`);
      try {
        await page.goto(startUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
      } catch (err) {
        console.log("Navigation timeout/error, continuing:", err.message);
      }
      await new Promise(r => setTimeout(r, 5000));

      // Hide messaging overlays
      console.log("Hiding messaging overlays...");
      await page.evaluate(() => {
        const style = document.createElement('style');
        style.id = 'hide-msg-overlay-style-' + Date.now();
        style.innerHTML = `
          .msg-overlay-container, 
          [class*="msg-overlay"], 
          #msg-overlay { 
            display: none !important; 
          }
        `;
        document.head.appendChild(style);
      });

      // Close any open composers
      console.log("Checking and closing any open composers first...");
      await page.evaluate(() => {
        function findDismissBtn(root) {
          if (!root) return null;
          const btn = Array.from(root.querySelectorAll('button')).find(
            b => {
              const label = b.getAttribute('aria-label') || '';
              const txt = b.innerText || '';
              const cls = b.className || '';
              return label.includes('Dismiss') || 
                     txt.includes('Dismiss') ||
                     label.toLowerCase() === 'close' ||
                     cls.includes('close-button');
            }
          );
          if (btn) return btn;
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
          let node;
          while (node = walker.nextNode()) {
            if (node.shadowRoot) {
              const found = findDismissBtn(node.shadowRoot);
              if (found) return found;
            }
          }
          return null;
        }
        const dismissBtn = findDismissBtn(document.body);
        if (dismissBtn) dismissBtn.click();
      });
      await new Promise(r => setTimeout(r, 2000));

      console.log("Clicking 'Start a post'...");
      const editorSelector = '.ql-editor';
      // Company admin only: open Create menu first if present
      const onCompanyAdmin = /linkedin\.com\/company\/.+\/admin/i.test(page.url());
      if (onCompanyAdmin) {
        await clickNativelyShadow(page, (root) => {
          return Array.from(root.querySelectorAll('a, button, [role="button"]')).find(el => {
            const t = (el.innerText || '').trim().toLowerCase();
            const label = (el.getAttribute('aria-label') || '').toLowerCase();
            return t === 'create' || label === 'create';
          });
        });
        await new Promise(r => setTimeout(r, 1500));
      }

      let editorReady = false;
      for (let startAttempt = 1; startAttempt <= 4 && !editorReady; startAttempt++) {
        // Dismiss leftovers that block the composer
        await page.keyboard.press('Escape').catch(() => {});
        await new Promise(r => setTimeout(r, 600));
        await page.evaluate(() => {
          document.querySelectorAll('.msg-overlay-container, [class*="msg-overlay"], #msg-overlay').forEach(el => el.remove());
        });

        let clickStartPost = await clickNativelyShadow(page, (root) => {
          return Array.from(root.querySelectorAll('*')).find(
            el => {
              if (!(el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || el.tagName === 'A' || el.getAttribute('aria-label') === 'Start a post')) return false;
              const t = (el.innerText || '').trim().toLowerCase();
              if (!t.includes('start a post')) return false;
              // Avoid giant parent containers that also contain the phrase
              const r = el.getBoundingClientRect();
              return r.width > 40 && r.width < 900 && r.height > 20 && r.height < 120;
            }
          );
        });
        // Company admin fallbacks. The Create menu sometimes renders its items late,
        // so reopen it and retry before giving up.
        for (let attempt = 1; attempt <= 3 && !clickStartPost && onCompanyAdmin; attempt++) {
          clickStartPost = await clickNativelyShadow(page, (root) => {
            return Array.from(root.querySelectorAll('button, a, [role="button"]')).find(el => {
              const t = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).toLowerCase();
              return t.includes('start a post') || t.includes('create a post') || t.includes('share content');
            });
          });
          if (clickStartPost) break;
          console.log(`'Start a post' not visible yet, reopening Create menu (attempt ${attempt}/3)...`);
          await clickNativelyShadow(page, (root) => {
            return Array.from(root.querySelectorAll('a, button, [role="button"]')).find(el => {
              const t = (el.innerText || '').trim().toLowerCase();
              const label = (el.getAttribute('aria-label') || '').toLowerCase();
              return t === 'create' || label === 'create';
            });
          });
          await new Promise(r => setTimeout(r, 2500));
        }
        if (!clickStartPost) {
          console.log(`Start a post click missed (attempt ${startAttempt}/4), reloading feed...`);
          await page.goto(startUrl, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
          await new Promise(r => setTimeout(r, 3500));
          continue;
        }

        try {
          await waitForSelectorShadow(page, editorSelector, 12000);
          editorReady = true;
        } catch (_) {
          console.log(`Composer editor not ready (attempt ${startAttempt}/4), retrying Start a post...`);
          await page.keyboard.press('Escape').catch(() => {});
          await new Promise(r => setTimeout(r, 1000));
          if (startAttempt === 4) {
            throw new Error("Timeout waiting for shadow selector: .ql-editor");
          }
        }
      }
      if (!editorReady) throw new Error("Could not open post composer");
      await new Promise(r => setTimeout(r, 1000));

      // Switch author to the company page when requested (any company stream).
      // Skip if composer already shows that company as author (company admin Create flow).
      const postAs = (process.env.POST_AS || scheduleMeta.postAs || '').trim();
      // Match the page name loosely: "OpenXCode" also matches "open xcode" / "open-xcode".
      const companyNamePattern = postAs
        ? postAs.toLowerCase().replace(/[^a-z0-9]+/g, '').split('').join('[^a-z0-9]*')
        : null;
      const alreadyCompany = companyNamePattern
        ? await page.evaluate((pattern, name) => {
            const re = new RegExp(pattern, 'i');
            const t = document.body.innerText || '';
            const nearAudience = new RegExp(pattern + '[\\s\\S]{0,40}Post to Anyone', 'i');
            if (nearAudience.test(t)) return true;
            return Array.from(document.querySelectorAll('button[aria-label]')).some(
              b => re.test((b.getAttribute('aria-label') || '').replace(/[^a-zA-Z0-9]+/g, ''))
            ) || Array.from(document.querySelectorAll('button[aria-label]')).some(
              b => (b.getAttribute('aria-label') || '').toLowerCase().includes(name.toLowerCase())
            );
          }, companyNamePattern, postAs)
        : false;
      const wantsCompany = !!postAs ||
        (scheduleMeta.stream && /company/i.test(String(scheduleMeta.stream)));
      if (!alreadyCompany && wantsCompany && companyNamePattern) {
        console.log(`Switching post author to ${postAs}...`);
        const openedActor = await clickNativelyShadow(page, (root) => {
          const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]') || root;
          return Array.from(modal.querySelectorAll('button, [role="button"]')).find(el => {
            const label = (el.getAttribute('aria-label') || '').toLowerCase();
            const txt = (el.innerText || '').toLowerCase();
            // Avoid the "Post to Anyone" audience settings button
            if (txt.includes('post to anyone') || label.includes('post to anyone')) return false;
            return label.includes('post as') || label.includes('actor') ||
              (txt.includes('post as') && !txt.includes('anyone'));
          });
        });
        if (openedActor) {
          await new Promise(r => setTimeout(r, 1500));
          await clickNativelyShadow(page, (root, pattern) => {
            const re = new RegExp(pattern, 'i');
            return Array.from(root.querySelectorAll('button, [role="menuitem"], li, div, span')).find(el => {
              const t = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).toLowerCase();
              return re.test(t) && !t.includes('post to anyone');
            });
          }, companyNamePattern);
          await new Promise(r => setTimeout(r, 1500));
        } else {
          console.log(`Author switcher not found — assuming company admin composer already posts as ${postAs}.`);
        }
      } else if (alreadyCompany) {
        console.log(`Composer already posting as ${postAs} — skipping author switch.`);
      }

      // ========== HANDLE ATTACHMENTS ==========
      if (post.type === 'poll') {
        console.log("Handling Poll attachment...");

        // Strategy 1: direct poll icon in composer toolbar
        let openedPoll = await clickNativelyShadow(page, (root) => {
          const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
          const container = modal || root;
          return Array.from(container.querySelectorAll('button, [role="menuitem"], li, span, div')).find(el => {
            const label = (el.getAttribute('aria-label') || '').toLowerCase();
            const txt = (el.innerText || '').trim().toLowerCase();
            return label.includes('poll') || txt === 'poll' || txt.includes('create a poll');
          });
        });

        // Strategy 2: More → Create a poll
        if (!openedPoll) {
          await clickNativelyShadow(page, (root) => {
            const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
            const container = modal || root;
            return Array.from(container.querySelectorAll('button')).find(el => {
              const label = (el.getAttribute('aria-label') || '').toLowerCase();
              const txt = (el.innerText || '').trim().toLowerCase();
              return label === 'more' || txt === 'more' ||
                (el.className.includes('share-promoted-detour-button') && txt.includes('more'));
            });
          });
          await new Promise(r => setTimeout(r, 2000));
          openedPoll = await clickNativelyShadow(page, (root) => {
            const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
            const container = modal || root;
            return Array.from(container.querySelectorAll('button, [role="menuitem"], li, span, div')).find(el => {
              const label = (el.getAttribute('aria-label') || '').toLowerCase();
              const txt = (el.innerText || '').trim().toLowerCase();
              return label.includes('create a poll') || txt.includes('create a poll') || txt === 'poll';
            });
          });
        }

        // Strategy 3: legacy detour buttons (poll is often the 2nd icon)
        if (!openedPoll) {
          const detourIdx = await page.evaluate(() => {
            function findDetours(root, out) {
              if (!root) return out;
              root.querySelectorAll('button.share-promoted-detour-button').forEach(b => out.push(b));
              const w = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
              let n;
              while (n = w.nextNode()) {
                if (n.shadowRoot) findDetours(n.shadowRoot, out);
              }
              return out;
            }
            const btns = findDetours(document.body, []);
            const modal = document.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
            const inModal = modal ? btns.filter(b => modal.contains(b)) : btns;
            return inModal.length >= 2 ? 1 : -1;
          });
          if (detourIdx >= 0) {
            openedPoll = await clickNativelyShadow(page, (root) => {
              const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
              const btns = Array.from((modal || root).querySelectorAll('button.share-promoted-detour-button'));
              return btns[detourIdx] || null;
            });
          }
        }

        if (!openedPoll) throw new Error("Could not find 'Create a poll' button");
        await new Promise(r => setTimeout(r, 2000));

        // Fill question
        await waitForSelectorShadow(page, 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"]');
        const questionEl = await getElementShadow(page, 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"]');
        await questionEl.focus();
        await page.keyboard.type(post.title);
        await questionEl.dispose();
        console.log("Filled poll question.");

        const options = post.pollOptionsStr.split('|').map(o => o.trim().slice(0, 30));
        
        const getInputs = async () => {
          const inputsHandle = await page.evaluateHandle(() => {
            function findInputs(root) {
              let found = [];
              const els = root.querySelectorAll('input[id*="poll-option"]');
              for (const el of els) found.push(el);
              const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
              let node;
              while (node = walker.nextNode()) {
                if (node.shadowRoot) found = found.concat(findInputs(node.shadowRoot));
              }
              return found;
            }
            return findInputs(document.body);
          });
          const properties = await inputsHandle.getProperties();
          const currentInputs = [];
          for (const property of properties.values()) {
            const el = property.asElement();
            if (el) currentInputs.push(el);
          }
          return currentInputs;
        };

        let optionInputs = await getInputs();
        if (optionInputs.length < 2) throw new Error("Option inputs not found");
        
        await optionInputs[0].focus();
        await page.keyboard.type(options[0]);
        await new Promise(r => setTimeout(r, 300));
        
        await optionInputs[1].focus();
        await page.keyboard.type(options[1]);
        await new Promise(r => setTimeout(r, 300));

        if (options[2]) {
          console.log("Adding third option...");
          await clickNativelyShadow(page, (root) => {
            return Array.from(root.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Add option'));
          });
          await new Promise(r => setTimeout(r, 1000));
          
          optionInputs = await getInputs();
          if (optionInputs.length < 3) throw new Error("Option 3 input not found");
          await optionInputs[2].focus();
          await page.keyboard.type(options[2]);
          await new Promise(r => setTimeout(r, 300));
        }

        if (options[3]) {
          console.log("Adding fourth option...");
          await clickNativelyShadow(page, (root) => {
            return Array.from(root.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Add option'));
          });
          await new Promise(r => setTimeout(r, 1000));
          
          optionInputs = await getInputs();
          if (optionInputs.length < 4) throw new Error("Option 4 input not found");
          await optionInputs[3].focus();
          await page.keyboard.type(options[3]);
          await new Promise(r => setTimeout(r, 300));
        }

        // Verify poll options
        console.log("Performing validation check on typed poll options...");
        const verifyVals = await page.evaluate(() => {
          function findInputs(root) {
            let found = [];
            const els = root.querySelectorAll('input[id*="poll-option"]');
            for (const el of els) found.push(el.value.trim());
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {
              if (node.shadowRoot) found = found.concat(findInputs(node.shadowRoot));
            }
            return found;
          }
          return findInputs(document.body);
        });
        console.log("Values found in inputs:", verifyVals);
        if (verifyVals.some(v => v === "")) {
          throw new Error("Validation Failed: Some poll option inputs are blank in React state/DOM!");
        }

        await page.screenshot({ path: `${prefix}_filled.png` });

        // Click Done
        console.log("Clicking Done on Poll creator...");
        const clickedPollDone = await clickNativelyShadowRetry(page, (root) => {
          return Array.from(root.querySelectorAll('button')).find(b => {
            const txt = b.innerText ? b.innerText.trim() : '';
            const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0 || window.getComputedStyle(b).display !== 'none';
            const isNotVideoJS = typeof b.className === 'string' && !b.className.includes('vjs-');
            const isDisabled = b.hasAttribute('disabled') || b.disabled || (typeof b.className === 'string' && b.className.includes('disabled'));
            return txt === 'Done' && isVisible && isNotVideoJS && !isDisabled;
          });
        });
        if (!clickedPollDone) throw new Error("Could not click Done on Poll creator");
        await new Promise(r => setTimeout(r, 2000));

      } else if (post.type === 'carousel') {
        // Upload the PDF BEFORE typing captions that contain URLs.
        // Link previews replace the media toolbar and hide "Add a document".
        console.log("Handling Carousel document upload (before caption)...");
        await new Promise(r => setTimeout(r, 1500));

        const findDocButton = (root) => {
          // Prefer exact aria-label on a real control — never match page-wide DIVs
          // (e.g. .application-outlet) whose innerText can contain "document"/"pdf".
          const controls = Array.from(root.querySelectorAll(
            'button, [role="menuitem"], [role="button"], label, input[type="file"]'
          ));
          const byAria = controls.find(b => {
            const label = (b.getAttribute('aria-label') || '').trim().toLowerCase();
            const r = b.getBoundingClientRect();
            return r.width > 8 && r.height > 8 && (
              label === 'add a document' ||
              label.includes('add a document') ||
              label === 'document'
            );
          });
          if (byAria) return byAria;
          return controls.find(b => {
            const hay = ((b.getAttribute('aria-label') || '') + ' ' + (b.innerText || '')).toLowerCase().replace(/\s+/g, ' ').trim();
            const r = b.getBoundingClientRect();
            // Keep text match short so we don't match the whole page chrome
            if (hay.length > 80) return false;
            return r.width > 8 && r.height > 8 && (
              hay.includes('add a document') ||
              hay === 'document' ||
              (hay.includes('document') && hay.includes('pdf'))
            );
          });
        };

        const findShareMore = (root) => {
          // Prefer the share-box detour More (not nav "More")
          const detour = Array.from(root.querySelectorAll('button.share-promoted-detour-button')).find(
            b => (b.getAttribute('aria-label') || '').trim() === 'More'
          );
          if (detour) return detour;
          const media = Array.from(root.querySelectorAll('button')).find(b =>
            /add media/i.test((b.getAttribute('aria-label') || '') + ' ' + (b.innerText || ''))
          );
          if (media) {
            let node = media.parentElement;
            for (let i = 0; i < 6 && node; i++) {
              const more = Array.from(node.querySelectorAll('button')).find(b => {
                const label = (b.getAttribute('aria-label') || '').trim();
                const cls = typeof b.className === 'string' ? b.className : '';
                return (label === 'More' || (b.innerText || '').trim() === 'More') &&
                  (cls.includes('detour') || cls.includes('share'));
              });
              if (more) return more;
              node = node.parentElement;
            }
          }
          return null;
        };

        let clickedDoc = await clickNativelyShadow(page, findDocButton);
        if (!clickedDoc) {
          console.log("Document button not in toolbar — opening share More menu...");
          // Ensure toolbar is visible
          await page.evaluate(() => {
            const more = document.querySelector('button.share-promoted-detour-button[aria-label="More"]');
            const footer = document.querySelector('.share-creation-state__footer, .share-box__footer, [role="dialog"]');
            (more || footer)?.scrollIntoView({ block: 'center', inline: 'nearest' });
          });
          await new Promise(r => setTimeout(r, 500));
          const openedMore = await clickNativelyShadow(page, findShareMore);
          console.log(openedMore ? "Share More menu opened." : "Share More button not found.");
          await new Promise(r => setTimeout(r, 2000));
          clickedDoc = await clickNativelyShadowRetry(page, findDocButton, 15000);
        }
        // One more pass: reopen More if still missing
        if (!clickedDoc) {
          console.log("Retrying share More → Add a document...");
          await clickNativelyShadow(page, findShareMore);
          await new Promise(r => setTimeout(r, 2500));
          clickedDoc = await clickNativelyShadow(page, findDocButton);
        }
        if (!clickedDoc) throw new Error("Could not find 'Add a document' button");
        await new Promise(r => setTimeout(r, 2000));

        const fileInputHandle = await page.evaluateHandle(() => {
          function findFileInput(root) {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {
              if (node.tagName === 'INPUT' && node.type === 'file') return node;
              if (node.shadowRoot) {
                const found = findFileInput(node.shadowRoot);
                if (found) return found;
              }
            }
            return null;
          }
          return findFileInput(document.body);
        });
        let fileInput = fileInputHandle.asElement();
        if (!fileInput) {
          // Wait briefly for LinkedIn to inject the file picker after Add a document
          for (let i = 0; i < 10 && !fileInput; i++) {
            await new Promise(r => setTimeout(r, 400));
            const retry = await page.evaluateHandle(() => {
              function findFileInput(root) {
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
                let node;
                while (node = walker.nextNode()) {
                  if (node.tagName === 'INPUT' && node.type === 'file') return node;
                  if (node.shadowRoot) {
                    const found = findFileInput(node.shadowRoot);
                    if (found) return found;
                  }
                }
                return null;
              }
              return findFileInput(document.body);
            });
            fileInput = retry.asElement();
            if (!fileInput) await retry.dispose();
          }
        }
        if (!fileInput) throw new Error("Could not find file input after Add a document");
        await fileInput.uploadFile(post.assetPath);
        console.log("Document uploaded. Waiting 4s for processing...");
        await new Promise(r => setTimeout(r, 4000));

        // Title — LinkedIn rejects Done when title exceeds 58 characters
        const docTitle = String(post.title || 'Document').slice(0, 58).replace(/[\s\-:;,]+$/, '');
        await waitForSelectorShadow(page, 'input.document-title-form__title-input, input[placeholder*="title to your document"]');
        const titleInput = await getElementShadow(page, 'input.document-title-form__title-input, input[placeholder*="title to your document"]');
        await titleInput.focus();
        await page.evaluate((el) => {
          el.focus();
          el.select();
          el.value = '';
          el.dispatchEvent(new Event('input', { bubbles: true }));
        }, titleInput);
        await page.keyboard.type(docTitle);
        await titleInput.dispose();
        console.log("Document title typed:", docTitle);

        // Verify title
        const titleVal = await page.evaluate(() => {
          function findTitleInput(root) {
            const el = root.querySelector('input.document-title-form__title-input, input[placeholder*="title to your document"]');
            if (el) return el.value.trim();
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {
              if (node.shadowRoot) {
                const val = findTitleInput(node.shadowRoot);
                if (val) return val;
              }
            }
            return null;
          }
          return findTitleInput(document.body);
        });
        console.log("Title value in DOM:", titleVal);
        if (!titleVal || titleVal === "") {
          throw new Error("Validation Failed: Document title input is blank!");
        }

        await page.screenshot({ path: `${prefix}_doc_uploaded.png` });

        // Click Done
        const clickedDocDone = await clickNativelyShadowRetry(page, (root) => {
          return Array.from(root.querySelectorAll('button')).find(b => {
            const txt = b.innerText ? b.innerText.trim() : '';
            const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0 || window.getComputedStyle(b).display !== 'none';
            const isNotVideoJS = typeof b.className === 'string' && !b.className.includes('vjs-');
            const isDisabled = b.hasAttribute('disabled') || b.disabled || (typeof b.className === 'string' && b.className.includes('disabled'));
            return txt === 'Done' && isVisible && isNotVideoJS && !isDisabled;
          });
        });
        if (!clickedDocDone) throw new Error("Could not click Done on Document uploader");
        await new Promise(r => setTimeout(r, 4000));

      } else if (post.type === 'infographic') {
        console.log("Handling Infographic image upload...");
        // Scope to the composer modal: the page behind it has its own Photo button
        // that does nothing when the modal is already open.
        const mediaFinder = (root) => {
          const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
          const scope = modal || root;
          const btns = Array.from(scope.querySelectorAll('button'));
          const label = (b) => (b.getAttribute('aria-label') || '') + ' ' + (b.innerText || '');
          return btns.find(b => /add media/i.test(label(b)) && (b.className || '').includes('detour')) ||
                 btns.find(b => /add media/i.test(label(b))) ||
                 btns.find(b => /add a photo|^photo$/i.test(label(b).trim()));
        };
        let fileInput = null;
        for (let attempt = 1; attempt <= 3 && !fileInput; attempt++) {
          const clickedMedia = await clickNativelyShadow(page, mediaFinder);
          if (!clickedMedia && attempt === 3) throw new Error("Could not find image upload button");
          await new Promise(r => setTimeout(r, 2500));
          const fileInputHandle = await page.evaluateHandle(() => {
            function findFileInput(root) {
              const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
              let node;
              while (node = walker.nextNode()) {
                if (node.tagName === 'INPUT' && node.type === 'file') return node;
                if (node.shadowRoot) {
                  const found = findFileInput(node.shadowRoot);
                  if (found) return found;
                }
              }
              return null;
            }
            return findFileInput(document.body);
          });
          fileInput = fileInputHandle ? fileInputHandle.asElement() : null;
          if (!fileInput) console.log(`File input not ready, retrying media button (attempt ${attempt}/3)...`);
        }
        if (!fileInput) throw new Error("Could not find file input in shadow DOM");
        await fileInput.uploadFile(post.assetPath);
        console.log("Image uploaded. Waiting 4s for processing...");
        await new Promise(r => setTimeout(r, 4000));

        await page.screenshot({ path: `${prefix}_image_uploaded.png` });

        // Click Next/Done in image editor
        const clickedImageNext = await clickNativelyShadowRetry(page, (root) => {
          return Array.from(root.querySelectorAll('button')).find(b => {
            const txt = b.innerText ? b.innerText.trim() : '';
            const isMatch = txt === 'Next' || txt === 'Done';
            const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0 || window.getComputedStyle(b).display !== 'none';
            const isNotVideoJS = typeof b.className === 'string' && !b.className.includes('vjs-');
            const isDisabled = b.hasAttribute('disabled') || b.disabled || (typeof b.className === 'string' && b.className.includes('disabled'));
            return isMatch && isVisible && isNotVideoJS && !isDisabled;
          });
        });
        if (!clickedImageNext) throw new Error("Could not click Next/Done in image editor");
        await new Promise(r => setTimeout(r, 3000));
      }

      // ========== FILL CAPTION ==========
      if (post.type !== 'poll' && post.type !== 'carousel') {
      console.log("Filling post caption text...");
      await waitForSelectorShadow(page, editorSelector, 15000);
      await new Promise(r => setTimeout(r, 1500));
      let filled = false;
      for (let attempt = 1; attempt <= 5 && !filled; attempt++) {
        filled = await fillCaptionShadow(page, post.caption);
        if (!filled) {
          console.log(`Caption fill attempt ${attempt}/5 failed, retrying...`);
          await new Promise(r => setTimeout(r, 2000));
        }
      }
      if (!filled) {
        const editorEl = await getElementShadow(page, editorSelector);
        await editorEl.focus();
        await page.evaluate((el) => {
          el.focus();
          document.execCommand('selectAll', false, null);
          document.execCommand('delete', false, null);
        }, editorEl);
        await new Promise(r => setTimeout(r, 500));
        const paragraphs = post.caption.split('\n');
        for (let i = 0; i < paragraphs.length; i++) {
          if (i > 0) {
            await page.keyboard.press('Enter');
            await new Promise(r => setTimeout(r, 150));
          }
          if (paragraphs[i]) {
            await page.keyboard.type(paragraphs[i]);
            await new Promise(r => setTimeout(r, 150));
          }
        }
        await editorEl.dispose();
      }
      await new Promise(r => setTimeout(r, 2000));

      // Verify caption
      const editorText = await getEditorTextShadow(page);
      console.log("Caption text in editor (length):", editorText ? editorText.length : 0);
      if (!editorText || editorText.length < 5) {
        throw new Error("Validation Failed: Post caption in editor is blank or too short!");
      }

      await page.screenshot({ path: `${prefix}_draft_composer.png` });
      } else if (post.type === 'carousel') {
        let editorText = await getEditorTextShadow(page);
        console.log("Carousel caption length after upload:", editorText ? editorText.length : 0);
        if (!editorText || editorText.length < 5) {
          console.log("Carousel caption lost after document upload — re-filling...");
          await waitForSelectorShadow(page, editorSelector, 15000);
          await new Promise(r => setTimeout(r, 1000));
          let refilled = false;
          for (let attempt = 1; attempt <= 5 && !refilled; attempt++) {
            refilled = await fillCaptionShadow(page, post.caption);
            if (!refilled) {
              console.log(`Carousel caption refill attempt ${attempt}/5 failed, retrying...`);
              await new Promise(r => setTimeout(r, 1500));
            }
          }
          editorText = await getEditorTextShadow(page);
          console.log("Carousel caption length after refill:", editorText ? editorText.length : 0);
          if (!editorText || editorText.length < 5) {
            throw new Error("Validation Failed: Carousel caption lost after document upload and refill failed!");
          }
        }
        await page.screenshot({ path: `${prefix}_draft_composer.png` });
      }

      // ========== POST NOW or SCHEDULE ==========
      if (process.env.POST_NOW === '1') {
        console.log("POST_NOW=1 — clicking Post immediately (no schedule)...");
        await page.screenshot({ path: `${prefix}_final_draft.png` });
        const clickedPostNow = await clickNativelyShadow(page, (root) => {
          const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
          const container = modal || root;
          const buttons = Array.from(container.querySelectorAll('button'));
          return buttons.find((b) => {
            const t = (b.innerText || '').trim();
            const label = (b.getAttribute('aria-label') || '').trim();
            const disabled =
              b.disabled ||
              b.getAttribute('disabled') !== null ||
              b.getAttribute('aria-disabled') === 'true' ||
              (typeof b.className === 'string' && b.className.includes('disabled'));
            if (disabled) return false;
            return t === 'Post' || label === 'Post';
          });
        });
        if (!clickedPostNow) throw new Error("Could not find enabled 'Post' button");
        console.log("Success! Waiting 6s for publish to complete...");
        await new Promise(r => setTimeout(r, 6000));
      } else {
      console.log("Opening Schedule Settings...");
      const clickedScheduleIcon = await clickNativelyShadow(page, (root) => {
        const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
        const container = modal || root;
        const buttons = Array.from(container.querySelectorAll('button'));
        // Company page composer uses an explicit "Schedule post" button
        const byText = buttons.find(b => {
          const t = (b.innerText || '').trim().toLowerCase();
          const label = (b.getAttribute('aria-label') || '').toLowerCase();
          return t === 'schedule post' || label === 'schedule post' ||
            label.includes('schedule post') || (label.includes('schedule') && !label.includes('scheduled'));
        });
        if (byText) return byText;
        const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
        if (postBtn && postBtn.previousElementSibling) {
          return postBtn.previousElementSibling;
        }
        return buttons.find(b => b.ariaLabel && b.ariaLabel.includes('Schedule'));
      });
      if (!clickedScheduleIcon) throw new Error("Could not find or click Schedule post clock icon");
      await new Promise(r => setTimeout(r, 3000));

      // ========== SET DATE & TIME ==========
      console.log(`Setting schedule: Date=${post.date}, Time=${post.time}`);
      await fillFieldShadow(page, 'input[placeholder*="Date"], input[aria-label*="date"], input[id*="date"]', post.date);
      
      let normalizedTime = post.time;
      if (normalizedTime.startsWith('0')) {
        normalizedTime = normalizedTime.substring(1);
      }
      await fillTimeComboboxShadow(page, 'input[placeholder*="Time"], input[aria-label*="time"], input[id*="time"], input[role="combobox"]', normalizedTime);

      await page.screenshot({ path: `${prefix}_schedule_settings.png` });

      // Click Next
      console.log("Saving schedule settings (clicking Next)...");
      const clickedNext = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Next'
        );
      });
      if (!clickedNext) throw new Error("Could not click Next in schedule modal");
      await new Promise(r => setTimeout(r, 3000));

      await page.screenshot({ path: `${prefix}_final_draft.png` });

      // Click final Schedule
      console.log("Clicking final 'Schedule' button...");
      const clickedScheduleFinal = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Schedule'
        );
      });
      if (!clickedScheduleFinal) throw new Error("Could not find final 'Schedule' button in composer modal");
      
      console.log("Success! Waiting 6s for scheduling process to complete...");
      await new Promise(r => setTimeout(r, 6000));
      }

      let isClosed = await page.evaluate(() => {
        function findEl(root, sel) {
          if (!root) return null;
          const el = root.querySelector(sel);
          if (el) return el;
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
          let node;
          while (node = walker.nextNode()) {
            if (node.shadowRoot) {
              const found = findEl(node.shadowRoot, sel);
              if (found) return found;
            }
          }
          return null;
        }
        return !findEl(document.body, '.ql-editor');
      });
      if (!isClosed) {
        console.log("Composer still open — dismissing and continuing...");
        await page.evaluate(() => {
          function findDismissBtn(root) {
            if (!root) return null;
            const btn = Array.from(root.querySelectorAll('button')).find(
              b => {
                const label = b.getAttribute('aria-label') || '';
                const txt = b.innerText || '';
                return label.includes('Dismiss') || txt.includes('Dismiss') || label.toLowerCase() === 'close';
              }
            );
            if (btn) return btn;
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {
              if (node.shadowRoot) {
                const found = findDismissBtn(node.shadowRoot);
                if (found) return found;
              }
            }
            return null;
          }
          const dismissBtn = findDismissBtn(document.body);
          if (dismissBtn) dismissBtn.click();
        });
        await new Promise(r => setTimeout(r, 3000));
        isClosed = await page.evaluate(() => {
          function findEl(root, sel) {
            if (!root) return null;
            const el = root.querySelector(sel);
            if (el) return el;
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {
              if (node.shadowRoot) {
                const found = findEl(node.shadowRoot, sel);
                if (found) return found;
              }
            }
            return null;
          }
          return !findEl(document.body, '.ql-editor');
        });
        if (!isClosed) console.warn("Composer may still be open — post may have scheduled anyway.");
      }
      
      console.log(`✓ Successfully scheduled Post ${post.id}/${posts.length}!`);
      okPosts.push(post.id);
      // Cool down between posts — LinkedIn UI gets flaky if we hammer Start a post
      await new Promise(r => setTimeout(r, 4000));
      } catch (postErr) {
        console.error(`✗ Failed Post ${post.id}/${posts.length}:`, postErr.message || postErr);
        failedPosts.push({ id: post.id, type: post.type, date: post.date, time: post.time, error: String(postErr.message || postErr) });
        try {
          await page.screenshot({ path: `${prefix}_FAILED.png` });
        } catch (_) {}
        try {
          await page.keyboard.press('Escape');
          await page.keyboard.press('Escape');
        } catch (_) {}
        await new Promise(r => setTimeout(r, 3000));
      }
    }

    console.log(`\n${'='.repeat(60)}`);
    console.log(`✓ SCHEDULED ${okPosts.length}/${queue.length} posts this run (ids: ${okPosts.join(', ') || 'none'})`);
    if (failedPosts.length) {
      console.log(`✗ FAILED ${failedPosts.length}:`);
      for (const f of failedPosts) {
        console.log(`  #${f.id} ${f.type} ${f.date} ${f.time} — ${f.error}`);
      }
      console.log(`Resume with: START_POST_ID=${failedPosts[0].id} SCHEDULE_FILE=${path.basename(scheduleFile)} node schedule_all_posts.cjs`);
    } else {
      console.log(`✓ ALL ${queue.length} REMAINING POSTS SCHEDULED SUCCESSFULLY!`);
    }
    console.log(`${'='.repeat(60)}`);
    process.exit(failedPosts.length ? 1 : 0);

  } catch (err) {
    console.error("Automator Exception:", err);
    try {
      const tmpDir = os.tmpdir();
      const dirs = fs.readdirSync(tmpDir).filter(name =>
        name.startsWith('agent-browser-chrome-') || name.startsWith('agent-browser-profile-')
      );
      if (dirs.length > 0) {
        const latestDir = dirs.map(name => {
          const fullPath = path.join(tmpDir, name);
          return { path: fullPath, mtime: fs.statSync(fullPath).mtimeMs };
        }).sort((a, b) => b.mtime - a.mtime)[0].path;
        const portFile = path.join(latestDir, 'DevToolsActivePort');
        const content = fs.readFileSync(portFile, 'utf8');
        const port = content.split('\n')[0].trim();
        const errBrowser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
        const errPages = await errBrowser.pages();
        const errPage = errPages.find(p => p.url().includes('linkedin.com'));
        if (errPage) {
          await errPage.screenshot({ path: path.join(__dirname, 'error_screenshot.png') });
          console.log("Saved error screenshot.");
        }
      }
    } catch (screenErr) {
      console.error("Failed to capture error screenshot:", screenErr);
    }
    process.exit(1);
  }
})();
