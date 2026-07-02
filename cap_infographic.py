from playwright.sync_api import sync_playwright
import os
import datetime

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        # Use an absolute file path
        file_path = f"file://{os.path.abspath('linkedin-infographic.html')}"
        page.goto(file_path)
        d = datetime.date.today().strftime('%Y%m%d')
        page.screenshot(path=f"linkedin-infographic-{d}.png", clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
        browser.close()

if __name__ == "__main__":
    capture()
