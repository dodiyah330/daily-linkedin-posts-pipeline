const puppeteer = require('puppeteer');
const fs = require('fs');

const urls = [
  "https://www.reddit.com/r/entrepreneur/top.json?limit=25&t=week&raw_json=1",
  "https://www.reddit.com/r/startups/top.json?limit=25&t=week&raw_json=1",
  "https://www.reddit.com/r/artificial/top.json?limit=25&t=week&raw_json=1",
  "https://www.reddit.com/r/SideProject/top.json?limit=20&t=week&raw_json=1",
  "https://www.reddit.com/r/ChatGPT/top.json?limit=20&t=week&raw_json=1",
  "https://www.reddit.com/r/passive_income/top.json?limit=20&t=week&raw_json=1"
];

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  // Set User-Agent to look like a real browser
  await page.setUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");
  
  let allPosts = [];
  
  for (const url of urls) {
    console.log(`Fetching: ${url}`);
    try {
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
      const bodyText = await page.evaluate(() => document.body.innerText);
      
      let data;
      try {
        data = JSON.parse(bodyText);
      } catch (e) {
        console.error(`Failed to parse JSON for ${url}. Body length: ${bodyText.length}`);
        // Let's write bodyText to a temp file for debugging
        fs.writeFileSync('./reddit_debug_body.html', bodyText);
        continue;
      }
      
      const posts = (data.data && data.data.children) || [];
      console.log(`Found ${posts.length} posts`);
      
      for (const post of posts) {
        const postData = post.data || {};
        
        let image_url = null;
        if (postData.url_overridden_by_dest && /\.(png|jpg|jpeg|gif|webp)/i.test(postData.url_overridden_by_dest)) {
          image_url = postData.url_overridden_by_dest;
        } else if (postData.preview && postData.preview.images && postData.preview.images.length > 0) {
          image_url = postData.preview.images[0].source ? postData.preview.images[0].source.url : null;
        } else if (postData.thumbnail && postData.thumbnail.startsWith('http')) {
          image_url = postData.thumbnail;
        }
        
        const simplified_post = {
          subreddit: postData.subreddit,
          title: postData.title,
          selftext: postData.selftext || "",
          ups: postData.ups || 0,
          num_comments: postData.num_comments || 0,
          url: "https://www.reddit.com" + (postData.permalink || ""),
          image_url: image_url
        };
        allPosts.push(simplified_post);
      }
      
      // Wait a bit to avoid hitting rate limits
      await new Promise(r => setTimeout(r, 2000));
    } catch (err) {
      console.error(`Error fetching ${url}: ${err.message}`);
    }
  }
  
  await browser.close();
  
  fs.writeFileSync("./reddit_data.json", JSON.stringify(allPosts, null, 2));
  console.log(`Saved ${allPosts.length} posts to ./reddit_data.json`);
})();
