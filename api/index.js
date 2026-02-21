const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');
const YTDlpWrap = require('yt-dlp-wrap').default;
const fs = require('fs');
const path = require('path');

// Setup yt-dlp binary in /tmp (writable folder)
const setupYtDlp = async () => {
    const filePath = path.join('/tmp', 'yt-dlp');
    if (!fs.existsSync(filePath)) {
        // Downloads the binary if not present
        await YTDlpWrap.downloadFromGithub(filePath);
        fs.chmodSync(filePath, '755'); // Make executable
    }
    return new YTDlpWrap(filePath);
};

export default async function handler(req, res) {
    // 1. Get URL from request
    const { url } = req.query;
    if (!url) return res.status(400).json({ error: 'Send a url param like ?url=...' });

    let browser = null;

    try {
        // 2. Launch Mini Browser (Puppeteer)
        browser = await puppeteer.launch({
            args: [...chromium.args, "--hide-scrollbars", "--disable-web-security"],
            defaultViewport: chromium.defaultViewport,
            executablePath: await chromium.executablePath(),
            headless: chromium.headless,
            ignoreHTTPSErrors: true,
        });

        const page = await browser.newPage();
        
        // Use a real Mobile User-Agent to look like your phone
        const userAgent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36";
        await page.setUserAgent(userAgent);

        // 3. Go to YouTube to get "Fresh" Cookies
        // We go to the embed URL because it loads faster than the full site
        const videoId = url.split('v=')[1]?.split('&')[0] || url.split('/').pop();
        await page.goto(`https://www.youtube.com/embed/${videoId}`, { 
            waitUntil: 'domcontentloaded', 
            timeout: 8000 
        });

        // Extract cookies from the browser session
        const cookies = await page.cookies();
        
        // Format cookies for yt-dlp (Netscape format)
        const cookieContent = cookies.map(c => {
            return `${c.domain}\tTRUE\t${c.path}\t${c.secure}\t${c.expires}\t${c.name}\t${c.value}`;
        }).join('\n');
        
        const cookiePath = '/tmp/cookies.txt';
        fs.writeFileSync(cookiePath, '# Netscape HTTP Cookie File\n' + cookieContent);

        // 4. Run yt-dlp with the cookies
        const ytDlp = await setupYtDlp();
        
        // Get the direct link (-g)
        const output = await ytDlp.execPromise([
            url,
            '-g', // Get URL only
            '--cookies', cookiePath,
            '--user-agent', userAgent,
            '-f', 'best[ext=mp4]/best', // Best MP4
        ]);

        res.status(200).json({ 
            link: output.trim(),
            status: "Success"
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ 
            error: error.message,
            tip: "If timeout, try again. Vercel Free tier has 10s limit." 
        });
    } finally {
        if (browser) await browser.close();
    }
}
