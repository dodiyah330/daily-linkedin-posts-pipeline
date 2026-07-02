import os
import sys
import datetime

def generate_paper(date_compact=None):
    if not date_compact:
        date_compact = datetime.date.today().isoformat().replace("-", "")
    
    date_str = f"{date_compact[:4]}-{date_compact[4:6]}-{date_compact[6:8]}"
    txt_filename = f"linkedin_posts_{date_compact}.txt"
    html_filename = f"linkedin_posts_{date_compact}.html"

    if not os.path.exists(txt_filename):
        print(f"Error: Text posts file '{txt_filename}' not found.")
        return False

    posts = {}
    current_key = None
    current_content = []

    with open(txt_filename, "r") as f:
        for line in f:
            if line.startswith("=================================================="):
                continue
            elif line.startswith("1. COLLABORATIVE ARTICLE"):
                current_key = "collaborative_article"
                current_content = []
            elif line.startswith("2. POLL"):
                current_key = "poll"
                current_content = []
            elif line.startswith("3. CAROUSEL"):
                current_key = "carousel"
                current_content = []
            elif line.startswith("4. INFOGRAPHIC"):
                current_key = "infographic"
                current_content = []
            elif line.startswith("5. POST 1"):
                current_key = "post_1"
                current_content = []
            elif line.startswith("6. POST 2"):
                current_key = "post_2"
                current_content = []
            elif line.startswith("7. POST 3"):
                current_key = "post_3"
                current_content = []
            elif line.startswith("8. POST 4"):
                current_key = "post_4"
                current_content = []
            elif line.startswith("9. POST 5"):
                current_key = "post_5"
                current_content = []
            elif line.startswith("10. POST 6"):
                current_key = "post_6"
                current_content = []
            elif line.startswith("11. POST 7"):
                current_key = "post_7"
                current_content = []
            else:
                if current_key:
                    current_content.append(line)
            
            if current_key:
                posts[current_key] = "".join(current_content).strip()

    def get_article_title(key, post_raw, meta_raw):
        lines = post_raw.strip().split("\n")
        if lines and (lines[0].startswith("Headline:") or lines[0].startswith("Headline ")):
            return lines[0].replace("Headline:", "").replace("Headline", "").strip()
        
        # Fallback to generic title based on key or metadata
        if key == "collaborative_article":
            return "Collaborative Discussion"
        elif key == "poll":
            return "Engagement Poll"
        elif key.startswith("post_"):
            # Try to parse Archetype from meta_raw
            for line in meta_raw.split("\n"):
                if "Archetype:" in line:
                    return line.split("Archetype:")[1].split("|")[0].strip()
            return f"Daily Post {key.split('_')[1]}"
        return "Daily Insight"

    clean_posts = {}
    metadata = {}
    article_titles = {}
    
    # Simple formatting helper to preserve paragraphs in HTML
    def format_text(text):
        paragraphs = text.split("\n\n")
        formatted = []
        for p in paragraphs:
            if p.strip():
                formatted.append(f"<p>{p.strip().replace(chr(10), '<br>')}</p>")
        return "\n".join(formatted)

    for k, v in posts.items():
        # Clean up Headline from raw text if present
        post_body = v
        lines = v.strip().split("\n")
        if lines and (lines[0].startswith("Headline:") or lines[0].startswith("Headline ")):
            post_body = "\n".join(lines[1:]).strip()
            
        if k.startswith("post_"):
            # Separate body from metadata
            body_lines = []
            meta_lines = []
            for line in post_body.split("\n"):
                if any(line.startswith(x) for x in ["Tool featured:", "Tools/stories featured:", "Story/announcement:", "Profession/sector affected:", "Take:", "What's being shared:", "Source:", "Archetype:", "Why this works:", "Word count:"]):
                    meta_lines.append(line)
                else:
                    body_lines.append(line)
            clean_posts[k] = "\n".join(body_lines).strip()
            metadata[k] = "\n".join(meta_lines).strip()
        elif k == "carousel":
            # Extract caption only
            body_lines = []
            capture = False
            for line in post_body.split("\n"):
                if line.startswith("Caption:") or line.startswith("CAROUSEL CAPTION:"):
                    capture = True
                    continue
                if line.startswith("Slide 1:"):
                    capture = False
                if capture:
                    body_lines.append(line)
            clean_posts[k] = "\n".join(body_lines).strip()
        elif k == "infographic":
            # Extract caption only
            body_lines = []
            capture = False
            for line in post_body.split("\n"):
                if line.startswith("Caption:") or line.startswith("INFOGRAPHIC CAPTION:"):
                    capture = True
                    continue
                if line.startswith("Hero Number:") or line.startswith("Donut Breakdown:") or line.startswith("Timeline:") or line.startswith("Takeaway:"):
                    capture = False
                if capture:
                    body_lines.append(line)
            clean_posts[k] = "\n".join(body_lines).strip()
            metadata[k] = post_body[post_body.find("Donut Breakdown:") if post_body.find("Donut Breakdown:") != -1 else post_body.find("Hero Number:"):].strip()
        else:
            clean_posts[k] = post_body

    for k, v in posts.items():
        article_titles[k] = get_article_title(k, v, metadata.get(k, ""))

    # Asset paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_url = f"file://{os.path.join(script_dir, 'carousel-routine', 'output', date_str, 'carousel-branded', 'startup-strategy-carousel.pdf')}"
    infographic_png = f"file://{os.path.join(script_dir, f'linkedin-infographic-{date_compact}.png')}"
    
    slides_html = ""
    for i in range(1, 8):
        slide_png = f"file://{os.path.join(script_dir, 'carousel-routine', 'output', date_str, 'carousel-branded', f'slide-0{i}.png')}"
        slides_html += f"""
        <div class="slide-card">
            <span class="slide-label">Slide {i}</span>
            <img src="{slide_png}" alt="Slide {i}" onerror="this.style.display='none';">
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>The Daily Founder — {date_str}</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Instrument+Serif:ital,wght@0,400;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        background-color: #FAF9F5;
        color: #141413;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
        padding: 40px 20px;
    }}
    .container {{
        max-width: 1400px;
        margin: 0 auto;
    }}
    
    /* Newspaper Header */
    .paper-header {{
        border-bottom: 2px solid #141413;
        padding-bottom: 20px;
        margin-bottom: 40px;
        text-align: center;
    }}
    .header-top {{
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 1px solid rgba(0, 0, 0, 0.08);
        padding-bottom: 15px;
        margin-bottom: 10px;
    }}
    .issue-no {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .logo {{
        font-family: 'Instrument Serif', serif;
        font-size: 64px;
        font-weight: 400;
        font-style: italic;
        line-height: 1;
        color: #d97757;
    }}
    .source-tag {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .header-meta {{
        display: flex;
        justify-content: space-between;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        color: #666;
        letter-spacing: 1px;
    }}
    
    /* Layout Grid */
    .paper-grid {{
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 40px;
    }}
    
    .main-column {{
        display: flex;
        flex-direction: column;
        gap: 40px;
    }}
    .side-column {{
        display: flex;
        flex-direction: column;
        gap: 40px;
        border-left: 1px solid rgba(0, 0, 0, 0.08);
        padding-left: 40px;
    }}
    
    /* Section Titles */
    .section-title {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 18px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 2px solid #141413;
        padding-bottom: 8px;
        margin-bottom: 25px;
        color: #d97757;
    }}
    
    /* Article Card */
    .article {{
        background: #FFF;
        border: 1px solid #E5E4DE;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.01);
        position: relative;
    }}
    .article-header {{
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 20px;
    }}
    .article-badge {{
        background-color: rgba(217, 119, 87, 0.1);
        color: #d97757;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .article-title {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 26px;
        font-weight: 800;
        line-height: 1.25;
        letter-spacing: -0.5px;
        color: #141413;
        margin-top: 8px;
    }}
    .article-body {{
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        line-height: 1.65;
        color: #2a2a2a;
        white-space: pre-wrap;
        margin-bottom: 25px;
    }}
    .article-body p {{
        margin-bottom: 16px;
    }}
    .article-meta {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 12px;
        color: #888;
        border-top: 1px dashed rgba(0,0,0,0.08);
        padding-top: 15px;
        white-space: pre-wrap;
    }}
    
    /* Action Buttons */
    .btn-copy {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background-color: #141413;
        color: #FAF9F5;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    .btn-copy:hover {{
        background-color: #d97757;
    }}
    .btn-copy.copied {{
        background-color: #489953;
    }}
    
    /* Infographic Preview */
    .infographic-preview img {{
        width: 100%;
        border-radius: 12px;
        border: 1px solid #E5E4DE;
        box-shadow: 0 10px 30px rgba(0,0,0,0.03);
        margin-top: 15px;
    }}
    
    /* Slides Container */
    .slides-preview {{
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin-top: 20px;
    }}
    .slide-card {{
        position: relative;
    }}
    .slide-label {{
        position: absolute;
        top: 15px;
        left: 15px;
        background-color: rgba(20,20,20,0.8);
        color: #FFF;
        padding: 4px 10px;
        border-radius: 4px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 11px;
        font-weight: 700;
        z-index: 10;
    }}
    .slide-card img {{
        width: 100%;
        border-radius: 12px;
        border: 1px solid #E5E4DE;
    }}
    
    /* Responsive Grid */
    @media (max-width: 1100px) {{
        .paper-grid {{
            grid-template-columns: 1fr;
        }}
        .side-column {{
            border-left: none;
            padding-left: 0;
        }}
    }}
    
    /* Print Styles for PDF Generation */
    @media print {{
        body {{
            background-color: #FAF9F5 !important;
            padding: 0 !important;
            color: #141413 !important;
        }}
        .container {{
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        .btn-copy {{
            display: none !important;
        }}
        .paper-grid {{
            display: block !important;
        }}
        .main-column, .side-column {{
            width: 100% !important;
            border-left: none !important;
            padding-left: 0 !important;
            gap: 20px !important;
        }}
        .article {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            border: 1px solid #E5E4DE !important;
            background: #FFF !important;
            box-shadow: none !important;
            margin-bottom: 15px !important;
            padding: 20px !important;
        }}
        .slides-preview, .infographic-preview {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}
        h1, h2, h3, .section-title {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}
    }}
</style>
</head>
<body>
<div class="container">
    <header class="paper-header">
        <div class="header-top">
            <span class="issue-no">ISSUE NO. {date_compact}</span>
            <h1 class="logo">The Daily Founder</h1>
            <span class="source-tag">FOUNDERS WING</span>
        </div>
        <div class="header-meta">
            <span>DATE: {date_str}</span>
            <span>EDITION: LINKEDIN DAILY SHEET</span>
            <span>STATUS: GENERATED SUCCESSFULLY</span>
        </div>
    </header>

    <div class="paper-grid">
        <!-- Main Column: Posts -->
        <main class="main-column">
            <div class="section-title">Core Discussion & Poll</div>
            
            <!-- Collaborative Article -->
            <article class="article">
                <div class="article-header">
                    <div>
                        <span class="article-badge">01. Collaborative Article</span>
                        <h2 class="article-title">{article_titles.get("collaborative_article", "")}</h2>
                    </div>
                    <button class="btn-copy" onclick="copyToClipboard('text-collab', this)">Copy Post</button>
                </div>
                <div class="article-body" id="text-collab">{clean_posts.get("collaborative_article", "")}</div>
            </article>
            
            <!-- Poll -->
            <article class="article">
                <div class="article-header">
                    <div>
                        <span class="article-badge">02. Engagement Poll</span>
                        <h2 class="article-title">{article_titles.get("poll", "")}</h2>
                    </div>
                    <button class="btn-copy" onclick="copyToClipboard('text-poll', this)">Copy Post</button>
                </div>
                <div class="article-body" id="text-poll">{clean_posts.get("poll", "")}</div>
            </article>

            <div class="section-title">Plain-Text AI News Curation</div>
            
            <!-- AI News Posts -->
            {"".join([f'''
            <article class="article" style="margin-bottom: 20px;">
                <div class="article-header">
                    <div>
                        <span class="article-badge">{article_titles.get(f"post_{i-4}", "")}</span>
                    </div>
                    <button class="btn-copy" onclick="copyToClipboard('text-post-{i-4}', this)">Copy Post</button>
                </div>
                <div class="article-body" id="text-post-{i-4}">{clean_posts.get(f"post_{i-4}", "")}</div>
                <div class="article-meta">{metadata.get(f"post_{i-4}", "")}</div>
            </article>
            ''' for i in range(5, 12)])}
        </main>
        
        <!-- Side Column: Previews -->
        <aside class="side-column">
            <!-- Infographic Section -->
            <div>
                <div class="section-title">Infographic</div>
                <article class="article">
                    <div class="article-header">
                        <div>
                            <span class="article-badge">04. Infographic Caption</span>
                        </div>
                        <button class="btn-copy" onclick="copyToClipboard('text-info-caption', this)">Copy Caption</button>
                    </div>
                    <div class="article-body" id="text-info-caption" style="font-size: 14px;">{clean_posts.get("infographic", "")}</div>
                    <div class="article-meta" style="font-size: 11px;">{metadata.get("infographic", "")}</div>
                    <div class="infographic-preview">
                        <img src="{infographic_png}" alt="Infographic Preview">
                    </div>
                </article>
            </div>
            
            <!-- Carousel Section -->
            <div>
                <div class="section-title">Carousel Slides</div>
                <article class="article">
                    <div class="article-header">
                        <div>
                            <span class="article-badge">03. Carousel Caption</span>
                        </div>
                        <button class="btn-copy" onclick="copyToClipboard('text-carousel-caption', this)">Copy Caption</button>
                    </div>
                    <div class="article-body" id="text-carousel-caption" style="font-size: 14px;">{clean_posts.get("carousel", "")}</div>
                    <div class="article-meta" style="margin-bottom: 20px;">
                        <a href="{pdf_url}" target="_blank" style="color: #d97757; font-weight: 700; text-decoration: none;">Download Carousel PDF ↗</a>
                    </div>
                    <div class="slides-preview">
                        {slides_html}
                    </div>
                </article>
            </div>
        </aside>
    </div>
</div>

<script>
function copyToClipboard(textId, buttonEl) {{
    const el = document.getElementById(textId);
    // Extract innerText or innerHTML depending on formatting
    let text = el.innerText || el.textContent;
    
    // Fallback split for headers
    if (textId === 'text-collab' || textId === 'text-poll') {{
        // strip header line
        const lines = text.split('\\n');
        if (lines[0].startsWith('Headline:')) {{
            text = lines.slice(1).join('\\n').trim();
        }}
    }}
    
    navigator.clipboard.writeText(text.trim()).then(() => {{
        const originalText = buttonEl.innerHTML;
        buttonEl.innerHTML = "✓ Copied!";
        buttonEl.classList.add("copied");
        buttonEl.style.backgroundColor = "#489953";
        setTimeout(() => {{
            buttonEl.innerHTML = originalText;
            buttonEl.classList.remove("copied");
            buttonEl.style.backgroundColor = "#141413";
        }}, 1500);
    }}).catch(err => {{
        console.error('Could not copy text: ', err);
    }});
}}
</script>
</body>
</html>
"""

    with open(html_filename, "w") as f:
        f.write(html_content)
    
    print(f"Daily newspaper generated successfully: {html_filename}")
    print(f"Link to view: file://{os.path.abspath(html_filename)}")
    
    # Generate PDF of the daily newspaper
    pdf_filename = html_filename.replace(".html", ".pdf")
    import subprocess
    import shutil
    print("Generating PDF from daily newspaper HTML...")
    try:
        env = os.environ.copy()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env["NODE_PATH"] = os.path.join(script_dir, "carousel-routine", "node_modules")
        subprocess.run([
            "node", "print_paper.cjs", html_filename, pdf_filename
        ], check=True, env=env)
        print(f"✓ PDF generated successfully: {pdf_filename}")
    except Exception as e:
        print(f"Error printing daily newspaper PDF: {e}")
        
    # Copy files to Downloads folder
    downloads_dir = "/Users/prithal/Downloads"
    if os.path.exists(downloads_dir):
        print(f"Copying generated assets to Downloads: {downloads_dir}")
        try:
            # 1. Newspaper HTML
            shutil.copy2(html_filename, os.path.join(downloads_dir, html_filename))
            # 2. Newspaper PDF
            if os.path.exists(pdf_filename):
                shutil.copy2(pdf_filename, os.path.join(downloads_dir, pdf_filename))
            # 3. Infographic PNG
            infographic_local = f"linkedin-infographic-{date_compact}.png"
            if os.path.exists(infographic_local):
                shutil.copy2(infographic_local, os.path.join(downloads_dir, infographic_local))
            # 4. Carousel PDF
            script_dir = os.path.dirname(os.path.abspath(__file__))
            carousel_dir = os.path.join(script_dir, "carousel-routine", "output", date_str, "carousel-branded")
            if os.path.exists(carousel_dir):
                carousel_pdfs = [os.path.join(carousel_dir, f) for f in os.listdir(carousel_dir) if f.endswith(".pdf")]
                if carousel_pdfs:
                    carousel_pdfs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                    shutil.copy2(carousel_pdfs[0], os.path.join(downloads_dir, f"startup-strategy-carousel-{date_compact}.pdf"))
            print("✓ Assets copied successfully to Downloads.")
        except Exception as e:
            print(f"Error copying assets to Downloads: {e}")
            
    return True

if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    generate_paper(date_arg)
