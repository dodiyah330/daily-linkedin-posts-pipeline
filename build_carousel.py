from playwright.sync_api import sync_playwright
import os
import datetime

def capture():
    date_str = datetime.date.today().isoformat()
    out_dir = f"./carousel-routine/output/{date_str}/carousel-branded"
    os.makedirs(out_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        
        pdf_html_path = os.path.abspath(f"{out_dir}/carousel.html")
        pdf_html = "<html><body style='margin:0;padding:0;'>"
        
        for i in range(1, 8):
            html_path = os.path.abspath(f"./carousel-routine/temp/carousel-branded/slide-0{i}.html")
            page.goto(f"file://{html_path}")
            png_path = f"{out_dir}/slide-0{i}.png"
            page.screenshot(path=png_path)
            print(f"Generated {png_path}")
            pdf_html += f"<img src='file://{os.path.abspath(png_path)}' style='width:1080px;height:1080px;display:block;page-break-after:always;'>"
        
        pdf_html += "</body></html>"
        with open(pdf_html_path, "w") as f:
            f.write(pdf_html)
            
        page.goto(f"file://{pdf_html_path}")
        pdf_path = f"{out_dir}/carousel.pdf"
        page.pdf(path=pdf_path, width="1080px", height="1080px", print_background=True)
        print(f"Generated {pdf_path}")
        browser.close()

if __name__ == "__main__":
    capture()
