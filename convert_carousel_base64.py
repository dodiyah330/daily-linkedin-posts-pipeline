import json
import base64
import os

input_path = '/Users/prithal/.gemini/antigravity/brain/0b5e7dd5-21ed-4683-96b3-da9f768406a7/.system_generated/steps/341/output.txt'
out_dir = '/Users/prithal/3d website/linkedin-automation-routine/carousel-routine/output/2026-06-08/carousel-branded'

os.makedirs(out_dir, exist_ok=True)

with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract content between first '[' and first ']'
start = content.find('[')
end = content.find(']')

if start != -1 and end != -1:
    json_str = content[start:end+1]
else:
    raise ValueError("Could not find JSON array in output file")

# Parse JSON array of base64 strings
screenshots = json.loads(json_str.strip())

for i, b64 in enumerate(screenshots):
    png_path = os.path.join(out_dir, f'slide-0{i+1}.png')
    img_data = base64.b64decode(b64)
    with open(png_path, 'wb') as f:
        f.write(img_data)
    print(f"Saved {png_path}")

# Now generate the carousel.html compilation file using HTTP URLs
html_path = os.path.join(out_dir, 'carousel.html')
html_content = '<html><body style="margin:0;padding:0;">\n'
for i in range(1, 8):
    html_content += f'<img src="http://192.168.1.89:8000/carousel-routine/output/2026-06-08/carousel-branded/slide-0{i}.png" style="width:1080px;height:1080px;display:block;page-break-after:always;">\n'
html_content += '</body></html>'

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Generated compilation HTML at {html_path}")
