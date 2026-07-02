const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

(async () => {
  try {
    const dateStr = new Date().toISOString().slice(0, 10);
    const tempDir = path.join(__dirname, 'temp', 'carousel-branded');
    const outDir = path.join(__dirname, 'output', dateStr, 'carousel-branded');
    fs.mkdirSync(outDir, { recursive: true });

    // Copy assets from temp to output directory so they resolve correctly
    const srcAssetsDir = path.join(tempDir, 'assets');
    const destAssetsDir = path.join(outDir, 'assets');
    if (fs.existsSync(srcAssetsDir)) {
      fs.cpSync(srcAssetsDir, destAssetsDir, { recursive: true });
    }

    const htmlFiles = fs.readdirSync(tempDir)
      .filter(f => /^slide-\d+\.html$/.test(f))
      .sort()
      .map(f => path.join(tempDir, f));

    if (htmlFiles.length === 0) {
      console.error('No slide HTML files found.');
      process.exit(1);
    }

    console.log('Compiling PDF from HTML slides...');

    // Combine files into a single printable HTML doc
    let combinedHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  body {
    margin: 0;
    padding: 0;
    width: auto !important;
    height: auto !important;
    overflow: visible !important;
    background: none !important;
  }
  .slide {
    position: relative;
    width: 1080px;
    height: 1080px;
    overflow: hidden;
    box-sizing: border-box;
  }
  @page {
    size: 1080px 1080px;
    margin: 0;
  }
  @media print {
    .slide {
      page-break-after: always;
      page-break-inside: avoid;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
  }
</style>
</head>
<body>
`;

    // Read stylesheets and slides
    // Since all slides share the exact same style, we can just load the first slide's style,
    // convert body rules to .slide rules, then output all slide contents.
    const firstSlide = fs.readFileSync(htmlFiles[0], 'utf8');
    const styleMatch = firstSlide.match(/<style>([\s\S]*?)<\/style>/);
    let styleContent = styleMatch ? styleMatch[1] : '';

    // Convert body selector to .slide selector to contain styles inside slide divs
    styleContent = styleContent.replace(/body\s*\{/, '.slide {');

    // Extract link tags (for Google Fonts)
    const linkMatches = firstSlide.match(/<link[^>]+>/g);
    const linkContent = linkMatches ? linkMatches.join('\n') : '';

    combinedHtml += `${linkContent}\n<style>${styleContent}</style>\n`;

    for (const htmlFile of htmlFiles) {
      const content = fs.readFileSync(htmlFile, 'utf8');
      // Extract the body content between <body> and </body>
      const bodyMatch = content.match(/<body>([\s\S]*?)<\/body>/);
      if (bodyMatch) {
        combinedHtml += `<div class="slide">\n` + bodyMatch[1] + `\n</div>\n`;
      }
    }

    combinedHtml += '</body>\n</html>';

    // Break any potential infinite onerror loops
    combinedHtml = combinedHtml.replaceAll("onerror=\"this.src='assets/interface.png'\"", "onerror=\"this.onerror=null; this.src='assets/interface.png';\"");

    const combinedHtmlPath = path.join(outDir, 'combined_print.html');
    fs.writeFileSync(combinedHtmlPath, combinedHtml);

    // Launch browser and print to PDF
    console.log("1. Launching browser...");
    const browser = await puppeteer.launch({
      headless: 'shell',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    console.log("2. Creating page...");
    const page = await browser.newPage();
    
    // Set window viewport to 1080x1080
    console.log("3. Setting viewport...");
    await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });
    
    console.log("4. Setting request interception...");
    await page.setRequestInterception(true);
    page.on('request', req => {
      const url = req.url();
      if ((url.startsWith('http') || url.startsWith('https')) && !url.includes('fonts.googleapis.com') && !url.includes('fonts.gstatic.com')) {
        req.abort();
      } else {
        req.continue();
      }
    });

    console.log("5. Navigating to combined HTML...");
    await page.goto('file://' + encodeURI(combinedHtmlPath), { waitUntil: 'domcontentloaded', timeout: 0 });
    console.log("6. Waiting 2s...");
    await new Promise(r => setTimeout(r, 2000));

    const outPdfPath = path.join(outDir, 'startup-strategy-carousel.pdf');
    
    console.log("7. Printing PDF...");
    await page.pdf({
      path: outPdfPath,
      width: '1080px',
      height: '1080px',
      printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 }
    });

    console.log(`PDF compiled successfully to ${outPdfPath}`);
    
    // Clean up temp combined HTML file
    fs.unlinkSync(combinedHtmlPath);
    
    await browser.close();
  } catch (err) {
    console.error("CRITICAL ERROR IN PDF COMPILATION:", err.stack || err);
    process.exit(1);
  }
})();
