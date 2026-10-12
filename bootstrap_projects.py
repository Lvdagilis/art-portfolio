
import os
import re
import json
from html.parser import HTMLParser

base_dir = os.getcwd()
index_path = os.path.join(base_dir, "index.html")
photo_path = os.path.join(base_dir, "projects/photography.html")
output_json = os.path.join(base_dir, "projects.json")

projects = []

class GalleryParser(HTMLParser):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.in_gallery = False
        self.in_item = False
        self.current_item = {}
        self.capture_h3 = False
        self.capture_p = False
        self.projects = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and 'gallery' in attrs.get('class', '').split():
            self.in_gallery = True
        
        if self.in_gallery:
            if tag == 'div' and 'gallery-item' in attrs.get('class', '').split():
                self.in_item = True
                self.current_item = {"category": self.category, "visible": True, "description": ""}
            
            if self.in_item:
                if tag == 'a':
                    self.current_item['link'] = attrs.get('href', '')
                elif tag == 'img':
                    self.current_item['image'] = attrs.get('src', '')
                    self.current_item['title'] = attrs.get('alt', '') # Fallback
                elif tag == 'h3':
                    self.capture_h3 = True
                elif tag == 'p':
                    # Only capture direct description, ignore other ps ?
                    self.capture_p = True

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_gallery:
            # We don't forcefully close gallery because nested divs might close it early in logic if not careful.
            # But gallery-items are distinct.
            pass
            
        if self.in_item and tag == 'div':
            # This is tricky because gallery-item contains divs. 
            # We rely on the structure being simple.
            pass

        if self.in_item and tag == 'a':
             # Usually </a> closes the main wrapper of the item content in my structure
             pass
        
        if tag == 'h3':
            self.capture_h3 = False
        if tag == 'p':
            self.capture_p = False

    def handle_data(self, data):
        if self.capture_h3:
            self.current_item['title'] = data.strip()
        if self.capture_p:
            desc = data.strip()
            if desc:
                self.current_item['description'] = desc

# Regex is probably safer and easier for this specific structure than writing a full parser state machine for nested divs
def parse_via_regex(html_content, category, base_path_correction=False):
    # Find the gallery block
    gallery_match = re.search(r'<div class="gallery">(.*?)</div>\s*</section>', html_content, re.DOTALL)
    # The gallery dict might end with </div> but be followed by other things.
    # Let's find "gallery-item" blocks.
    
    # This regex attempts to match the gallery-item structure
    # <div class="gallery-item"> ... </div>
    # It might fail if nested divs are complex, but our structure is shallow.
    item_pattern = re.compile(r'<div class="gallery-item">\s*<a href="([^"]+)">\s*<img src="([^"]+)" alt="([^"]+)"[^>]*>\s*<div class="[^"]+">\s*<h3>(.*?)</h3>(.*?)</div>\s*</a>\s*</div>', re.DOTALL)
    
    items = item_pattern.findall(html_content)
    parsed_projects = []
    
    for href, src, alt, title, rest in items:
        # Extract description from 'rest' if present
        desc = ""
        p_match = re.search(r'<p[^>]*>(.*?)</p>', rest, re.DOTALL)
        if p_match:
            desc = p_match.group(1).strip()
            
        # Clean title
        title = title.strip()
        
        # Correction
        if base_path_correction:
            if not href.startswith("projects/") and not href.startswith("http"):
                 href = f"projects/{href}"
            href = href.replace("projects/projects/", "projects/")  # Safety
            
            if src.startswith("../"):
                src = src[3:]
                
        parsed_projects.append({
            "title": title,
            "category": category,
            "visible": True,
            "image": src,
            "link": href,
            "description": desc
        })
        
    return parsed_projects

if os.path.exists(index_path):
    print("Parsing index.html...")
    with open(index_path, 'r') as f:
        # We need to only look at the 'work' section for regex to not match other things
        content = f.read()
        work_section = re.search(r'<section id="work">.*?</section>', content, re.DOTALL)
        if work_section:
            main_items = parse_via_regex(work_section.group(0), "main")
            projects.extend(main_items)

if os.path.exists(photo_path):
    print("Parsing projects/photography.html...")
    with open(photo_path, 'r') as f:
        photo_items = parse_via_regex(f.read(), "photography", base_path_correction=True)
        projects.extend(photo_items)

print(f"Found {len(projects)} projects.")

# Remove duplicates if any (e.g. Photography link itself)
unique_projects = []
seen_links = set()
for p in projects:
    if p['link'] not in seen_links:
        unique_projects.append(p)
        seen_links.add(p['link'])

with open(output_json, 'w') as f:
    json.dump(unique_projects, f, indent=4)

print(f"Saved to {output_json}")
