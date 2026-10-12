import os
import shutil
import re
import sys
import html
from html.parser import HTMLParser

# Configuration
SOURCE_DIRS = [
    "lvdagilis site",
    "lvdagilis site/photos"
]
base_dir = os.getcwd()
projects_dir = os.path.join(base_dir, "projects")
images_dir = os.path.join(base_dir, "images", "projects")

# Ensure directories exist
os.makedirs(projects_dir, exist_ok=True)
os.makedirs(images_dir, exist_ok=True)

def simple_slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

class SimpleModuleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.modules = []
        self.current_module = None
        self.depth = 0
        self.module_depth = -1
        self.capture_text = False
        self.text_accumulator = []
        
        self.title = None
        self.description = None

    def handle_starttag(self, tag, attrs):
        self.depth += 1
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "").split()

        # Meta data
        if tag == "meta" and attrs_dict.get("property") == "og:title":
            t = attrs_dict.get("content")
            if t: self.title = t.replace("Lukas V. Dagilis - ", "")
        if tag == "meta" and attrs_dict.get("name") == "description":
            self.description = attrs_dict.get("content")

        # Start Module
        if "project-module" in classes:
            # We don't support nested modules well, but they are usually siblings
            self.module_depth = self.depth
            m_type = "unknown"
            if "project-module-image" in classes: m_type = "image"
            elif "project-module-text" in classes: m_type = "text"
            elif "project-module-video" in classes: m_type = "video"
            elif "project-module-embed" in classes: m_type = "embed"
            elif "project-module-audio" in classes: m_type = "audio"
            
            self.current_module = {'type': m_type, 'content': {}, 'raw_text': []}
            self.modules.append(self.current_module)
        
        # Inside Module
        if self.current_module and self.depth >= self.module_depth:
            # Image
            if tag == "img" and self.current_module['type'] == 'image':
                 # Get highest res src
                 src = attrs_dict.get("src")
                 # Check valid local
                 if src and "_files/" in src:
                     self.current_module['content']['src'] = src
            
            # Text / Caption
            if "rich-text" in classes:
                self.capture_text = True
            
            # Video
            if tag == "iframe":
                self.current_module['content']['src'] = attrs_dict.get("src")
                if self.current_module['type'] == 'unknown':
                     self.current_module['type'] = 'video'

    def handle_endtag(self, tag):
        if self.current_module and self.depth == self.module_depth:
            # Closing the module div
            if self.capture_text:
                # Flush text
                pass # text is accumulated in handle_data
            
            # Process accumulated text
            full_text = "".join(self.current_module['raw_text']).strip()
            if self.current_module['type'] == 'text':
                self.current_module['content']['text'] = full_text
            elif self.current_module['type'] == 'image':
                self.current_module['content']['caption'] = full_text

            self.current_module = None
            self.module_depth = -1
            self.capture_text = False
        
        self.depth -= 1

    def handle_data(self, data):
        if self.current_module and self.capture_text:
            # We want to preserve structure but strip excessive whitespace?
            # actually better to keep it raw-ish but maybe stripped 
            # The simple parser here flattens structure. 
            # For rich text, we ideally want inner HTML. But HTMLParser doesn't give that easily.
            # We'll just extract text.
            self.current_module['raw_text'].append(data)

def migrate_project(html_path):
    print(f"Processing: {html_path}")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    parser = SimpleModuleParser()
    try:
        parser.feed(content)
    except Exception as e:
        print(f"Error parsing {html_path}: {e}")
        return None

    title = parser.title
    # Fallback title
    if not title:
        match = re.search(r'<title>(.*?)</title>', content)
        if match:
             title = match.group(1).replace("Lukas V. Dagilis - ", "")
    if not title:
        title = os.path.splitext(os.path.basename(html_path))[0].replace("Lukas V. Dagilis - ", "")
    
    # HTML Unescape title
    if title:
        title = html.unescape(title)
        
    slug = simple_slugify(title)
    description = parser.description if parser.description else ""

    html_dir = os.path.dirname(html_path)
    
    # Process extracted modules
    valid_modules = []
    has_valid_images = False
    
    # Setup Image Directory
    project_img_dir = os.path.join(images_dir, slug)
    os.makedirs(project_img_dir, exist_ok=True)
    img_counter = 1
    main_image_path = None

    for m in parser.modules:
        if m['type'] == 'image':
            src = m['content'].get('src')
            if src:
                src = src.replace("%20", " ")
                local_path = os.path.join(html_dir, src) if not os.path.isabs(src) else src
                
                if os.path.exists(local_path):
                    has_valid_images = True
                    # Copy image
                    ext = os.path.splitext(local_path)[1]
                    new_filename = f"image-{img_counter}{ext}"
                    dest_path = os.path.join(project_img_dir, new_filename)
                    shutil.copy2(local_path, dest_path)
                    
                    web_path = f"../images/projects/{slug}/{new_filename}"
                    m['content']['web_src'] = web_path
                    if not main_image_path: main_image_path = web_path
                    img_counter += 1
                else:
                    m['content']['error'] = True # Image missing locally
            else:
                 m['content']['error'] = True # No src extracted
        
        valid_modules.append(m)

    # Fallback Logic: If no images found in HTML modules, scan directory
    if not has_valid_images:
        print(f"  No valid images in HTML. Scanning directory...")
        basename = os.path.basename(html_path)
        files_dir_name = os.path.splitext(basename)[0] + "_files"
        files_dir = os.path.join(html_dir, files_dir_name)
        
        if os.path.exists(files_dir):
            fallback_images = []
            for filename in sorted(os.listdir(files_dir)):
                 if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                     fallback_images.append(os.path.join(files_dir, filename))
            
            # Dedup logic for fallback
            def get_image_info(path):
                # Supports UUID (36) and shorter IDs (20+) matches
                match = re.search(r'([a-f0-9-]{20,})(?:_rw_(\d+))?\.jpg$', path)
                if match:
                     return match.group(1), int(match.group(2)) if match.group(2) else 0
                return path, 0

            best_images = {}
            ordered_ids = []
            for img_path in fallback_images:
                content_id, res = get_image_info(img_path)
                if content_id not in best_images:
                    ordered_ids.append(content_id)
                    best_images[content_id] = (res, img_path)
                else:
                    if res > best_images[content_id][0]:
                        best_images[content_id] = (res, img_path)
            
            unique_fallback = [best_images[cid][1] for cid in ordered_ids]
            
            for img_path in unique_fallback:
                ext = os.path.splitext(img_path)[1]
                new_filename = f"image-{img_counter}{ext}"
                dest_path = os.path.join(project_img_dir, new_filename)
                shutil.copy2(img_path, dest_path)
                
                web_path = f"../images/projects/{slug}/{new_filename}"
                # Create a synthetic image module
                valid_modules.append({
                    'type': 'image',
                    'content': {'web_src': web_path, 'caption': ''}
                })
                if not main_image_path: main_image_path = web_path
                img_counter += 1

    if not main_image_path:
        main_image_path = "images/placeholder.jpg" 

    # Generate HTML Page
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Lukas V. Dagilis</title>
    <meta name="description" content="{description}">
    <link rel="stylesheet" href="../style.css">
    <style>
        .project-content {{
            max-width: 800px;
            margin: 4rem auto;
            padding: 0 1rem;
            line-height: 1.6;
        }}
        .project-header {{
            margin-bottom: 3rem;
            text-align: center;
        }}
        .project-header h1 {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }}
        .project-description {{
             font-size: 1.2rem;
             color: #444;
             margin-bottom: 2rem;
        }}
        .project-module {{
            margin-bottom: 2rem;
        }}
        .project-module img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .module-text {{
            font-size: 1.1rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }}
        .project-caption {{
            font-size: 0.9rem;
            color: #666;
            margin-top: 0.5rem;
            text-align: center;
            font-style: italic;
        }}
        .video-container {{
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
        }}
        .video-container iframe {{
             position: absolute;
             top: 0; left: 0; width: 100%; height: 100%;
        }}
        .back-link {{
            display: block;
            margin-top: 4rem;
            text-align: center;
            font-weight: bold;
            color: #333;
            text-decoration: none;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <header>
        <nav>
            <h1><a href="../index.html">Lukas Vytautas Dagilis</a></h1>
            <ul>
                <li><a href="../index.html#work">Work</a></li>
                <li><a href="../index.html#about">About</a></li>
                <li><a href="../index.html#contact">Contact</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <section class="project-content">
            <header class="project-header">
                <h1>{title}</h1>
                <p class="project-description">{description}</p>
            </header>
            
            <div class="project-modules">
"""
    
    for m in valid_modules:
        if m['type'] == 'text':
            text = m['content'].get('text', '')
            if text:
                html_content += f'<div class="project-module module-text">{text}</div>\n'
        
        elif m['type'] == 'image':
            web_src = m['content'].get('web_src')
            caption = m['content'].get('caption', '')
            if web_src:
                html_content += f'<div class="project-module">\n'
                html_content += f'  <img src="{web_src}" alt="{title}" loading="lazy">\n'
                if caption:
                    html_content += f'  <div class="project-caption">{caption}</div>\n'
                html_content += f'</div>\n'
        
        elif m['type'] == 'video':
            src = m['content'].get('src')
            if src:
                html_content += f'<div class="project-module">\n'
                html_content += f'  <div class="video-container"><iframe src="{src}" frameborder="0" allowfullscreen></iframe></div>\n'
                html_content += f'</div>\n'

    html_content += """
            </div>
            <a href="../index.html#work" class="back-link">← Back to Works</a>
        </section>
    </main>

    <footer>
        <p>&copy; 2025 Lukas Vytautas Dagilis. All rights reserved.</p>
    </footer>
</body>
</html>
"""
    
    dest_html_path = os.path.join(projects_dir, f"{slug}.html")
    with open(dest_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return {
        "title": title,
        "slug": slug,
        "path": f"projects/{slug}.html",
        "image": main_image_path
    }

def main():
    projects_found = []
    
    # 1. Scan direct HTML files
    for relative_dir in SOURCE_DIRS:
        search_dir = os.path.join(base_dir, relative_dir)
        if not os.path.exists(search_dir): continue
        print(f"Scanning directory: {search_dir}")
        for filename in sorted(os.listdir(search_dir)):
            if filename.endswith(".html") and not filename.startswith("index"):
                filepath = os.path.join(search_dir, filename)
                files_dir = filepath.replace(".html", "_files")
                sub_dir_check = os.path.join(search_dir, os.path.splitext(filename)[0])
                if os.path.exists(files_dir) or os.path.exists(sub_dir_check):
                    try:
                        result = migrate_project(filepath)
                        if result and not any(p['slug'] == result['slug'] for p in projects_found):
                            projects_found.append(result)
                    except Exception as e:
                        print(f"Failed {filename}: {e}")

    # 2. Dynamic scan of subdirectories
    root_site_dir = os.path.join(base_dir, "lvdagilis site")
    if os.path.exists(root_site_dir):
        print(f"Scanning subdirectories in: {root_site_dir}")
        for item in sorted(os.listdir(root_site_dir)):
            item_path = os.path.join(root_site_dir, item)
            # Must be a directory, skip 'photos' (already scanned), 'about', and hidden files
            if os.path.isdir(item_path) and item != "photos" and item != "about" and not item.startswith("."):
                html_candidates = [f for f in os.listdir(item_path) if f.endswith(".html") and not f.startswith("index")]
                if html_candidates:
                    best_candidate = max(html_candidates, key=len)
                    filepath = os.path.join(item_path, best_candidate)
                    try:
                        result = migrate_project(filepath)
                        if result and not any(p['slug'] == result['slug'] for p in projects_found):
                            projects_found.append(result)
                    except Exception as e:
                        print(f"Failed {item}/{best_candidate}: {e}")
                else:
                    # Strategy 3: Image-only folder (e.g. Once Upon an Artist)
                    # Check if there are images
                    images = [f for f in os.listdir(item_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                    if images:
                        print(f"Processing image-only folder: {item}")
                        try:
                            # Create a synthetic project from directory
                            title = item
                            slug = simple_slugify(title)
                            
                            # Prepare destination
                            project_img_dir = os.path.join(images_dir, slug)
                            os.makedirs(project_img_dir, exist_ok=True)
                            
                            valid_modules = []
                            main_image_path = None
                            
                            # Copy all images
                            for i, filename in enumerate(sorted(images)):
                                src_path = os.path.join(item_path, filename)
                                ext = os.path.splitext(filename)[1]
                                new_filename = f"image-{i+1}{ext}"
                                dest_path = os.path.join(project_img_dir, new_filename)
                                shutil.copy2(src_path, dest_path)
                                
                                web_path = f"../images/projects/{slug}/{new_filename}"
                                valid_modules.append({
                                    'type': 'image', 
                                    'content': {'web_src': web_path, 'caption': ''}
                                })
                                if not main_image_path: main_image_path = web_path
                            
                            # Generate simple HTML
                            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Lukas V. Dagilis</title>
    <link rel="stylesheet" href="../style.css">
    <style>
        .project-content {{ max-width: 800px; margin: 4rem auto; padding: 0 1rem; line-height: 1.6; }}
        .project-header {{ margin-bottom: 3rem; text-align: center; }}
        .project-header h1 {{ font-size: 2.5rem; margin-bottom: 1rem; }}
        .project-module {{ margin-bottom: 2rem; }}
        .project-module img {{ width: 100%; height: auto; display: block; }}
        .back-link {{ display: block; margin-top: 4rem; text-align: center; font-weight: bold; color: #333; text-decoration: none; }}
        .back-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <header>
        <nav>
            <h1><a href="../index.html">Lukas Vytautas Dagilis</a></h1>
            <ul>
                <li><a href="../index.html#work">Work</a></li>
                <li><a href="../index.html#about">About</a></li>
                <li><a href="../index.html#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    <main>
        <section class="project-content">
            <header class="project-header"><h1>{title}</h1></header>
            <div class="project-modules">
"""
                            for m in valid_modules:
                                web_src = m['content'].get('web_src')
                                html_content += f'<div class="project-module"><img src="{web_src}" alt="{title}" loading="lazy"></div>\n'
                                
                            html_content += """
            </div>
            <a href="../index.html#work" class="back-link">← Back to Works</a>
        </section>
    </main>
    <footer><p>&copy; 2025 Lukas Vytautas Dagilis. All rights reserved.</p></footer>
</body>
</html>
"""
                            dest_html_path = os.path.join(projects_dir, f"{slug}.html")
                            with open(dest_html_path, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                                
                            result = {
                                "title": title,
                                "slug": slug,
                                "path": f"projects/{slug}.html",
                                "image": main_image_path
                            }
                            if not any(p['slug'] == result['slug'] for p in projects_found):
                                projects_found.append(result)

                        except Exception as e:
                            print(f"Failed image-only {item}: {e}")

    print(f"Migrated {len(projects_found)} projects.")
    projects_found.sort(key=lambda x: x['title'])
    
    print("\n--- HTML Snippet for index.html ---")
    print('<div class="gallery">')
    for p in projects_found:
        thumb_path = p['image'].replace("../", "")
        print(f"""    <div class="gallery-item">
        <a href="{p['path']}">
            <img src="{thumb_path}" alt="{p['title']}" loading="lazy">
            <div class="gallery-info">
                <h3>{p['title']}</h3>
            </div>
        </a>
    </div>""")
    print('</div>')

if __name__ == "__main__":
    main()
