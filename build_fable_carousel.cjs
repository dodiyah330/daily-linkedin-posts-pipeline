const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

(async () => {
    console.log("Generating HTML slides first...");
    execSync('python3 generate_fable_carousel.py', { cwd: __dirname });

    const d = new Date().toISOString().slice(0, 10);
    const outDir = path.resolve(__dirname, `./carousel-routine/output/${d}/carousel-branded`);
    fs.mkdirSync(outDir, { recursive: true });

    console.log("Launching Chrome using puppeteer-core in headless mode (true)...");
    const browser = await puppeteer.launch({
        executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-gpu',
          '--disable-dev-shm-usage',
          '--use-mock-keychain',
          '--password-store=basic',
          '--disable-extensions',
          '--disable-component-update',
          '--no-default-browser-check'
        ]
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
    const pdfPath = `${outDir}/linkedin-carousel-${d}.pdf`;
    await page.pdf({ 
        path: pdfPath, 
        width: 1080,
        height: 1080,
        printBackground: true 
    });
    console.log(`Generated PDF at ${pdfPath}`);

    // Copy to /Users/prithal/Downloads
    const downloadsDir = "/Users/prithal/Downloads";
    fs.mkdirSync(downloadsDir, { recursive: true });
    const destPdf = path.join(downloadsDir, `linkedin-carousel-fable-${d.replace(/-/g, '')}.pdf`);
    fs.copyFileSync(pdfPath, destPdf);
    console.log(`Copied PDF to Downloads: ${destPdf}`);

    await browser.close();
    console.log("Carousel build complete!");
})();
