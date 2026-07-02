const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

(async () => {
    console.log("Starting carousel rendering using puppeteer-core...");
    const d = '2026-06-07'; // Fixed to today's scheduled date
    const outDir = path.resolve(__dirname, `./carousel-routine/output/${d}/carousel-branded`);
    fs.mkdirSync(outDir, { recursive: true });

    const browser = await puppeteer.launch({
        executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 2 });

    // Process all 7 slides
    for (let i = 1; i <= 7; i++) {
        const slidePath = `file://${path.resolve(__dirname, './carousel-routine/temp/carousel-branded/slide-0' + i + '.html')}`;
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
    const pdfPath = `${outDir}/carousel-20260607.pdf`; // We use fixed name or date-based name
    await page.pdf({ 
        path: pdfPath, 
        width: 1080,
        height: 1080,
        printBackground: true 
    });
    console.log(`Generated PDF at ${pdfPath}`);

    // Also copy to slack_downloads so the scheduler can find it if needed
    const destDir = path.resolve(__dirname, './slack_downloads');
    fs.mkdirSync(destDir, { recursive: true });
    fs.copyFileSync(pdfPath, path.join(destDir, 'carousel-20260607.pdf'));
    console.log(`Copied PDF to slack_downloads/carousel-20260607.pdf`);

    await browser.close();
    console.log("Carousel build complete!");
})();
