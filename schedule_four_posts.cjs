const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

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
    // Dynamically remove messaging overlays to prevent blocking clicks
    await page.evaluate(() => {
      document.querySelectorAll('.msg-overlay-container, [class*="msg-overlay"], #msg-overlay').forEach(el => el.remove());
    });

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
      const tagAndClass = await page.evaluate(e => {
        return `${e.tagName} class="${e.className}" text="${e.innerText ? e.innerText.trim() : ''}"`;
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

async function clickNativelyShadowRetry(page, finderFn, timeout = 15000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const clicked = await clickNativelyShadow(page, finderFn);
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
      type: 'carousel',
      date: '06/11/2026',
      time: '9:15 PM',
      caption: `Scaling to seven figures is a feat.
But maintaining it? That's the real challenge.

Too many founders hit a revenue peak only to let the business slide.
Why? Because they focused on the raw number instead of building a system.

Here's the reality:
• High ad spend can mask a lack of organic demand.
• Revenue does not equal a sustainable business.
• Profit and retention are what actually keep you alive.

The dream is a business that grows through efficiency, not just buying traffic.
If you don't build a system that runs without your constant attention, the growth will vanish.

How do you balance aggressive growth with long-term stability?

♻️ Repost to save a freelancer from the revenue trap.

Follow @founderswing for daily frameworks.`,
      assetPath: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/linkedin-carousel-2026-06-11.pdf',
      title: 'Built $1.06M revenue with 17,000 orders'
    },
    {
      id: 2,
      type: 'infographic',
      date: '06/12/2026',
      time: '12:15 AM',
      caption: `The cost of AI adoption is reaching an extreme.

Some companies are now spending $7,500 per employee every single month on AI tools.
This spend is becoming a significant portion of their payroll.

For many firms:
• The cost of AI tools is starting to rival the cost of human talent.
• They are spending $90,000 annually per head just on software.

The critical question:
Does the productivity gain actually justify this level of spending?

Is this level of spending a smart long-term bet, or a bubble about to burst?

♻️ Repost to help a founder benchmark their AI costs.

Follow @founderswing for more data drops.`,
      assetPath: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/linkedin-infographic.png'
    },
    {
      id: 3,
      type: 'regular',
      date: '06/12/2026',
      time: '3:15 AM',
      caption: `To make AI agents 10x more useful, stop giving them generic instructions.

Instead, give them a "Business Context File."

Upload a single document that lists:
1. Target customer personas
2. Top 3 competitor weaknesses
3. Brand voice guidelines (e.g., "Professional but blunt")
4. Specific goals for the month

Tell the AI:
"Reference this file before every single response."

This stops the AI from guessing and makes the output incredibly accurate.

Have you tried using a dedicated context file for your AI agents yet?

Follow @founderswing for more insights.`
    },
    {
      id: 4,
      type: 'poll',
      date: '06/12/2026',
      time: '6:15 AM',
      caption: `Freelancing offers freedom.
But it also creates a high-stakes environment.

Losing a single client can feel like a total collapse.
And the mental toll of hiding this struggle from family and peers often outweighs the financial stress itself.

Which is the hardest part of the freelance transition?
(Vote in the poll below)

Share a story of how the transition to self-employment actually felt for you in the comments.`,
      title: 'Which is the hardest part of the freelance transition?',
      pollOptionsStr: 'Losing a primary client|Hiding failures from family|Finding the first 3 clients|Managing inconsistent income'
    },
    {
      id: 5,
      type: 'regular',
      date: '06/12/2026',
      time: '9:15 AM',
      caption: `Technical debt is a silent killer for early-stage ventures.

Too many founders fall into a classic trap:
Paying for a pretty interface without a working engine.

A common failure:
A non-technical founder pays for a prototype that looks finished, but only functions in 20% of the intended ways.

This creates a deceptive layer of progress:
• The product looks great in a demo.
• The actual logic is a mess of disconnected pieces.

This is a massive risk for the incoming technical co-founder or lead engineer.
They inherit a codebase that requires a complete rewrite rather than a simple polish.

The cost:
• Delays the actual product launch by months.
• Drains limited capital on fixing avoidable mistakes.

The solution:
Prioritize function over form.

A crude interface that solves a real problem is infinitely more valuable than a polished app that does nothing.
Technical founders must audit the actual logic and data flow before signing any agreements.
You need to see the guts of the system, not just the skin.

How do you properly audit a "vibe-coded" prototype before joining a team?

Follow @founderswing for more insights.`
    },
    {
      id: 6,
      type: 'regular',
      date: '06/12/2026',
      time: '12:15 PM',
      caption: `A new tool called Oasis 3 can now generate photorealistic driving environments in real-time.

It creates hours of simulated traffic and roads for autonomous vehicle testing via an API.

Why this matters:
• Developers can test cars in a virtual world before hitting the actual pavement.
• It completely removes the risk of physical crashes during early testing.

Tool featured: Oasis 3 (by Decart)
Source: TechCrunch AI
Archetype: Tool Spotlight | Emotion: WOW

Follow @founderswing for more insights.`
    },
    {
      id: 7,
      type: 'regular',
      date: '06/12/2026',
      time: '3:15 PM',
      caption: `The AI sector is moving fast this week.

Here's the rapid-fire roundup:
• Amazon borrowed $17.5B to fund its AI infrastructure needs.
• Warner Music bought Sureel AI to track when artists' work is used for training.
• Niteshift raised $7M to fight model lock-in.
• Jedify got $24M to give agents better business context.
• SpaceX is eyeing a massive IPO driven by space data center plans.

Source: TechCrunch AI
Archetype: Weekly Roundup | Emotion: OHHH

Which of these updates do you think will have the biggest long-term impact?

Follow @founderswing for more insights.`
    },
    {
      id: 8,
      type: 'regular',
      date: '06/12/2026',
      time: '6:15 PM',
      caption: `Amazon is borrowing $17.5B from banks to fund its AI growth.

This is a massive bet on the future of cloud computing.
The company is spending billions on chips and data centers to compete.

The major risk:
• Mounting debt on the balance sheet.
• If the productivity gains from AI do not materialize quickly, these loans become a heavy burden.

Source: TechCrunch AI
Archetype: Plain English Breakdown | Emotion: OHHH

Do you think tech giants are over-leveraging themselves in the AI race?

Follow @founderswing for more insights.`
    },
    {
      id: 9,
      type: 'regular',
      date: '06/12/2026',
      time: '9:15 PM',
      caption: `Niteshift is launching a way for companies to use AI coding without being locked into one model maker.

This gives developers the power to switch tools without losing their entire setup.

Why this is a game-changer:
• Switch models seamlessly as pricing or capabilities change.
• Retain complete control over your development workflow.
• Avoid being held hostage by a single AI provider.

Control over the tech stack is the only way to stay lean and agile.

Source: TechCrunch AI
Archetype: Unfair Advantage | Emotion: WOW

Follow @founderswing for more insights.`
    },
    {
      id: 10,
      type: 'regular',
      date: '06/13/2026',
      time: '12:15 AM',
      caption: `The rise of AI agents is changing the job market.

Companies are now hiring for roles that focus on giving these agents "business context."

This means the new high-income skill is:
• Not just writing prompts.
• But organizing and structuring company data so an AI can actually use it.

Learning how to structure business knowledge for AI is the quickest way to increase your market value today.

Source: TechCrunch AI
Archetype: Career/Income | Emotion: AHA

Follow @founderswing for more insights.`
    },
    {
      id: 11,
      type: 'regular',
      date: '06/13/2026',
      time: '3:15 AM',
      caption: `Warner Music buying Sureel AI is a move for control, not innovation.

They are trying to build a fence around their intellectual property.
This is a defensive play in a world where AI can mimic any voice.

The big picture:
• The battle for attribution will be the biggest legal fight of the decade.
• The music industry is just the first to draw a line in the sand.

Source: TechCrunch AI
Archetype: Hot Take | Emotion: THINK

How do you think we should handle copyright and attribution in the era of generative AI?

Follow @founderswing for more insights.`
    }
  ];

  try {
    console.log("Locating active devtools port dynamically...");
    const tmpDir = os.tmpdir();
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
    const page = pages.find(p => p.url().includes('linkedin.com'));
    if (!page) {
      console.error("LinkedIn page not found!");
      process.exit(1);
    }
    await page.bringToFront();
    await page.setViewport({ width: 1280, height: 1200 });

    for (const post of posts) {
      console.log(`\n==========================================`);
      console.log(`Scheduling Post ${post.id} (${post.type}): Date=${post.date}, Time=${post.time}`);
      console.log(`==========================================`);
      const prefix = `/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/post_${post.type}`;

      // ALWAYS navigate/reload to feed home page to guarantee a clean slate and close all modals
      console.log("Navigating to feed home page...");
      try {
        await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 15000 });
      } catch (err) {
        console.log("Navigation timeout/error, continuing:", err.message);
      }
      await new Promise(r => setTimeout(r, 4000));

      // Hide messaging overlays to prevent blocking clicks
      console.log("Hiding messaging overlays...");
      await page.evaluate(() => {
        const style = document.createElement('style');
        style.id = 'hide-msg-overlay-style';
        style.innerHTML = `
          .msg-overlay-container, 
          [class*="msg-overlay"], 
          #msg-overlay { 
            display: none !important; 
          }
        `;
        document.head.appendChild(style);
      });

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

      // Handle specific attachments before writing caption
      if (post.type === 'poll') {
        console.log("Handling Poll attachment...");
        // Click More
        await clickNativelyShadow(page, (root) => {
          return Array.from(root.querySelectorAll('button')).find(
            b => (b.ariaLabel && b.ariaLabel.includes('More')) || (b.innerText && b.innerText.includes('More'))
          );
        });
        await new Promise(r => setTimeout(r, 1500));

        // Click Create a poll
        const clickedPoll = await clickNativelyShadow(page, (root) => {
          return Array.from(root.querySelectorAll('button')).find(
            b => (b.ariaLabel && b.ariaLabel.includes('Create a poll')) || (b.innerText && b.innerText.includes('Create a poll'))
          );
        });
        if (!clickedPoll) throw new Error("Could not find 'Create a poll' button");
        await new Promise(r => setTimeout(r, 2000));

        // Fill question using keyboard type
        await waitForSelectorShadow(page, 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"]');
        const questionEl = await getElementShadow(page, 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"]');
        await questionEl.focus();
        await page.keyboard.type(post.title);
        await questionEl.dispose();
        console.log("Filled poll question.");

        const options = post.pollOptionsStr.split('|').map(o => o.trim());
        
        // Get option input elements
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

        // Fill Option 1 & 2
        let optionInputs = await getInputs();
        if (optionInputs.length < 2) throw new Error("Option inputs not found");
        
        await optionInputs[0].focus();
        await page.keyboard.type(options[0]);
        await new Promise(r => setTimeout(r, 300));
        
        await optionInputs[1].focus();
        await page.keyboard.type(options[1]);
        await new Promise(r => setTimeout(r, 300));

        // Fill Option 3 if exists
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

        // Fill Option 4 if exists
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

        // Programmatic verification check before clicking Done
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

        // Take screenshot of filled poll creator modal
        console.log("Taking screenshot of filled poll creation modal...");
        await page.screenshot({ path: `${prefix}_filled.png` });

        // Click Done inside Poll creator (wait until enabled)
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
        if (!clickedPollDone) throw new Error("Could not click Done on Poll creator (button remained disabled or was not found)");
        await new Promise(r => setTimeout(r, 2000));

      } else if (post.type === 'carousel') {
        console.log("Handling Carousel document upload...");
        let clickedDoc = await clickNativelyShadow(page, (root) => {
          const btns = Array.from(root.querySelectorAll('button'));
          return btns.find(b => b.ariaLabel && b.ariaLabel.includes('Add a document')) ||
                 btns.find(b => b.innerText && b.innerText.includes('Add a document')) ||
                 btns.find(b => b.innerText && b.innerText.includes('document'));
        });

        if (!clickedDoc) {
          // Expand More
          await clickNativelyShadow(page, (root) => {
            return Array.from(root.querySelectorAll('button')).find(
              b => (b.ariaLabel && b.ariaLabel.includes('More')) || (b.innerText && b.innerText.includes('More'))
            );
          });
          await new Promise(r => setTimeout(r, 1500));
          clickedDoc = await clickNativelyShadow(page, (root) => {
            const btns = Array.from(root.querySelectorAll('button'));
            return btns.find(b => b.ariaLabel && b.ariaLabel.includes('Add a document')) ||
                   btns.find(b => b.innerText && b.innerText.includes('Add a document')) ||
                   btns.find(b => b.innerText && b.innerText.includes('document'));
          });
        }
        if (!clickedDoc) throw new Error("Could not find 'Add a document' button");
        await new Promise(r => setTimeout(r, 2000));

        // Upload file traversing shadow roots
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
        if (!fileInputHandle) throw new Error("Could not find file input in shadow DOM");
        const fileInput = fileInputHandle.asElement();
        await fileInput.uploadFile(post.assetPath);
        console.log("Document uploaded. Waiting 4s for processing...");
        await new Promise(r => setTimeout(r, 4000));

        // Input title using simulated typing
        await waitForSelectorShadow(page, 'input.document-title-form__title-input, input[placeholder*="title to your document"]');
        const titleInput = await getElementShadow(page, 'input.document-title-form__title-input, input[placeholder*="title to your document"]');
        await titleInput.focus();
        await page.keyboard.type(post.title);
        await titleInput.dispose();
        console.log("Document title typed:", post.title);

        // Verify title is typed in DOM
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

        // Take screenshot of document uploader modal
        console.log("Taking screenshot of document uploader modal...");
        await page.screenshot({ path: `${prefix}_doc_uploaded.png` });

        // Click Done (wait until enabled)
        const clickedDocDone = await clickNativelyShadowRetry(page, (root) => {
          return Array.from(root.querySelectorAll('button')).find(b => {
            const txt = b.innerText ? b.innerText.trim() : '';
            const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0 || window.getComputedStyle(b).display !== 'none';
            const isNotVideoJS = typeof b.className === 'string' && !b.className.includes('vjs-');
            const isDisabled = b.hasAttribute('disabled') || b.disabled || (typeof b.className === 'string' && b.className.includes('disabled'));
            return txt === 'Done' && isVisible && isNotVideoJS && !isDisabled;
          });
        });
        if (!clickedDocDone) throw new Error("Could not click Done on Document uploader (button remained disabled or was not found)");
        await new Promise(r => setTimeout(r, 3000));

      } else if (post.type === 'infographic') {
        console.log("Handling Infographic image upload...");
        const clickedMedia = await clickNativelyShadow(page, (root) => {
          const btns = Array.from(root.querySelectorAll('button'));
          return btns.find(b => b.ariaLabel && b.ariaLabel.includes('Add media')) ||
                 btns.find(b => b.innerText && b.innerText.includes('Add media')) ||
                 btns.find(b => b.innerText && b.innerText.includes('Photo')) ||
                 btns.find(b => b.ariaLabel && b.ariaLabel.includes('Photo'));
        });
        if (!clickedMedia) throw new Error("Could not find image upload button");
        await new Promise(r => setTimeout(r, 2000));

        // Upload file
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
        if (!fileInputHandle) throw new Error("Could not find file input in shadow DOM");
        const fileInput = fileInputHandle.asElement();
        await fileInput.uploadFile(post.assetPath);
        console.log("Image uploaded. Waiting 4s for processing...");
        await new Promise(r => setTimeout(r, 4000));

        // Take screenshot of image editor modal
        console.log("Taking screenshot of image editor modal...");
        await page.screenshot({ path: `${prefix}_image_uploaded.png` });

        // Click Next/Done in image editor (wait until enabled)
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
        if (!clickedImageNext) throw new Error("Could not click Next/Done in image editor (button remained disabled or was not found)");
        await new Promise(r => setTimeout(r, 3000));
      }

      // Fill text caption inside editor
      console.log("Filling post caption text...");
      await waitForSelectorShadow(page, editorSelector, 15000);
      const editorEl = await getElementShadow(page, editorSelector);
      await editorEl.focus();

      // Clear contents first
      await page.evaluate((el) => {
        el.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
      }, editorEl);
      await new Promise(r => setTimeout(r, 1000));

      // Type paragraph by paragraph, pressing Enter in between, to preserve paragraph breaks correctly in Quill editor
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
      await new Promise(r => setTimeout(r, 2000));
      await editorEl.dispose();

      // Verify caption is populated
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

      // Take screenshot of prepared draft composer before scheduling
      console.log("Taking screenshot of draft composer with caption and assets...");
      await page.screenshot({ path: `${prefix}_draft_composer.png` });

      // Open Schedule modal
      console.log("Opening Schedule Settings...");
      const clickedScheduleIcon = await clickNativelyShadow(page, (root) => {
        const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
        const container = modal || root;
        const buttons = Array.from(container.querySelectorAll('button'));
        const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
        if (postBtn && postBtn.previousElementSibling) {
          return postBtn.previousElementSibling;
        }
        return buttons.find(b => b.ariaLabel && b.ariaLabel.includes('Schedule'));
      });
      if (!clickedScheduleIcon) throw new Error("Could not find or click Schedule post clock icon");
      await new Promise(r => setTimeout(r, 3000));

      // Fill date and time
      console.log(`Setting schedule: Date=${post.date}, Time=${post.time}`);
      await fillFieldShadow(page, 'input[placeholder*="Date"], input[aria-label*="date"], input[id*="date"]', post.date);
      
      // Normalize time if it has leading zero to match combobox input logic
      let normalizedTime = post.time;
      if (normalizedTime.startsWith('0')) {
        normalizedTime = normalizedTime.substring(1);
      }
      await fillTimeComboboxShadow(page, 'input[placeholder*="Time"], input[aria-label*="time"], input[id*="time"], input[role="combobox"]', normalizedTime);

      // Take screenshot of schedule settings modal
      console.log("Taking screenshot of filled schedule settings modal...");
      await page.screenshot({ path: `${prefix}_schedule_settings.png` });

      // Click Next inside schedule settings
      console.log("Saving schedule settings (clicking Next)...");
      const clickedNext = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Next'
        );
      });
      if (!clickedNext) throw new Error("Could not click Next in schedule modal");
      await new Promise(r => setTimeout(r, 3000));

      // Take screenshot of final schedule screen
      console.log("Taking screenshot of final schedule composer screen...");
      await page.screenshot({ path: `${prefix}_final_draft.png` });

      // Click final Schedule button to submit
      console.log("Clicking final 'Schedule' button...");
      const clickedScheduleFinal = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Schedule'
        );
      });
      if (!clickedScheduleFinal) throw new Error("Could not find final 'Schedule' button in composer modal");
      
      // Wait for modal to close
      console.log("Success! Waiting 6s for scheduling process to complete...");
      await new Promise(r => setTimeout(r, 6000));

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

    console.log("\n✓ ALL 4 POSTS HAVE BEEN SCHEDULED SUCCESSFULLY!");
    process.exit(0);

  } catch (err) {
    console.error("Automator Exception:", err);
    try {
      const tmpDir = os.tmpdir();
      const dirs = fs.readdirSync(tmpDir).filter(name => name.startsWith('agent-browser-chrome-'));
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
          await errPage.screenshot({ path: '/Users/prithal/3d website/error_screenshot.png' });
          console.log("Saved error screenshot to /Users/prithal/3d website/error_screenshot.png");
        }
      }
    } catch (screenErr) {
      console.error("Failed to capture error screenshot:", screenErr);
    }
    process.exit(1);
  }
})();
