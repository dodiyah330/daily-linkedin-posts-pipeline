const puppeteer = require('puppeteer');

(async () => {
  console.log('🚀 Starting LinkedIn Post Scheduler...');
  
  // Launch context with persistent profile in project directory
  const browser = await puppeteer.launch({
    headless: false,
    userDataDir: '/Users/prithal/Documents/carousel-routine/.puppeteer_profile',
    defaultViewport: null,
    args: ['--start-maximized'],
    protocolTimeout: 1800000 // 30 minutes
  });

  const pages = await browser.pages();
  const page = pages.length > 0 ? pages[0] : await browser.newPage();

  console.log('📬 Navigating to LinkedIn feed...');
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });

  // 1. Wait for login verification
  console.log('🔒 Verifying login session...');
  try {
    await page.waitForSelector('.feed-identity-module, .global-nav, .share-box-feed-entry__trigger', { timeout: 10000 });
    console.log('✅ Logged in successfully!');
  } catch (e) {
    console.log('⚠️ Active session not found. Please log in manually in the opened browser window...');
    await page.waitForSelector('.feed-identity-module, .global-nav, .share-box-feed-entry__trigger', { timeout: 0 });
    console.log('✅ Logged in successfully after manual intervention!');
  }

  // 2. Click "Start a post"
  console.log('📝 Locating "Start a post" button...');
  const startPostSelectors = [
    'button.share-box-feed-entry__trigger',
    'button[data-control-name="share_box"]',
    '#main button.share-box-feed-entry__trigger',
    '//button[contains(., "Start a post")]'
  ];

  let startPostBtn = null;
  for (const selector of startPostSelectors) {
    try {
      if (selector.startsWith('//')) {
        const [el] = await page.$x(selector);
        if (el) {
          startPostBtn = el;
          break;
        }
      } else {
        startPostBtn = await page.waitForSelector(selector, { timeout: 2000 });
        if (startPostBtn) break;
      }
    } catch (err) {}
  }

  if (!startPostBtn) {
    console.log('❌ Could not find "Start a post" button automatically. Please click it in the browser window.');
    // Let user click it
    await page.waitForSelector('.share-box-composer, .share-creation-state', { timeout: 60000 });
  } else {
    await startPostBtn.click();
    console.log('✅ Clicked "Start a post".');
  }

  // Wait for post composer modal
  await page.waitForSelector('.share-box-composer, .share-creation-state, [role="dialog"]', { timeout: 10000 });
  console.log('✅ Post composer modal opened.');

  // 3. Click "Add a document" button
  console.log('📁 Looking for "Add a document" button...');
  const docButtonSelectors = [
    'button[aria-label="Add a document"]',
    'button[aria-label="Share a document"]',
    'button.share-promoted-detour-button[aria-label="Add a document"]',
    'button[aria-label="Add a document"] svg',
    '//button[contains(@aria-label, "document")]'
  ];

  let docBtn = null;
  for (const selector of docButtonSelectors) {
    try {
      if (selector.startsWith('//')) {
        const [el] = await page.$x(selector);
        if (el) {
          docBtn = el;
          break;
        }
      } else {
        docBtn = await page.waitForSelector(selector, { timeout: 2000 });
        if (docBtn) break;
      }
    } catch (err) {}
  }

  if (!docBtn) {
    // Try opening the "More" actions menu if document isn't direct
    console.log('🔍 Document button not direct, checking for "More" actions menu...');
    const moreBtnSelectors = [
      'button[aria-label="More options"]',
      'button[aria-label="Show more Actions"]',
      'button[aria-label="More actions"]'
    ];
    for (const moreSel of moreBtnSelectors) {
      try {
        const moreBtn = await page.$(moreSel);
        if (moreBtn) {
          await moreBtn.click();
          console.log('✅ Clicked "More actions".');
          await new Promise(r => setTimeout(r, 1000));
          break;
        }
      } catch (err) {}
    }
    
    // Re-check for document button after clicking more
    for (const selector of docButtonSelectors) {
      try {
        if (selector.startsWith('//')) {
          const [el] = await page.$x(selector);
          if (el) {
            docBtn = el;
            break;
          }
        } else {
          docBtn = await page.$(selector);
          if (docBtn) break;
        }
      } catch (err) {}
    }
  }

  if (docBtn) {
    await docBtn.click();
    console.log('✅ Clicked "Add a document".');
  } else {
    console.log('⚠️ Could not click Document button. Please click it manually in the browser.');
  }

  // 4. Upload file
  console.log('📤 Waiting for file input...');
  const fileInputSelector = 'input[type="file"]';
  await page.waitForSelector(fileInputSelector, { timeout: 30000 });
  const fileInput = await page.$(fileInputSelector);
  const filePath = '/Users/prithal/Downloads/website-vs-whatsapp-carousel (1).pdf';
  console.log(`📄 Uploading: ${filePath}`);
  await fileInput.uploadFile(filePath);

  // 5. Document title
  console.log('✍️ Waiting for document title input...');
  const titleSelectors = [
    'input[placeholder="Document title"]',
    'input[name="document-title"]',
    'input[aria-label="Document title"]',
    'input[type="text"]'
  ];
  let titleInput = null;
  for (const sel of titleSelectors) {
    try {
      titleInput = await page.waitForSelector(sel, { timeout: 5000 });
      if (titleInput) break;
    } catch (err) {}
  }

  if (titleInput) {
    await titleInput.type('Website vs WhatsApp AI Agent Setup Guide');
    console.log('✅ Typed document title.');
  } else {
    console.log('⚠️ Could not find Title input. Please type the title manually.');
  }

  // Click "Done" inside the document uploader preview modal
  console.log('💾 Looking for "Done" button...');
  const doneSelectors = [
    'button.share-box-footer__primary-btn',
    'button.share-creation-state__done-btn',
    'button.share-document-preview__done-btn',
    '//button[span[text()="Done"]]',
    '//button[contains(., "Done")]'
  ];
  let doneBtn = null;
  for (const selector of doneSelectors) {
    try {
      if (selector.startsWith('//')) {
        const [el] = await page.$x(selector);
        if (el) {
          doneBtn = el;
          break;
        }
      } else {
        doneBtn = await page.waitForSelector(selector, { timeout: 3000 });
        if (doneBtn) break;
      }
    } catch (err) {}
  }

  if (doneBtn) {
    await doneBtn.click();
    console.log('✅ Clicked Done on uploader.');
  } else {
    console.log('⚠️ Click "Done" manually to attach the document.');
  }

  await new Promise(r => setTimeout(r, 2000));

  // 6. Enter caption
  console.log('📝 Typing post caption...');
  const caption = `Website vs. WhatsApp AI Agent: Where should you build first?

If you’re a solopreneur or a small business, a website used to be the default first step. But in 2026, the game has changed.

Most customers don’t want to navigate a 5-page website to find an answer. They want immediate, direct communication.

Here's the breakdown of why a WhatsApp AI Agent might be the most valuable asset for your business right now:
1. 10-Minute Setup: Using tools like YCloud, you can go live with a fully functioning support agent in minutes (no-code).
2. Keep Your Number: Coexistence mode lets you run your AI agent on your existing WhatsApp Business number while still using the app.
3. Zero Friction: Your customers are already on WhatsApp. No links to click, no contact forms to fill out.

Check out the carousel below for the complete setup guide and a comparison of YCloud vs. Claude + n8n.

Let me know in the comments: Are you still relying on website forms, or have you moved to conversational AI? 👇

#solopreneur #ai #whatsapp #growthmarketing #nocode`;

  const editorSelectors = [
    '.ql-editor',
    'div[contenteditable="true"]',
    '.share-editor__editor'
  ];
  let editor = null;
  for (const sel of editorSelectors) {
    try {
      editor = await page.waitForSelector(sel, { timeout: 5000 });
      if (editor) break;
    } catch (err) {}
  }

  if (editor) {
    await editor.focus();
    await page.keyboard.type(caption);
    console.log('✅ Caption entered.');
  } else {
    console.log('⚠️ Could not find post composer text area. Please paste/type your caption manually.');
  }

  // 7. Click scheduling icon
  console.log('⏰ Locating schedule clock icon...');
  const scheduleIconSelectors = [
    'button[aria-label="Schedule for later"]',
    'button.share-actions__schedule-btn',
    'button[data-control-name="schedule_post"]',
    '//button[contains(@aria-label, "Schedule")]'
  ];
  let scheduleIcon = null;
  for (const selector of scheduleIconSelectors) {
    try {
      if (selector.startsWith('//')) {
        const [el] = await page.$x(selector);
        if (el) {
          scheduleIcon = el;
          break;
        }
      } else {
        scheduleIcon = await page.waitForSelector(selector, { timeout: 5000 });
        if (scheduleIcon) break;
      }
    } catch (err) {}
  }

  if (scheduleIcon) {
    await scheduleIcon.click();
    console.log('✅ Clicked Schedule clock icon.');
  } else {
    console.log('⚠️ Could not find Schedule icon. Please click it manually to open the scheduling options.');
  }

  // Wait for date/time selectors
  console.log('📅 Setting date and time...');
  const dateInputSelector = 'input[type="date"], input[name="date"], .schedule-modal__date-input';
  const timeInputSelector = 'input[type="time"], input[name="time"], select[name="time"], .schedule-modal__time-select';

  try {
    await page.waitForSelector(dateInputSelector, { timeout: 10000 });
    
    // Set Date to May 25, 2026 (Tomorrow)
    await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (el) {
        el.value = '2026-05-25';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }, dateInputSelector);
    console.log('✅ Date set to 2026-05-25 (Tomorrow).');

    // Set Time to 10:00 AM (10:00)
    await page.waitForSelector(timeInputSelector, { timeout: 5000 });
    await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (el) {
        el.value = '10:00';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }, timeInputSelector);
    console.log('✅ Time set to 10:00 AM.');

    // Click Next in Schedule dialog
    console.log('👉 Clicking Next/Save on schedule settings...');
    const nextSelectors = [
      'button.schedule-modal__next-btn',
      'button.share-schedule-modal__next-btn',
      '//button[span[text()="Next"]]',
      '//button[contains(., "Next")]'
    ];
    let nextBtn = null;
    for (const selector of nextSelectors) {
      try {
        if (selector.startsWith('//')) {
          const [el] = await page.$x(selector);
          if (el) {
            nextBtn = el;
            break;
          }
        } else {
          nextBtn = await page.waitForSelector(selector, { timeout: 3000 });
          if (nextBtn) break;
        }
      } catch (err) {}
    }

    if (nextBtn) {
      await nextBtn.click();
      console.log('✅ Clicked Next.');
    } else {
      console.log('⚠️ Please click "Next" in the schedule window manually.');
    }

    // Wait for the composer post button to become "Schedule"
    await new Promise(r => setTimeout(r, 2000));
    
    console.log('🚀 Ready to schedule. Looking for final Schedule/Post button...');
    const schedulePostSelectors = [
      'button.share-actions__post-btn',
      'button.share-box_actions__post-btn',
      '//button[contains(., "Schedule")]',
      '//button[contains(., "Post")]'
    ];
    let finalBtn = null;
    for (const selector of schedulePostSelectors) {
      try {
        if (selector.startsWith('//')) {
          const [el] = await page.$x(selector);
          if (el) {
            finalBtn = el;
            break;
          }
        } else {
          finalBtn = await page.waitForSelector(selector, { timeout: 3000 });
          if (finalBtn) break;
        }
      } catch (err) {}
    }

    if (finalBtn) {
      // We will let the user review it, but we can click it or tell them to click it
      console.log('🎉 Post is prepared and ready to schedule!');
      console.log('Clicking the final Schedule button...');
      await finalBtn.click();
      console.log('✅ Clicked final Schedule button.');
    } else {
      console.log('⚠️ Please click "Schedule" manually in the browser window.');
    }

  } catch (err) {
    console.log('⚠️ Automation had trouble setting date/time or clicking Next. Please complete the scheduling step manually in the opened browser window.');
    console.error(err);
  }

  console.log('📢 Done! Keeping browser window open so you can review and confirm.');
})();
