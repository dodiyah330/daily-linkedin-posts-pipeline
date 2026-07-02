import json
import base64
import os
import re

input_path = '/Users/prithal/.gemini/antigravity/brain/0b5e7dd5-21ed-4683-96b3-da9f768406a7/.system_generated/steps/406/output.txt'
pdf_path = '/Users/prithal/3d website/linkedin-automation-routine/linkedin_posts_20260608.pdf'

with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract base64 string from inside double quotes
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
print(f"Saved daily newspaper PDF to {pdf_path}")
