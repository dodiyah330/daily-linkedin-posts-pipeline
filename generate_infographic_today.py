import os
import json

def main():
    json_path = "./infographic_data.json"
    template_path = "./linkedin-infographic-template.html"
    output_path = "./linkedin-infographic.html"
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found. Cannot generate infographic.")
        return
        
    if not os.path.exists(template_path):
        print(f"Error: {template_path} not found.")
        return

    with open(json_path) as f:
        data = json.load(f)

    # Build the bar rows HTML
    bar_rows_html = []
    for bar in data.get("bars", []):
        row = f"""    <div class="bar-row">
      <div class="bar-info">
        <span class="bar-label">{bar.get('label')}</span>
        <span class="bar-value">{bar.get('value')}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width: {bar.get('value')}; background-color: {bar.get('color', '#5E6AD2')};"></div>
      </div>
    </div>"""
        bar_rows_html.append(row)
        
    bar_rows_combined = "\n".join(bar_rows_html)

    with open(template_path) as f:
        template = f.read()

    # Perform replacements
    html_content = template
    html_content = html_content.replace("{{BADGE}}", data.get("badge", "📊 Insights"))
    html_content = html_content.replace("{{DATE_LABEL}}", data.get("date_label", ""))
    html_content = html_content.replace("{{TITLE_MAIN}}", data.get("title_main", ""))
    html_content = html_content.replace("{{TITLE_SPAN}}", data.get("title_span", ""))
    html_content = html_content.replace("{{SUBTITLE}}", data.get("subtitle", ""))
    html_content = html_content.replace("{{BAR_ROWS}}", bar_rows_combined)
    html_content = html_content.replace("{{TAKEAWAY_NUM}}", data.get("takeaway_num", ""))
    html_content = html_content.replace("{{TAKEAWAY_TEXT}}", data.get("takeaway_text", ""))
    html_content = html_content.replace("{{SOURCE}}", data.get("source", ""))

    with open(output_path, "w") as f:
        f.write(html_content)

    print(f"Infographic HTML generated successfully at {output_path}")

if __name__ == "__main__":
    main()
