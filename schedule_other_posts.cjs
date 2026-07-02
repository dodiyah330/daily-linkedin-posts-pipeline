const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

async function getElementShadow(page, selector) {
  const handle = await page.evaluateHandle((sel) => {
    function findEl(root) {
      if (!root) return null;
      const el = root.querySelector(sel);
      if (el) return el;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.shadowRoot) {
          const found = findEl(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return findEl(document.body);
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

async function clickNativelyShadow(page, finderFn) {
  try {
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
    if (el) {
      await page.evaluate(e => e.focus(), el);
      await el.click();
      await page.evaluate(e => e.click(), el);
      await el.dispose();
      return true;
    }
    return false;
  } catch (err) {
    console.error("clickNativelyShadow error:", err);
    return false;
  }
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

(async () => {
  const posts = [
    {
      id: 1,
      date: '06/11/2026',
      time: '9:15 AM',
      caption: `Headline: App development without a developer team\n\nBuilding a mobile app usually requires a designer, a product manager, and two developers working for months. A new platform called MWM AI just launched a tool that replaces the entire squad with AI agents.\n\nThe system sets up a three-agent squad. The product manager agent drafts the requirements, the designer agent builds the layout, and the developer agent writes the code. They debate features, test the code internally, and output a functional app in about 15 minutes.\n\nThis means solo entrepreneurs can test mobile app ideas in real time instead of spending thousands on prototypes.\n\nIt is free to start. Search for MWM AI online to see the agent squad build a calculator or a task manager in a short screen recording.\n\nHow will this change the speed at which your team tests new product features?`
    },
    {
      id: 3,
      date: '06/11/2026',
      time: '12:15 PM',
      caption: `Headline: The enterprise cloud alliance explained in plain English\n\nIBM and Google Cloud just announced a major partnership to scale enterprise agent platforms. The news sounds like corporate boilerplate, but it affects how large companies run their daily operations.\n\nCurrently, big businesses store data across different clouds. When they try to build AI systems, the software gets stuck because it cannot access data stored on a competitor's database. An agent on Google Cloud cannot talk to a database on IBM Cloud.\n\nThis new partnership connects the two ecosystems. A company can now build one AI agent that reads client data on IBM and automatically updates sales records on Google Cloud.\n\nThe payoff is faster processing times and fewer database errors. Tasks that required manual data transfer between systems are now automated.\n\nHowever, there is an honest limitation. Setting up these connected agents still requires complex data mapping, meaning companies cannot deploy them without significant IT setup.\n\nHow does your team handle the challenge of connecting AI tools across different cloud databases?`
    },
    {
      id: 4,
      date: '06/11/2026',
      time: '3:15 PM',
      caption: `Headline: Generating complex financial memos in minutes\n\nMost financial analysts spend fifteen hours writing a single credit memo. A new tool launched by S&P Global changes this by automating the research process.\n\nThe platform connects database records with writing agents. An analyst inputs a company name, and the tool automatically gathers historical revenue, debt metrics, and market conditions to write a complete draft in under five minutes.\n\nThis means small investment firms can evaluate four times as many deals without hiring more research staff.\n\nAt FounderWing, we keep track of these tools because they show how automated research is moving from experimental apps to institutional finance.\n\nIt is currently being rolled out to enterprise clients. Search for S&P Global Credit Memo to read the release notes.\n\nWhat is the most time-consuming research task in your team's weekly schedule?`
    },
    {
      id: 5,
      date: '06/11/2026',
      time: '6:15 PM',
      caption: `Headline: The new high-paying career category in tech\n\nThe career of the prompt engineer is declining. The new, higher-paying opportunity is the Multi-Agent Squad Manager.\n\nAs companies move from simple chatbots to squads of connected agents, the required skill is no longer writing the perfect question. Instead, it is managing how different agents talk to each other.\n\nAn agent squad manager sets up a team of specialized agents, defines their roles, and resolves conflicts when they disagree. For example, they manage a PM agent, a designer agent, and a developer agent to ensure they ship code without looping.\n\nThis changes the job market. Companies are paying top salaries for people who understand how to structure digital systems rather than just write prompts.\n\nTo prepare for this shift, build a three-agent squad using a local tool this week. Assign roles, set a goal, and write rules for how they must share files.\n\nHave you started managing automated workflows in your daily team operations?`
    },
    {
      id: 6,
      date: '06/11/2026',
      time: '9:15 PM',
      caption: `Headline: The hidden reason behind the Anthropic IPO filing\n\nThe headlines are framing Anthropic's confidential IPO filing as a sign of startup strength. The reality is likely the opposite: it is a race to cash out before the training cost squeeze hits.\n\nBuilding frontier models requires billions in computer chips. Currently, startups rely on venture capital firms to fund these training runs. But as training costs climb, venture capital pools are running dry.\n\nGoing public allows Anthropic to access public markets for funding. However, public markets demand profits, not just impressive demos. If the next model does not show a clear path to profitability, the stock could crash.\n\nAt FounderWing, we see this as a warning for builders. If the companies creating the models are rushing to go public for survival capital, relying on their low prices is a risky strategy.\n\nAn IPO might secure cash for Anthropic, but it will also force them to raise pricing for developers and businesses.\n\nDo you believe public markets will continue to fund unprofitable model training runs?`
    },
    {
      id: 7,
      date: '06/12/2026',
      time: '12:15 AM',
      caption: `Headline: Steal this three-step agent squad template\n\nAn agent squad template to automate content research.\n\nUse this workflow in any agent setup:\n\n1. Agent A (Researcher): Read the URL and list 5 facts.\n2. Agent B (Editor): Rewrite the facts into a three-sentence summary without jargon.\n3. Agent C (Reviewer): Check the summary against the original URL for accuracy.\n\nThis team setup prevents the AI from making things up and saves 30 minutes per article.\n\nSave this post to build your squad.\n\nWhich step in your research workflow takes the most time to review?`
    }
  ];

  try {
    console.log("Locating active devtools port...");
    const tmpDir = '/var/folders/c7/crm35d6s6t18fsxlt7ylmf580000gn/T';
    const dirs = fs.readdirSync(tmpDir).filter(name => name.startsWith('agent-browser-chrome-'));
    if (dirs.length === 0) {
      throw new Error('No agent-browser-chrome directories found in tmp');
    }
    const latestDir = dirs.map(name => {
      const fullPath = path.join(tmpDir, name);
      return { path: fullPath, mtime: fs.statSync(fullPath).mtimeMs };
    }).sort((a, b) => b.mtime - a.mtime)[0].path;
    const portFile = path.join(latestDir, 'DevToolsActivePort');
    const content = fs.readFileSync(portFile, 'utf8');
    const port = content.split('\n')[0].trim();
    console.log(`Connecting to browser on port ${port}...`);
    const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com/feed'));
    if (!page) {
      console.error("LinkedIn feed page not found!");
      process.exit(1);
    }
    await page.bringToFront();
    await page.setViewport({ width: 1280, height: 1200 });

    for (const post of posts) {
      console.log(`\n==========================================`);
      console.log(`Scheduling Post ${post.id}: Date=${post.date}, Time=${post.time}`);
      console.log(`==========================================`);
      const prefix = `/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/post_other_${post.id}`;

      // ALWAYS navigate/reload to feed home page to guarantee a clean slate and close all modals
      console.log("Navigating to feed home page...");
      try {
        await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 15000 });
      } catch (err) {
        console.log("Navigation timeout/error, continuing:", err.message);
      }
      await new Promise(r => setTimeout(r, 3000));

      // Close open composer
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
      const clickStartPost = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('*')).find(
          el => (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || el.getAttribute('aria-label') === 'Start a post') &&
                el.innerText && el.innerText.trim().includes('Start a post')
        );
      });
      if (!clickStartPost) throw new Error("Could not find 'Start a post' button");

      const editorSelector = '.ql-editor, [contenteditable="true"]';
      await waitForSelectorShadow(page, editorSelector, 15000);
      await new Promise(r => setTimeout(r, 1000));

      const editorEl = await getElementShadow(page, editorSelector);
      if (!editorEl) throw new Error("Editor not found");

      console.log("Focusing and clearing editor...");
      await page.evaluate((el) => {
        el.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
      }, editorEl);
      await new Promise(r => setTimeout(r, 1000));

      console.log("Typing caption...");
      await page.keyboard.type(post.caption);
      await new Promise(r => setTimeout(r, 2000));
      await editorEl.dispose();

      // Verify caption
      const editorText = await page.evaluate(() => {
        function findText(root) {
          const el = root.querySelector('.ql-editor');
          if (el) return el.innerText.trim();
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
          let node;
          while (node = walker.nextNode()) {
            if (node.shadowRoot) {
              const txt = findText(node.shadowRoot);
              if (txt) return txt;
            }
          }
          return null;
        }
        return findText(document.body);
      });
      console.log("Caption text in editor (length):", editorText ? editorText.length : 0);
      if (!editorText || editorText.length < 5) {
        throw new Error("Validation Failed: Post caption in editor is blank or too short!");
      }

      await page.screenshot({ path: `${prefix}_draft.png` });

      console.log("Opening Schedule Settings...");
      const clickedScheduleIcon = await clickNativelyShadow(page, (root) => {
        const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
        const container = modal || root;
        const buttons = Array.from(container.querySelectorAll('button'));
        const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
        if (postBtn && postBtn.previousElementSibling) {
          return postBtn.previousElementSibling;
        }
        return buttons.find(b => {
          const label = b.getAttribute('aria-label') || '';
          return label.includes('Schedule');
        });
      });
      if (!clickedScheduleIcon) throw new Error("Could not find Schedule icon");
      await new Promise(r => setTimeout(r, 3000));

      console.log(`Setting date/time values...`);
      await fillFieldShadow(page, 'input[placeholder*="Date"], input[aria-label*="date"], input[id*="date"]', post.date);
      await fillTimeComboboxShadow(page, 'input[placeholder*="Time"], input[aria-label*="time"], input[id*="time"], input[role="combobox"]', post.time);

      await page.screenshot({ path: `${prefix}_schedule_settings.png` });

      console.log("Saving schedule settings (clicking Next)...");
      const clickedNext = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Next'
        );
      });
      if (!clickedNext) throw new Error("Could not click Next in schedule modal");
      await new Promise(r => setTimeout(r, 3000));

      await page.screenshot({ path: `${prefix}_final_draft.png` });

      console.log("Clicking final 'Schedule' button...");
      const clickedScheduleFinal = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Schedule'
        );
      });
      if (!clickedScheduleFinal) throw new Error("Could not find final 'Schedule' button");
      
      console.log("Waiting 6s for scheduling process to complete...");
      await new Promise(r => setTimeout(r, 6000));

      // Verify closed
      const isClosed = await page.evaluate(() => {
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
      if (!isClosed) throw new Error("composer editor did not close. Scheduling might have failed!");
      
      console.log(`✓ Successfully scheduled Post ${post.id}!`);
    }

    console.log("\n✓ ALL OTHER TEXT POSTS HAVE BEEN SCHEDULED SUCCESSFULLY!");
    process.exit(0);

  } catch (err) {
    console.error("Automator Exception:", err);
    process.exit(1);
  }
})();
