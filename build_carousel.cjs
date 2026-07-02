const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

(async () => {
    // Generate HTML first
    execSync('python3 generate_carousel_today.py');

    const d = new Date().toISOString().slice(0, 10);
    const outDir = `./carousel-routine/output/${d}/carousel-branded`;
    fs.mkdirSync(outDir, { recursive: true });

    const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 2 });

    const pdfImages = [];
    
    // Process all 7 slides
    for (let i = 1; i <= 7; i++) {
        const slidePath = `file://${path.resolve('./carousel-routine/temp/carousel-branded/slide-0' + i + '.html')}`;
        await page.goto(slidePath, { waitUntil: 'networkidle0' });
        const pngPath = `${outDir}/slide-0${i}.png`;
        await page.screenshot({ path: pngPath });
        console.log(`Generated ${pngPath}`);
    }

    // Now compile into PDF
    const pdfHtmlPath = `${outDir}/carousel.html`;
    let pdfHtml = `<html><body style="margin:0;padding:0;">`;
    for (let i = 1; i <= 7; i++) {
        pdfHtml += `<img src="file://${path.resolve(outDir + '/slide-0' + i + '.png')}" style="width:1080px;height:1080px;display:block;page-break-after:always;">`;
    }
    pdfHtml += `</body></html>`;
    fs.writeFileSync(pdfHtmlPath, pdfHtml);

    await page.goto(`file://${path.resolve(pdfHtmlPath)}`, { waitUntil: 'networkidle0' });
    await page.pdf({ 
        path: `${outDir}/linkedin-carousel-${d}.pdf`, 
        width: 1080,
        height: 1080,
        printBackground: true 
    });
    console.log(`Generated ${outDir}/linkedin-carousel-${d}.pdf`);

    await browser.close();
})();
