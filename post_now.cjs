#!/usr/bin/env node
/**
 * Post ONE text post to LinkedIn right now (not schedule).
 * Requires: agent-browser --session linkedin_bot --headed open https://www.linkedin.com/feed/
 * Usage: node post_now.cjs [schedule_one_post.json]
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

async function getElementShadow(page, selector) {
  const handle = await page.evaluateHandle((sel) => {
    function findEl(root) {
      if (!root) return null;
      const els = root.querySelectorAll(sel);
      for (const el of els) {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        if (rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none') {
          return el;
        }
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while ((node = walker.nextNode())) {
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

async function clickNativelyShadow(page, finderFn) {
  await page.evaluate(() => {
    document.querySelectorAll('#interop-outlet, .msg-overlay-container, [class*="msg-overlay"]').forEach((el) => {
      el.style.pointerEvents = 'none';
      el.style.display = 'none';
    });
  });

  const handle = await page.evaluateHandle((finder) => {
    const fn = new Function('return ' + finder)();
    function findInShadow(root) {
      if (!root) return null;
      const res = fn(root);
      if (res) return res;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while ((node = walker.nextNode())) {
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
  if (!el) {
    await handle.dispose();
    return false;
  }
  await page.evaluate((e) => {
    e.scrollIntoView({ block: 'center', inline: 'center' });
    e.click();
  }, el);
  await el.dispose();
  await handle.dispose();
  return true;
}

async function fillCaption(page, caption) {
  const editorSelector = '.ql-editor, div[role="textbox"][contenteditable="true"], .share-creation-state__text-editor div[contenteditable="true"]';
  const editor = await getElementShadow(page, editorSelector);
  if (!editor) return false;
  await editor.focus();
  await page.evaluate((el) => {
    el.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
  }, editor);
  await new Promise((r) => setTimeout(r, 300));
  try {
    const client = await page.createCDPSession();
    await client.send('Input.insertText', { text: caption });
  } catch (_) {
    const paragraphs = caption.split('\n');
    for (let i = 0; i < paragraphs.length; i++) {
      if (i > 0) await page.keyboard.press('Enter');
      if (paragraphs[i]) await page.keyboard.type(paragraphs[i], { delay: 5 });
    }
  }
  await editor.dispose();
  return true;
}

(async () => {
  const schedulePath = path.resolve(__dirname, process.argv[2] || 'schedule_one_post.json');
  const data = JSON.parse(fs.readFileSync(schedulePath, 'utf8'));
  const post = data.posts[0];
  if (!post || !post.caption) throw new Error('No caption in schedule file');

  fs.mkdirSync(path.join(__dirname, 'slack_downloads'), { recursive: true });

  const tmpDir = os.tmpdir();
  const dirs = fs.readdirSync(tmpDir).filter(
    (name) => name.startsWith('agent-browser-chrome-') || name.startsWith('agent-browser-profile-')
  );
  if (!dirs.length) throw new Error('No agent-browser profile found. Launch agent-browser --headed first.');
  const latestDir = dirs
    .map((name) => {
      const fullPath = path.join(tmpDir, name);
      return { path: fullPath, mtime: fs.statSync(fullPath).mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime)[0].path;
  const port = fs.readFileSync(path.join(latestDir, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
  console.log('Connecting to port', port);

  const browser = await puppeteer.connect({
    browserURL: `http://127.0.0.1:${port}`,
    protocolTimeout: 120000,
  });
  const pages = await browser.pages();
  let page = pages.find((p) => p.url().includes('linkedin.com')) || pages[0];
  await page.bringToFront();
  await page.setViewport({ width: 1280, height: 1200 });

  console.log('Opening feed...');
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise((r) => setTimeout(r, 4000));

  console.log("Clicking Start a post...");
  let started = await clickNativelyShadow(page, (root) => {
    const els = [...root.querySelectorAll('a,button,[role="button"]')];
    return els.find((el) => {
      const t = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).toLowerCase();
      return t.includes('start a post');
    });
  });
  if (!started) throw new Error("Could not click Start a post");
  await new Promise((r) => setTimeout(r, 3000));

  console.log('Filling caption...');
  const filled = await fillCaption(page, post.caption);
  if (!filled) throw new Error('Could not fill caption');
  await new Promise((r) => setTimeout(r, 1500));

  await page.screenshot({ path: path.join(__dirname, 'slack_downloads', 'post_now_draft.png') });

  console.log('Clicking Post...');
  let posted = await clickNativelyShadow(page, (root) => {
    const buttons = [...root.querySelectorAll('button')];
    return buttons.find((b) => {
      const t = (b.innerText || '').trim();
      const label = (b.getAttribute('aria-label') || '').trim();
      const disabled = b.disabled || b.getAttribute('disabled') !== null || (b.getAttribute('aria-disabled') === 'true');
      if (disabled) return false;
      return t === 'Post' || label === 'Post' || /^Post$/i.test(label);
    });
  });
  if (!posted) {
    // Sometimes primary CTA is "Post" inside share-box footer
    posted = await clickNativelyShadow(page, (root) => {
      const buttons = [...root.querySelectorAll('button.share-actions__primary-action, button[class*="share-actions"], button')];
      return buttons.find((b) => {
        const t = (b.innerText || '').trim();
        const disabled = b.disabled || b.getAttribute('aria-disabled') === 'true';
        return !disabled && t === 'Post';
      });
    });
  }
  if (!posted) throw new Error('Could not click Post button');

  await new Promise((r) => setTimeout(r, 5000));
  await page.screenshot({ path: path.join(__dirname, 'slack_downloads', 'post_now_done.png') });
  console.log('✓ Post submitted. Check your LinkedIn feed / recent activity.');
  process.exit(0);
})().catch((err) => {
  console.error('FAILED:', err.message);
  process.exit(1);
});
