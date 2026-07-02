import json
import base64
import re

input_path = '/Users/prithal/.gemini/antigravity/brain/0b5e7dd5-21ed-4683-96b3-da9f768406a7/.system_generated/steps/331/output.txt'
output_path = '/Users/prithal/3d website/linkedin-automation-routine/linkedin-infographic-20260608.png'

with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The file contains:
# ### Result
# "iVBORw0KGgo..."
# Let's extract the string within the quotes
match = re.search(r'"([^"]+)"', content, re.DOTALL)
if not match:
    # Try reading the whole content excluding the header if no quotes
    lines = content.strip().split('\n')
    if lines[0].startswith('###'):
        base64_str = ''.join(lines[1:]).strip()
    else:
        base64_str = content.strip()
else:
    base64_str = match.group(1).replace('\n', '').replace('\r', '').strip()

img_data = base64.b64decode(base64_str)
with open(output_path, 'wb') as f:
    f.write(img_data)

print(f"Decoded and saved to {output_path}")
