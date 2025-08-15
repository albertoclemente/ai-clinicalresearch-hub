#!/usr/bin/env python3
"""
Quick HTML generation script to test the premium UI template.
"""

import json
from jinja2 import Template
from datetime import datetime

# Load the brief data
with open('briefs/2025-08-15.json', 'r') as f:
    brief_data = json.load(f)

# Load the template
with open('templates/index.html', 'r') as f:
    template_content = f.read()

# Create Jinja2 template
template = Template(template_content)

# Prepare template variables
items = brief_data['items']
total_items = len(items)
brief_date = "2025-08-15"

# Render the template
html_output = template.render(
    items=items,
    total_items=total_items,
    brief_date=brief_date
)

# Save the output
with open('site/index.html', 'w') as f:
    f.write(html_output)

print(f"✅ Generated HTML with {total_items} articles")
print("📁 Output: site/index.html")
print("🎨 Premium UI enhancements applied!")
