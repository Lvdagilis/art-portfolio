# Lukas V. Dagilis - Portfolio Website

A clean, modern portfolio website showcasing new media art, interaction design, photography, and installations.

## Hosting on GitHub Pages

To host this website for free on GitHub Pages:

1. **Create a new GitHub repository**
   - Go to [github.com](https://github.com) and create a new repository
   - Name it `portfolio` or `your-username.github.io` for a personal site
   - Keep it public

2. **Initialize git and push your code**
   ```bash
   cd "/Users/lukas/Documents/Python/portfolio website"
   git init
   git add .
   git commit -m "Initial commit: Portfolio website"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
   git push -u origin main
   ```

3. **Enable GitHub Pages**
   - Go to your repository settings
   - Navigate to "Pages" in the left sidebar
   - Under "Source", select "main" branch
   - Click "Save"
   - Your site will be available at `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/`

## Customizing the Website

### Update Personal Information

1. **Edit index.html**
   - Update the hero section title and description
   - Update the email address in the contact section
   - Add/remove gallery items as needed
   - Update project titles and descriptions

2. **Add More Images**
   - Place images in the `images/` folder
   - Reference them in index.html using `images/your-image.jpg`
   - Recommended image size: 1200-2000px wide

3. **Customize Colors**
   - Edit `style.css` to change colors, fonts, and layout
   - Main color variables are in the CSS file

## Local Testing

To view the website locally before deploying:

1. **Simple method**: Just open `index.html` in your web browser

2. **With a local server** (recommended for testing):
   ```bash
   # Python 3
   python3 -m http.server 8000

   # Then open http://localhost:8000 in your browser
   ```

## File Structure

```
portfolio website/
├── index.html          # Main HTML file
├── style.css           # Stylesheet
├── images/             # Portfolio images
│   ├── installation-jars.jpg
│   ├── church-projection.jpg
│   ├── couple-by-water.jpg
│   ├── landscape-mountains.jpg
│   └── portrait.jpg
└── README.md           # This file
```

## Content

The website features:
- 12+ projects including interactive installations, projection design, and photography
- Real project descriptions extracted from your original WordPress site
- Press mentions and links
- Social media links (LinkedIn, Instagram, Vimeo, YouTube)
- Contact information

## Features

- Responsive design (works on mobile and desktop)
- Clean, minimalist aesthetic
- Mixed gallery with images and text-only project cards
- Sticky navigation
- Fast loading with lazy image loading
- No dependencies or frameworks needed
- SEO-friendly with proper meta tags

## Adding More Projects

To add a new project with an image:

```html
<div class="gallery-item">
    <img src="images/your-image.jpg" alt="Project description" loading="lazy">
    <div class="gallery-info">
        <h3>Project Title</h3>
        <p>Brief description</p>
    </div>
</div>
```

To add a text-only project:

```html
<div class="gallery-item">
    <div class="gallery-placeholder">
        <h3>Project Title</h3>
        <p class="project-desc">Detailed project description goes here...</p>
    </div>
</div>
```

## Notes

- The `.gitignore` file excludes the original WordPress folders (`wordpress/` and `lvd/`) from being uploaded to GitHub
- Only the 5 selected portfolio images are included in the `images/` folder
- Additional project images can be added from the `lvdagilis site/` folder if needed

## License

All images and content belong to Lukas Vytautas Dagilis.
