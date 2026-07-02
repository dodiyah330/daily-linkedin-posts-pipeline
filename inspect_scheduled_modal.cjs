const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

(async () => {
  try {
    const tmpDir = os.tmpdir();
    const dirs = fs.readdirSync(tmpDir).filter(name => name.startsWith('agent-browser-chrome-'));
    if (dirs.length === 0) throw new Error('No chrome dirs');
    const latestDir = dirs.map(name => {
      const fullPath = path.join(tmpDir, name);
      return { path: fullPath, mtime: fs.statSync(fullPath).mtimeMs };
    }).sort((a, b) => b.mtime - a.mtime)[0].path;
    const portFile = path.join(latestDir, 'DevToolsActivePort');
    const content = fs.readFileSync(portFile, 'utf8');
    const port = content.split('\n')[0].trim();
    const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com'));
    
    console.log("Bringing page to front...");
    await page.bringToFront();

    async function clickNativelyShadow(finderFn) {
      // Remove overlays
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
          return `${e.tagName} class="${e.className}" text="${e.innerText ? e.innerText.trim().substring(0, 30) : ''}"`;
        }, el);
        console.log(`clickNativelyShadow: Found element: <${tagAndClass}>. Clicking...`);
        await page.evaluate(e => {
          e.focus();
          e.scrollIntoView({ block: 'center', inline: 'center' });
          const rect = e.getBoundingClientRect();
          const x = rect.left + rect.width / 2;
          const y = rect.top + rect.height / 2;
          const opts = { bubbles: true, cancelable: true, view: window, screenX: x, screenY: y, clientX: x, clientY: y };
          e.dispatchEvent(new PointerEvent('pointerdown', opts));
          e.dispatchEvent(new MouseEvent('mousedown', opts));
          e.dispatchEvent(new PointerEvent('pointerup', opts));
          e.dispatchEvent(new MouseEvent('mouseup', opts));
          e.dispatchEvent(new MouseEvent('click', opts));
        }, el);
        await el.dispose();
        return true;
      }
      return false;
    }

    console.log("Reloading page to clear all modals...");
    await page.reload({ waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 5000));

    // Open composer
    console.log("Opening composer...");
    await clickNativelyShadow((root) => {
      return Array.from(root.querySelectorAll('button, [role="button"], span')).find(
        el => (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || el.getAttribute('aria-label') === 'Start a post') &&
              el.innerText && el.innerText.trim().includes('Start a post')
      );
    });

    console.log("Waiting for composer modal to be visible...");
    let composerVisible = false;
    for (let i = 0; i < 10; i++) {
      composerVisible = await page.evaluate(() => {
        return !!document.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
      });
      if (composerVisible) break;
      await new Promise(r => setTimeout(r, 1000));
    }
    if (!composerVisible) throw new Error("Composer modal did not appear");

    console.log("Waiting 3s for composer toolbar to render...");
    await new Promise(r => setTimeout(r, 3000));

    // Click Schedule Settings (clock icon)
    console.log("Opening Schedule Settings...");
    await clickNativelyShadow((root) => {
      const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
      const container = modal || root;
      const buttons = Array.from(container.querySelectorAll('button'));
      const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
      if (postBtn && postBtn.previousElementSibling) {
        return postBtn.previousElementSibling;
      }
      return buttons.find(b => b.ariaLabel && b.ariaLabel.includes('Schedule'));
    });

    console.log("Waiting 3s for schedule dialog to render...");
    await new Promise(r => setTimeout(r, 3000));

    // Click View all scheduled posts
    console.log("Clicking View all scheduled posts...");
    await clickNativelyShadow((root) => {
      return Array.from(root.querySelectorAll('button, a')).find(el => {
        const txt = el.innerText ? el.innerText.trim() : '';
        return txt.toLowerCase().includes('view all scheduled posts');
      });
    });

    console.log("Waiting 6s for Scheduled posts modal list to load...");
    await new Promise(r => setTimeout(r, 6000));

    // Click the first Actions button
    console.log("Clicking the first actions button...");
    await clickNativelyShadow((root) => {
      const btns = Array.from(root.querySelectorAll('button'));
      return btns.find(b => b.ariaLabel && b.ariaLabel.includes('Actions menu for scheduled post'));
    });

    console.log("Waiting 3s for actions menu to appear...");
    await new Promise(r => setTimeout(r, 3000));

    // Click Delete post
    console.log("Clicking Delete post button...");
    await clickNativelyShadow((root) => {
      const els = Array.from(root.querySelectorAll('button, div, span, [role="button"]'));
      return els.find(b => b.innerText && b.innerText.trim() === 'Delete post');
    });

    console.log("Waiting 3s for delete confirmation dialog...");
    await new Promise(r => setTimeout(r, 3000));

    // Take screenshot of confirmation dialog
    console.log("Taking screenshot of delete confirmation dialog...");
    await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/inspect_delete_confirm.png' });

    console.log("Inspecting elements in delete confirmation dialog...");
    const confirmElements = await page.evaluate(() => {
      function findElements(root) {
        let found = [];
        const btns = root.querySelectorAll('button, [role="button"], a, li, span');
        for (const btn of btns) {
          const txt = btn.innerText ? btn.innerText.trim() : '';
          const label = btn.ariaLabel || btn.getAttribute('aria-label') || '';
          if (txt.includes('Delete') || txt.includes('Cancel') || txt.includes('Discard') || txt.includes('Confirm')) {
            found.push({
              tagName: btn.tagName,
              className: btn.className,
              text: txt,
              ariaLabel: label
            });
          }
        }
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            found = found.concat(findElements(node.shadowRoot));
          }
        }
        return found;
      }
      return findElements(document.body);
    });

    console.log("Found controls in delete confirmation dialog:", JSON.stringify(confirmElements, null, 2));
    process.exit(0);
  } catch (err) {
    console.error("Error:", err);
    process.exit(1);
  }
})();
