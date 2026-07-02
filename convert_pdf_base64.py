import json
import base64
import os
import re

input_path = '/Users/prithal/.gemini/antigravity/brain/0b5e7dd5-21ed-4683-96b3-da9f768406a7/.system_generated/steps/362/output.txt'
out_dir = '/Users/prithal/3d website/linkedin-automation-routine/carousel-routine/output/2026-06-08/carousel-branded'
pdf_path = os.path.join(out_dir, 'linkedin-carousel-2026-06-08.pdf')
slack_dir = '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads'
slack_pdf_path = os.path.join(slack_dir, 'carousel-20260608.pdf')

os.makedirs(out_dir, exist_ok=True)
os.makedirs(slack_dir, exist_ok=True)

with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract base64 string from inside the double quotes
match = re.search(r'"([^"]+)"', content, re.DOTALL)
if not match:
    lines = content.strip().split('\n')
    if lines[0].startswith('###'):
        base64_str = ''.join(lines[1:]).strip()
    else:
        base64_str = content.strip()
else:
    base64_str = match.group(1).replace('\n', '').replace('\r', '').strip()

pdf_data = base64.b64decode(base64_str)

with open(pdf_path, 'wb') as f:
    f.write(pdf_data)
print(f"Saved PDF to {pdf_path}")

with open(slack_pdf_path, 'wb') as f:
    f.write(pdf_data)
print(f"Copied PDF to {slack_pdf_path}")
