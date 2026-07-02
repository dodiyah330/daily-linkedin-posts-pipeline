const puppeteer = require('puppeteer-core');

// Helper to recursively find an element piercing shadow roots
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

// Helper to wait for element inside shadow DOM
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

// Helper to click elements natively piercing shadow roots
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
      // Focus element
      await page.evaluate(e => e.focus(), el);
      // Native click
      await el.click();
      // Fallback click
      await page.evaluate(e => e.click(), el).catch(() => {});
      await el.dispose();
      return true;
    }
    return false;
  } catch (err) {
    console.error("clickNativelyShadow error:", err);
    return false;
  }
}

const captions = {
  // Post 1 (Carousel - Wed June 10, 2026 at 8:30 PM)
  carousel: `Left a salaried job to freelance and lost the only client 6 weeks later.

This case study shows why one client is a dependency, not a business (swipe through all slides).

Which client concentration percentage makes you start looking for new deals?

♻️ Repost to save a freelancer from the dependency trap

Follow @founderswing for daily frameworks`,

  // Post 2 (Infographic - Sun June 7, 2026 at 11:30 PM)
  infographic: `The organic reach numbers that explain why social media feels harder.

Getting attention on social networks is tighter than ever. Platforms are filtering aggressively for relevance to keep users inside their apps.

These baseline benchmarks from 2026 show the reality (visual chart details below):
- Instagram leads the pack at 3.20% average organic reach.
- Facebook follows at 2.10% for brand pages.
- LinkedIn sits at 1.68% organic reach potential.
- X (Twitter) averages 1.13% reach.
- TikTok averages 0.44% baseline organic distribution.

The takeaway: if you rely purely on broad broadcasting, your reach will shrink. Focus on high-engagement, specific formats like carousels and community-driven content.

Which platform's organic reach rate surprised you the most?

♻️ Repost to help a founder bench their social metrics correctly

Follow @founderswing for daily data drops`,

  // Post 3 (Text-only - Mon June 8, 2026 at 2:30 AM)
  creditMemos: `Credit memos used to take days. S&P Global just made them a morning task.

For anyone who's worked in credit analysis, the credit memo is one of the most time-consuming documents in finance. Pulling data, synthesizing risk factors, writing up findings, formatting everything to standard. A solid memo can eat two or three days of an analyst's week.

S&P Global just launched a platform called Credit Memo Builder that compresses that process dramatically. Analysts feed in the relevant information and a team of coordinated AI agents works through the research, analysis, and drafting, producing a structured credit memo in minutes rather than days.

The human consequence is straightforward: analysts get hours back every week. Those hours can go toward higher-judgment work, like stress-testing assumptions, having deeper client conversations, or reviewing more deals than the team could previously handle.

At Founders Wing, we have been tracking how agentic tools are quietly reshaping financial workflows, and Credit Memo Builder is one of the cleaner examples of agents doing repetitive analytical work so humans can focus on the decisions that actually require expertise.

The tool does not replace the analyst's judgment. It removes the friction that slows the analyst down before they even get to apply that judgment.

That distinction matters. A lot.

For financial professionals reading this: how much of your current week is spent on document production versus actual analysis? And if that ratio shifted, where would you redirect the time?`,

  // Post 4 (Text-only - Mon June 8, 2026 at 5:30 AM)
  anthropicIpo: `Anthropic filing for an IPO is not the triumph it looks like.

For a company that has positioned itself as the safety-first, mission-driven counterweight to OpenAI, filing for a public offering represents a hard pivot into the public market's quarterly growth expectations.

Anthropic is raising capital, but they're also entering a phase where safe, slow, safety-centric AI research becomes a tough sell to institutional public market investors looking for immediate ARR growth.

Founders Wing sees something different worth talking about: this IPO is a defensive play. As compute costs rise and private capital markets get more selective, going public is the only way to lock in the massive, sustained funding needed to compete with OpenAI and Google.

It's not a victory lap; it's a resource grab in a race where the burn rate is measured in billions.

If Anthropic goes public, they will have to disclose their actual revenue, compute expenditures, and customer concentration. We will finally see the real unit economics of safety-first foundation models.

Will safety-centric positioning survive public market scrutiny? Or will the demands of retail and institutional investors force Anthropic to prioritize product speed over guardrails?`
};

(async () => {
  const wsEndpoint = process.argv[2];
  if (!wsEndpoint) {
    console.error("Usage: node edit_scheduled_posts.cjs <wsEndpoint>");
    process.exit(1);
  }

  try {
    console.log(`Connecting to browser via: ${wsEndpoint}`);
    const browser = await puppeteer.connect({ browserWSEndpoint: wsEndpoint });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com'));
    
    if (!page) {
      console.error("LinkedIn page not found!");
      process.exit(1);
    }
    await page.bringToFront();

    // Set taller viewport height so buttons at the bottom of modals are always visible
    console.log("Setting browser viewport size to 1280x1200...");
    await page.setViewport({ width: 1280, height: 1200 });

    // Mapping post date/times to caption keys
    const targets = [
      { key: 'infographic', label: 'Sun June 7, 2026 at 11:30 PM' },
      { key: 'creditMemos', label: 'Mon June 8, 2026 at 2:30 AM' },
      { key: 'anthropicIpo', label: 'Mon June 8, 2026 at 5:30 AM' },
      { key: 'carousel', label: 'Wed June 10, 2026 at 8:30 PM' }
    ];

    for (const target of targets) {
      console.log(`\n--- Starting Flow for Post: ${target.key} (${target.label}) ---`);
      
      // 0. Ensure we are on clean feed homepage to start fresh
      console.log("Navigating to LinkedIn feed...");
      await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });
      await new Promise(r => setTimeout(r, 5000));

      // Handle any active composer modal overlay by dismissing it
      const dismissOverlay = await page.evaluate(() => {
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
        
        // Find close/dismiss button
        function findDismissBtn(root) {
          if (!root) return null;
          const btn = Array.from(root.querySelectorAll('button')).find(
            b => (b.ariaLabel && b.ariaLabel.includes('Dismiss')) || 
                 (b.innerText && b.innerText.includes('Dismiss')) ||
                 (b.ariaLabel && b.ariaLabel.toLowerCase() === 'close') ||
                 (b.className && b.className.includes('close-button'))
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

        const hasModal = !!findEl(document.body, '.ql-editor, [contenteditable="true"]');
        if (!hasModal) return "no-modal";
        const btn = findDismissBtn(document.body);
        if (btn) {
          btn.click();
          return "dismiss-clicked";
        }
        return "modal-found-no-dismiss-btn";
      });
      console.log("Dismiss modal check:", dismissOverlay);
      if (dismissOverlay === "dismiss-clicked") {
        await new Promise(r => setTimeout(r, 2000));
        // Check if there is a confirmation modal to discard
        const discardConfirm = await clickNativelyShadow(page, (root) => {
          return Array.from(root.querySelectorAll('button')).find(
            b => b.innerText && b.innerText.trim() === 'Discard'
          );
        });
        if (discardConfirm) {
          console.log("Discarded unsaved draft changes.");
          await new Promise(r => setTimeout(r, 2000));
        }
      }

      // 1. Click "Start a post"
      console.log("Clicking 'Start a post'...");
      const clickStartPost = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('*')).find(
          el => (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || el.getAttribute('aria-label') === 'Start a post') &&
                el.innerText && el.innerText.trim().includes('Start a post')
        );
      });
      if (!clickStartPost) throw new Error("Could not find 'Start a post' button");
      
      // Wait for text editor to ensure composer modal is fully loaded
      console.log("Waiting for text editor to load...");
      const editorSelector = '.ql-editor, [contenteditable="true"]';
      await waitForSelectorShadow(page, editorSelector, 15000);
      await new Promise(r => setTimeout(r, 2000));

      // 2. Click "Schedule post" clock icon
      console.log("Clicking Schedule post clock icon...");
      const clickedScheduleIcon = await clickNativelyShadow(page, (root) => {
        const buttons = Array.from(root.querySelectorAll('button'));
        const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
        if (postBtn && postBtn.previousElementSibling) {
          return postBtn.previousElementSibling;
        }
        return buttons.find(b => b.ariaLabel && b.ariaLabel.includes('Schedule'));
      });
      if (!clickedScheduleIcon) throw new Error("Could not find Schedule post clock icon");
      await new Promise(r => setTimeout(r, 2000));

      // 3. Click "View all scheduled posts"
      console.log("Clicking 'View all scheduled posts'...");
      const clickedViewAll = await clickNativelyShadow(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim().includes('View all scheduled posts')
        );
      });
      if (!clickedViewAll) throw new Error("Could not find 'View all scheduled posts' button");
      await new Promise(r => setTimeout(r, 3000));

      // 4. Find the Actions button for the specific target
      console.log(`Locating actions button for: ${target.label}`);
      const actionsButtonHandle = await page.evaluateHandle((lbl) => {
        function findInShadow(root) {
          if (!root) return null;
          const buttons = Array.from(root.querySelectorAll('button'));
          const found = buttons.find(b => b.ariaLabel && b.ariaLabel.includes('Actions menu for scheduled post') && b.ariaLabel.includes(lbl));
          if (found) return found;
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
          let node;
          while (node = walker.nextNode()) {
            if (node.shadowRoot) {
              const res = findInShadow(node.shadowRoot);
              if (res) return res;
            }
          }
          return null;
        }
        return findInShadow(document.body);
      }, target.label);

      const actionsBtn = actionsButtonHandle.asElement();
      if (!actionsBtn) {
        throw new Error(`Could not find actions button for scheduled post: ${target.label}`);
      }
      
      console.log("Clicking actions button...");
      await page.evaluate(e => e.focus(), actionsBtn);
      await actionsBtn.click();
      await page.evaluate(e => e.click(), actionsBtn).catch(() => {});
      await actionsBtn.dispose();
      await new Promise(r => setTimeout(r, 2500));

      // 5. Click "Edit post" button in menu (broad tag matching)
      console.log("Clicking 'Edit post' button...");
      const clickEditSuccess = await clickNativelyShadow(page, (root) => {
        const els = Array.from(root.querySelectorAll('button, div, li, span, [role="button"]'));
        return els.find(b => {
          const txt = b.innerText ? b.innerText.trim() : '';
          const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0;
          return txt === 'Edit post' && isVisible;
        });
      });

      if (!clickEditSuccess) {
        throw new Error("Could not find or click 'Edit post' button in the Actions menu");
      }
      await new Promise(r => setTimeout(r, 3000));

      // 6. Wait for the editor to load
      console.log("Waiting for editor `.ql-editor` to load...");
      await waitForSelectorShadow(page, editorSelector, 15000);
      const editorEl = await getElementShadow(page, editorSelector);
      
      // 7. Update the caption text
      console.log("Replacing caption text...");
      await editorEl.focus();
      
      // Clear contents
      await page.evaluate((el) => {
        if (el) el.innerHTML = '<p><br></p>';
      }, editorEl);
      await editorEl.dispose();

      // Type new caption
      await page.keyboard.type(captions[target.key]);
      await new Promise(r => setTimeout(r, 2500));

      // Take a screenshot of the edited post
      await page.screenshot({ path: `/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/edit_${target.key}_filled.png` });
      console.log(`Saved screenshot to edit_${target.key}_filled.png`);

      // 8. Click "Schedule" button to save changes (broad tag matching)
      console.log("Clicking 'Schedule' button to save changes...");
      const clickScheduleSuccess = await clickNativelyShadow(page, (root) => {
        const els = Array.from(root.querySelectorAll('button, div, span, [role="button"]'));
        return els.find(b => {
          const txt = b.innerText ? b.innerText.trim() : '';
          const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0;
          return (txt === 'Schedule' || b.getAttribute('aria-label') === 'Schedule') && isVisible;
        });
      });

      if (!clickScheduleSuccess) {
        throw new Error("Could not find or click 'Schedule' button to save");
      }

      console.log("Post save submitted. Waiting 6s for modal to close...");
      await new Promise(r => setTimeout(r, 6000));
    }

    console.log("\nAll posts have been edited successfully!");
    process.exit(0);

  } catch (err) {
    console.error("Error editing scheduled posts:", err);
    process.exit(1);
  }
})();
