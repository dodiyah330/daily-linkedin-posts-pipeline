const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const DATE_STR = new Date().toISOString().slice(0, 10);
const OUT_DIR = path.join(__dirname, 'output', DATE_STR, 'carousel-branded');
fs.mkdirSync(OUT_DIR, { recursive: true });

const CREAM = '#F5EFE8';
const CORAL = '#E63946';
const INK = '#1A1A1A';
const MUTE = '#5A5148';

// slide content: the Fable export-control carousel (Curiosity Gap hook)
const slides = [
  { type: 'hook', label: 'AI + ACCESS',
    title: ['The day an AI', 'vanished in', '90 minutes'], em: 'vanished',
    sub: 'What one government memo just revealed about the tools you build on.' },
  { type: 'body', n: '01', label: 'THE LAUNCH',
    head: ['A lab shipped its most', 'powerful model on a', 'Tuesday'], em: 'powerful',
    body: 'Three days later, a single government directive ordered it cut off from every foreign user. The model went dark worldwide in under 90 minutes.' },
  { type: 'body', n: '02', label: 'THE TRIGGER',
    head: ['It was not a', 'scandal'], em: 'scandal',
    body: 'Engineers found one narrow way to slip past its safety checks. That was enough for the tool to be pulled from millions of people who had built nothing wrong.' },
  { type: 'body', n: '03', label: 'THE LOCKOUT',
    head: ['Not priced out.', 'Locked out'], em: 'Locked',
    body: 'For almost two weeks, anyone outside the approved list lost access. The line was no longer what you could pay. It was which passport you held.' },
  { type: 'body', n: '04', label: 'THE REVERSAL',
    head: ['Softened, but the', 'point landed'], em: 'point',
    body: 'Political pressure later eased the restrictions. But it was already clear: the best AI can be switched off for whole countries with one memo.' },
  { type: 'body', n: '05', label: 'THE LESSON',
    head: ['Access is now a', 'political', 'decision'], em: 'political',
    body: 'The takeaway is not to fear AI. It is to notice that if your work depends on one hosted model, part of your business now lives outside your control.' },
  { type: 'cta',
    head: ['Where AI is', 'reshaping work', 'and access'], em: 'work',
    sub: 'Follow me.' },
];

function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function headHTML(lines, em) {
  return lines.map(l => {
    if (em && l.includes(em)) {
      const parts = l.split(em);
      return `<div>${esc(parts[0])}<span class="em">${esc(em)}</span>${esc(parts[1]||'')}</div>`;
    }
    return `<div>${esc(l)}</div>`;
  }).join('');
}

function slideHTML(s, idx, total) {
  let inner = '';
  if (s.type === 'hook') {
    inner = `
      <span class="badge">${esc(s.label)}</span>
      <h1 class="hook">${headHTML(s.title, s.em)}</h1>
      <p class="sub">${esc(s.sub)}</p>
      <div class="swipe">swipe →</div>`;
  } else if (s.type === 'cta') {
    inner = `
      <div class="ctaWrap">
        <div class="ctaKicker">Follow me</div>
        <h1 class="hook">${headHTML(s.head, s.em)}</h1>
        <p class="sub">${esc(s.sub)}</p>
      </div>`;
  } else {
    inner = `
      <div class="toprow"><span class="num">${esc(s.n)}</span><span class="eyebrow">${esc(s.label)}</span></div>
      <h1 class="head">${headHTML(s.head, s.em)}</h1>
      <p class="body">${esc(s.body)}</p>`;
  }
  return `<!DOCTYPE html><html><head><meta charset="UTF-8"/><style>
    *{margin:0;padding:0;box-sizing:border-box;}
    html,body{width:1080px;height:1080px;}
    body{background:${CREAM};color:${INK};font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
      padding:96px;display:flex;flex-direction:column;justify-content:center;position:relative;overflow:hidden;}
    .em{font-family:Georgia,"Times New Roman",serif;font-style:italic;color:${CORAL};}
    .badge{position:absolute;top:96px;left:96px;background:${CORAL};color:#fff;font-size:20px;font-weight:700;letter-spacing:.5px;padding:10px 20px;border-radius:999px;}
    .hook{font-size:92px;line-height:1.02;font-weight:800;letter-spacing:-2px;}
    .head{font-size:74px;line-height:1.05;font-weight:800;letter-spacing:-1.5px;margin-bottom:36px;}
    .sub{font-size:30px;color:${MUTE};margin-top:34px;max-width:820px;line-height:1.4;}
    .body{font-size:33px;color:${MUTE};line-height:1.45;max-width:860px;}
    .toprow{display:flex;align-items:center;gap:22px;margin-bottom:40px;}
    .num{font-size:40px;font-weight:800;color:${CORAL};}
    .eyebrow{font-size:22px;font-weight:700;letter-spacing:2px;color:${INK};border-left:3px solid ${CORAL};padding-left:16px;}
    .swipe{position:absolute;bottom:80px;left:96px;font-size:26px;color:${CORAL};font-weight:700;}
    .ctaKicker{font-size:24px;font-weight:700;letter-spacing:1px;color:${CORAL};margin-bottom:26px;}
    .footer{position:absolute;bottom:64px;left:96px;right:96px;display:flex;justify-content:space-between;align-items:center;
      font-size:19px;color:#8A8073;border-top:1px solid #DAD0C4;padding-top:20px;}
    .footer .brand{color:${CORAL};font-weight:700;}
  </style></head><body>
    ${inner}
    <div class="footer"><span class="brand">Follow me</span><span>${idx} / ${total}</span></div>
  </body></html>`;
}

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const pngPaths = [];
  for (let i = 0; i < slides.length; i++) {
    const num = String(i + 1).padStart(2, '0');
    const html = slideHTML(slides[i], i + 1, slides.length);
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1080 });
    await page.setContent(html, { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 300));
    const out = path.join(OUT_DIR, `slide-${num}.png`);
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
    pngPaths.push(out);
    console.log(`slide-${num}.png`);
    await page.close();
  }

  // Build PDF FROM the rendered PNGs (PNGs are source of truth)
  const imgsHTML = pngPaths.map(p => {
    const b64 = fs.readFileSync(p).toString('base64');
    return `<div class="pg"><img src="data:image/png;base64,${b64}"/></div>`;
  }).join('\n');
  const pdfHTML = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><style>
    *{margin:0;padding:0;} .pg{width:1080px;height:1080px;overflow:hidden;} img{width:1080px;height:1080px;display:block;}
    @page{size:1080px 1080px;margin:0;} @media print{.pg{page-break-after:always;}}
  </style></head><body>${imgsHTML}</body></html>`;
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });
  await page.setContent(pdfHTML, { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 500));
  const pdfPath = path.join(OUT_DIR, 'the-day-an-ai-vanished-carousel.pdf');
  await page.pdf({ path: pdfPath, width: '1080px', height: '1080px', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  console.log('PDF: ' + pdfPath);
  await browser.close();
  console.log('ALL_DONE');
})();
