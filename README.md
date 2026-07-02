# 📂 lejfles / vps

> Personal hub — anything I want to open in a browser lives here.

🌐 **Live site:** https://lejfles.github.io/vps/

## What is this

A static site hosted free on GitHub Pages. The `index.html` is an auto-generated
dashboard that lists every file in this repo — HTML pages, Markdown docs, images,
PDFs — with search and category grouping. Push a file, it shows up.

## How to add content

### Option A — Through GitHub web (easiest)

1. Open https://github.com/lejfles/vps
2. Click **Add file → Upload files** (or **Create new file**)
3. Drop in HTML / MD / images / anything
4. Commit to `main`
5. Refresh https://lejfles.github.io/vps/ — your file appears in the index

### Option B — From your VPS (with SSH key)

```bash
cd ~/lejfles-pages/vps        # the cloned repo
cp /path/to/your-file.html .   # or .md / .png / .pdf
git add .
git commit -m "Add your-file"
git push
```

## File types supported

| Type | Examples | Renders as |
|---|---|---|
| `.html`, `.htm` | Custom pages, exported docs | Opens directly |
| `.md` | Notes, articles | Opens as plain text (raw Markdown) |
| `.png` `.jpg` `.gif` `.webp` `.svg` | Screenshots, images | Opens directly |
| `.pdf` | Documents | Opens in browser viewer |

## Site structure

```
vps/
├── index.html       ← auto-listing dashboard (this site)
├── README.md        ← this file
└── <your files>     ← anything you push
```

## How the index works

`index.html` calls the GitHub REST API (`/repos/lejfles/vps/git/trees`) on every
load, so the dashboard is always in sync with the repo — no build step, no cache.

---

<sub>Built and deployed by Hermes · GitHub Pages · Public repo</sub>