
import os
import json
import re

base_dir = os.getcwd()
projects_json_path = os.path.join(base_dir, "projects.json")
index_path = os.path.join(base_dir, "index.html")
photo_html_path = os.path.join(base_dir, "projects/photography.html")

def generate_gallery_html(items, context="root"):
    html = ""
    for item in items:
        if not item.get("visible", True):
            continue
            
        title = item["title"]
        image = item["image"]
        link = item["link"]
        desc = item.get("description", "")
        
        # Path adjustments
        if context == "subdir":
            # Image "../"
            if not image.startswith("../") and not image.startswith("http"):
                 image = "../" + image
            # Link strip "projects/" if valid
            if link.startswith("projects/"):
                link = link.replace("projects/", "")
        
        html += f"""                <div class="gallery-item">
                    <a href="{link}">
                        <img src="{image}" alt="{title}" loading="lazy">
                        <div class="gallery-info">
                            <h3>{title}</h3>
"""
        if desc:
            html += f"                            <p>{desc}</p>\n"
            
        html += """                        </div>
                    </a>
                </div>
"""
    return html

def update_index(projects):
    if not os.path.exists(index_path):
        print("Error: index.html not found")
        return

    main_projects = [p for p in projects if p.get("category") == "main"]
    
    # Generate HTML
    gallery_html = '<div class="gallery">\n'
    gallery_html += generate_gallery_html(main_projects, context="root")
    gallery_html += "            </div>"
    
    with open(index_path, 'r') as f:
        content = f.read()
        
    # Replace the gallery div. 
    # We look for <div class="gallery"> ... </div> inside <section id="work">
    # Because valid HTML parsers might be overkill/slow/removed, regex is fast if structure is known.
    # But wait, my previous regex relied on replacing the whole section.
    # Let's target strictly the <div class="gallery">...</div>
    
    # We can match start and end of gallery div.
    # However, since we have the start of the section "Other Works", let's use that as anchor.
    
    # Pattern: <h3 class="other-works-heading">Other Works</h3>\s*<div class="gallery">.*?</div>(\s*</section>)
    # We need to match the specific closing div of gallery, not section.
    # Counting divs is hard with regex. 
    # But we know the gallery is the last thing in the section usually.
    
    # Let's just find the first <div class="gallery"> after "other-works-heading" and replace it until </div> that is followed by </section> or just use greedy?
    # Actually, I can just replace the whole "Other Works" block if I want to be safe.
    
    section_match = re.search(r'(<h3 class="other-works-heading">Other Works</h3>\s*)(<div class="gallery">[\s\S]*?</div>)(\s*</section>)', content)
    if section_match:
         new_content = content[:section_match.start(2)] + gallery_html + content[section_match.end(2):]
         with open(index_path, 'w') as f:
             f.write(new_content)
         print("Updated index.html")
    else:
        print("Could not find gallery section in index.html to update.")

def update_photography(projects):
    if not os.path.exists(photo_html_path):
        print("Error: projects/photography.html not found")
        return

    photo_projects = [p for p in projects if p.get("category") == "photography"]
    
    # Generate HTML
    gallery_html = '<div class="gallery">\n'
    gallery_html += generate_gallery_html(photo_projects, context="subdir")
    gallery_html += """            </div>
            <a href="../index.html#work" class="back-link">← Back to Works</a>"""

    with open(photo_html_path, 'r') as f:
        content = f.read()
        
    # Pattern: <div class="gallery"> ... <a href="../index.html#work"
    # We replace from <div class="gallery"> up to the back link or closing section.
    
    # Let's match <div class="gallery"> ... </div>
    # In photography.html, the gallery div is followed by the back link.
    
    # Regex: (<div class="gallery">[\s\S]*?</div>)(\s*<a href="\.\./index\.html#work")
    # This assumes the closing div is right before the link.
    
    match = re.search(r'(<div class="gallery">[\s\S]*?</div>)(\s*<a href="\.\./index\.html#work")', content)
    
    # Actually, my generator includes the closing div AND the back link. 
    # So I should match both and replace both to be safe, or just the gallery.
    # Let's replace just the gallery content if I can matches it.
    
    # Simpler: Find <section ...> ... <h2>Photography</h2> ... HERE ... </section>
    # Let's just create the file specifically.
    # Reuse the template logic from previous script?
    # No, I want to preserve the header/footer if they change.
    
    # Let's try to match <div class="gallery"> until <a href=...back-link
    
    match = re.search(r'(<div class="gallery">[\s\S]*?)(<a href="\.\./index\.html#work" class="back-link">)', content)
    if match:
        # We need to close the div in generated html? 
        # generate_gallery_html returns string ending with </div>
        # But here I am constructing:
        # gallery_html = <div class="gallery">...</div> + back-link
        
        # So I should replace everything between <h2>Photography</h2> and </section> basically?
        # Let's look at file content again.
        # <section ...> <h2>...</h2> <div class="gallery">...</div> <a ...>...</a> </section>
        
        # Let's target <div class="gallery"> all the way to </a>
        pass
        
    # Allow me to overwrite the whole section content
    start_marker = "<h2>Photography</h2>"
    end_marker = "</section>"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker, start_idx)
    
    if start_idx != -1 and end_idx != -1:
        prefix = content[:start_idx + len(start_marker)]
        suffix = content[end_idx:]
        
        new_middle = "\n" + gallery_html + "\n        "
        new_content = prefix + new_middle + suffix
        
        with open(photo_html_path, 'w') as f:
            f.write(new_content)
        print("Updated projects/photography.html")
    else:
        print("Could not find section to update in photography.html")


if __name__ == "__main__":
    if not os.path.exists(projects_json_path):
        print("projects.json not found. Run bootstrap_projects.py first.")
    else:
        with open(projects_json_path, 'r') as f:
            projects = json.load(f)
            
        update_index(projects)
        update_photography(projects)
