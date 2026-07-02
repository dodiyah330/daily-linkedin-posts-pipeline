const puppeteer = require('puppeteer-core');
const fs = require('fs');

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
  const caption = fs.readFileSync('/Users/prithal/3d website/linkedin-automation-routine/post4_caption.txt', 'utf8').trim();
  const date = '06/11/2026';
  const time = '6:15 AM';
  const pollQuestion = 'Which approach is more effective for early-stage companies?';
  const pollOptions = [
    '80-hour hustle (speed first)',
    '40-hour focus (health first)',
    'Hybrid style (milestones)',
    'Flex model (funding)'
  ];
  const prefix = '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/post_poll';

  try {
    console.log("Locating active devtools port...");
    const path = require('path');
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

    const currentUrl = page.url();
    if (!currentUrl.includes('linkedin.com/feed')) {
      console.log("Navigating to feed home page to start clean...");
      try {
        await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 15000 });
      } catch (err) {
        console.log("Navigation timeout/error, continuing anyway:", err.message);
      }
    } else {
      console.log("Already on LinkedIn feed, skipping navigation...");
    }
    await new Promise(r => setTimeout(r, 3000));

    console.log("Checking and closing any open composers first...");
    const closedComposer = await page.evaluate(() => {
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
      const hasEditor = !!findEl(document.body, '.ql-editor');
      if (!hasEditor) return "no-composer-found";

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
      if (dismissBtn) {
        dismissBtn.click();
        return "clicked-dismiss";
      }
      return "composer-found-but-no-dismiss-btn";
    });
    console.log("Composer check result:", closedComposer);
    if (closedComposer === "clicked-dismiss") {
      await new Promise(r => setTimeout(r, 2000));
    }

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

    console.log("Clicking 'More' (three dots)...");
    const clickedMore = await clickNativelyShadow(page, (root) => {
      const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
      const container = modal || root;
      return Array.from(container.querySelectorAll('button')).find(
        b => {
          const label = b.getAttribute('aria-label') || '';
          const txt = b.innerText || '';
          return (label.toLowerCase() === 'more' || txt.toLowerCase().includes('more')) && b.className.includes('share-promoted-detour-button');
        }
      );
    });
    if (!clickedMore) console.log("Warning: 'More' button not found/clicked, checking if poll option is directly visible.");
    await new Promise(r => setTimeout(r, 1500));

    console.log("Clicking 'Create a poll'...");
    const clickedPoll = await clickNativelyShadow(page, (root) => {
      const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
      const container = modal || root;
      return Array.from(container.querySelectorAll('button')).find(
        b => {
          const label = b.getAttribute('aria-label') || '';
          const txt = b.innerText || '';
          return label.toLowerCase().includes('create a poll') || txt.toLowerCase().includes('create a poll');
        }
      );
    });
    if (!clickedPoll) throw new Error("Could not find 'Create a poll' button");
    await new Promise(r => setTimeout(r, 2000));

    console.log("Filling poll question...");
    await waitForSelectorShadow(page, 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"]');
    const questionEl = await getElementShadow(page, 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"]');
    if (!questionEl) throw new Error("Poll question textarea not found");
    await questionEl.focus();
    await page.keyboard.type(pollQuestion);
    await questionEl.dispose();

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

    console.log("Filling Options 1 and 2...");
    let optionInputs = await getInputs();
    if (optionInputs.length < 2) throw new Error("Option 1 & 2 inputs not found");

    await optionInputs[0].focus();
    await page.keyboard.type(pollOptions[0]);
    await new Promise(r => setTimeout(r, 500));

    await optionInputs[1].focus();
    await page.keyboard.type(pollOptions[1]);
    await new Promise(r => setTimeout(r, 500));

    console.log("Adding third option...");
    await clickNativelyShadow(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Add option'));
    });
    await new Promise(r => setTimeout(r, 1000));
    
    optionInputs = await getInputs();
    if (optionInputs.length < 3) throw new Error("Option 3 input not found");
    await optionInputs[2].focus();
    await page.keyboard.type(pollOptions[2]);
    await new Promise(r => setTimeout(r, 500));

    console.log("Adding fourth option...");
    await clickNativelyShadow(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Add option'));
    });
    await new Promise(r => setTimeout(r, 1000));
    
    optionInputs = await getInputs();
    if (optionInputs.length < 4) throw new Error("Option 4 input not found");
    await optionInputs[3].focus();
    await page.keyboard.type(pollOptions[3]);
    await new Promise(r => setTimeout(r, 500));

    // Verification check before Done
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
    console.log("Values in options inputs:", verifyVals);
    if (verifyVals.some(v => v === "")) {
      throw new Error("Validation Failed: Blank poll options found!");
    }

    await page.screenshot({ path: `${prefix}_filled.png` });
    console.log(`Saved screenshot to: ${prefix}_filled.png`);

    console.log("Clicking Done on Poll creator...");
    const clickedDone = await clickNativelyShadow(page, (root) => {
      const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
      const container = modal || root;
      return Array.from(container.querySelectorAll('button')).find(b => {
        const txt = b.innerText ? b.innerText.trim() : '';
        const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0;
        return txt === 'Done' && isVisible;
      });
    });
    if (!clickedDone) throw new Error("Could not click Done on poll creator");
    await new Promise(r => setTimeout(r, 3000));

    console.log("Filling post caption text...");
    await waitForSelectorShadow(page, editorSelector, 15000);
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
    await page.keyboard.type(caption);
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

    await page.screenshot({ path: `${prefix}_draft_composer.png` });
    console.log(`Saved screenshot to: ${prefix}_draft_composer.png`);

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

    console.log(`Setting schedule: Date=${date}, Time=${time}`);
    await fillFieldShadow(page, 'input[placeholder*="Date"], input[aria-label*="date"], input[id*="date"]', date);
    await fillTimeComboboxShadow(page, 'input[placeholder*="Time"], input[aria-label*="time"], input[id*="time"], input[role="combobox"]', time);

    await page.screenshot({ path: `${prefix}_schedule_settings.png` });
    console.log(`Saved screenshot to: ${prefix}_schedule_settings.png`);

    console.log("Saving schedule settings (clicking Next)...");
    const clickedNext = await clickNativelyShadow(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(
        b => b.innerText && b.innerText.trim() === 'Next'
      );
    });
    if (!clickedNext) throw new Error("Could not click Next in schedule modal");
    await new Promise(r => setTimeout(r, 3000));

    await page.screenshot({ path: `${prefix}_final_draft.png` });
    console.log(`Saved screenshot to: ${prefix}_final_draft.png`);

    console.log("Clicking final 'Schedule' button...");
    const clickedScheduleFinal = await clickNativelyShadow(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(
        b => b.innerText && b.innerText.trim() === 'Schedule'
      );
    });
    if (!clickedScheduleFinal) throw new Error("Could not find final 'Schedule' button");
    
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
    
    console.log("✓ Successfully scheduled post 4!");
    process.exit(0);

  } catch (err) {
    console.error("Automator Exception:", err);
    try {
      const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' });
      const pages = await browser.pages();
      const page = pages.find(p => p.url().includes('linkedin.com/feed'));
      if (page) {
        await page.screenshot({ path: `${prefix}_error.png` });
        console.log(`Saved error screenshot to ${prefix}_error.png`);
      }
    } catch (e) {
      console.error("Failed to capture error screenshot:", e);
    }
    process.exit(1);
  }
})();
