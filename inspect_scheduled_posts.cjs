const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

(async () => {
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
    
    // Check if scheduled posts modal is already open
    const isModalOpen = await page.evaluate(() => {
      function findInShadow(root, sel) {
        if (!root) return null;
        const el = root.querySelector(sel);
        if (el) return el;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findInShadow(node.shadowRoot, sel);
            if (found) return found;
          }
        }
        return null;
      }
      const heading = findInShadow(document.body, 'h2');
      return !!heading && heading.innerText.includes('Scheduled posts');
    });
    
    if (!isModalOpen) {
      console.log("Scheduled posts modal not open. Opening it...");
      await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 15000 });
      await new Promise(r => setTimeout(r, 4000));
      
      // Click start post using shadow-dom search
      await page.evaluate(() => {
        function findEl(root) {
          if (!root) return null;
          const el = Array.from(root.querySelectorAll('*')).find(
            e => (e.tagName === 'BUTTON' || e.getAttribute('role') === 'button' || e.getAttribute('aria-label') === 'Start a post') &&
                  e.innerText && e.innerText.trim().includes('Start a post')
          );
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
        const btn = findEl(document.body);
        if (btn) btn.click();
      });
      await new Promise(r => setTimeout(r, 3000));
      
      // Click schedule icon
      await page.evaluate(() => {
        function findScheduleIcon(root) {
          if (!root) return null;
          const buttons = Array.from(root.querySelectorAll('button'));
          const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
          if (postBtn && postBtn.previousElementSibling) {
            return postBtn.previousElementSibling;
          }
          const schedBtn = buttons.find(b => b.getAttribute('aria-label')?.includes('Schedule'));
          if (schedBtn) return schedBtn;
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
          let node;
          while (node = walker.nextNode()) {
            if (node.shadowRoot) {
              const found = findScheduleIcon(node.shadowRoot);
              if (found) return found;
            }
          }
          return null;
        }
        const btn = findScheduleIcon(document.body);
        if (btn) btn.click();
      });
      await new Promise(r => setTimeout(r, 3000));
      
      // Click view all scheduled posts
      await page.evaluate(() => {
        function findViewAll(root) {
          if (!root) return null;
          const el = Array.from(root.querySelectorAll('a, button, span')).find(
            e => e.innerText && e.innerText.includes('View all scheduled posts')
          );
          if (el) return el;
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
          let node;
          while (node = walker.nextNode()) {
            if (node.shadowRoot) {
              const found = findViewAll(node.shadowRoot);
              if (found) return found;
            }
          }
          return null;
        }
        const btn = findViewAll(document.body);
        if (btn) btn.click();
      });
      await new Promise(r => setTimeout(r, 4000));
    }
    
    // Scroll the modal to load all posts
    console.log("Scrolling scheduled posts modal to load more content...");
    await page.evaluate(async () => {
      function findScrollable(root) {
        if (!root) return null;
        const heading = Array.from(root.querySelectorAll('h2, span, p')).find(el => el.innerText && el.innerText.includes('Scheduled posts'));
        if (heading) {
          let p = heading.parentNode;
          while (p && p !== document.body) {
            if ((p.classList && p.classList.contains('artdeco-modal')) || p.getAttribute('role') === 'dialog') {
              const elements = p.querySelectorAll('*');
              for (const el of elements) {
                if (el.scrollHeight > el.clientHeight) {
                  const style = window.getComputedStyle(el);
                  if (style.overflowY === 'auto' || style.overflowY === 'scroll' || el.className.includes('content') || el.className.includes('list')) {
                    return el;
                  }
                }
              }
              const content = p.querySelector('.artdeco-modal__content') || p;
              return content;
            }
            p = p.parentNode || p.host;
          }
        }
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findScrollable(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      const scrollable = findScrollable(document.body);
      if (scrollable) {
        for (let i = 0; i < 5; i++) {
          scrollable.scrollTop = scrollable.scrollHeight;
          await new Promise(r => setTimeout(r, 1000));
        }
      } else {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 2000));
      }
    });

    console.log("Saving screenshot of scrolled modal...");
    await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/scheduled_modal_scrolled.png' });

    // Click 'Show more Scheduled posts' if present
    const clickedShowMore = await page.evaluate(() => {
      function findShowMore(root) {
        if (!root) return null;
        const el = Array.from(root.querySelectorAll('button, span, a')).find(
          e => e.innerText && e.innerText.trim() === 'Show more Scheduled posts'
        );
        if (el) return el;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            const found = findShowMore(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      const btn = findShowMore(document.body);
      if (btn) {
        btn.click();
        return true;
      }
      return false;
    });

    if (clickedShowMore) {
      console.log("Clicked 'Show more Scheduled posts' button, waiting 3s for loading...");
      await new Promise(r => setTimeout(r, 3000));
      console.log("Saving screenshot after clicking show more...");
      await page.screenshot({ path: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/scheduled_modal_scrolled_more.png' });
    }

    // Now extract scheduled posts details
    const scheduledDetails = await page.evaluate(() => {
      function findPreviews(root) {
        if (!root) return [];
        let found = Array.from(root.querySelectorAll('button, div')).filter(
          el => el.getAttribute('aria-label')?.includes('Preview of the scheduled post') ||
                (el.innerText && el.innerText.includes('scheduled post that will be published'))
        ).map(el => {
          return {
            label: el.getAttribute('aria-label') || el.innerText,
            textContext: el.innerText ? el.innerText.trim() : ''
          };
        });
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while (node = walker.nextNode()) {
          if (node.shadowRoot) {
            found = found.concat(findPreviews(node.shadowRoot));
          }
        }
        return found;
      }
      // De-duplicate by label
      const all = findPreviews(document.body);
      const unique = [];
      const seen = new Set();
      for (const item of all) {
        if (!seen.has(item.label)) {
          seen.add(item.label);
          unique.push(item);
        }
      }
      return unique;
    });
    
    console.log("SCHEDULED_POSTS_DATA:" + JSON.stringify(scheduledDetails, null, 2));
    process.exit(0);
  } catch (err) {
    console.error("Error inspecting:", err);
    process.exit(1);
  }
})();
