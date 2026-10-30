# 📚 Better KitaboSunnat (بہتر کتاب و سنت)

[![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-blue?logo=github)](https://pages.github.com/)
[![Search Engine](https://img.shields.io/badge/Search-Zero--Latency%20Client--Side-brightgreen)](index.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Catalog Sync](https://img.shields.io/badge/Catalog%20Sync-Automated%20Weekly-orange)](.github/workflows/sync-catalog.yml)

A high-performance, modern, open-source search engine and library interface for **[KitaboSunnat.com](https://kitabosunnat.com/)** (کتاب و سنت لائبریری / محدث میڈیا), engineered to run **100% free on GitHub Pages** with zero server costs or backend infrastructure.

KitaboSunnat hosts over **9,300+ free Islamic books**, but its web search often crashes or times out. **Better KitaboSunnat** solves this by loading an indexed catalog directly into the browser, enabling **instant search (< 5ms)**, one-click redirects to official download pages, and automated weekly catalog updates.

---

## 🌟 Live Demo on GitHub Pages

Once deployed, your website will be accessible globally via:
```
https://<YOUR-GITHUB-USERNAME>.github.io/Better-KitaboSunnat/
```

---

## ✨ Features

- 🌐 **100% Free GitHub Pages Hosting:** Zero backend servers, zero databases to manage, zero hosting bills.
- ⚡ **Zero-Lag Search (< 5ms):** Fast client-side search across 9,300+ books with Arabic/Urdu character normalization (ignores Tashkeel/diacritics, unifies Alif/Yeh/Heh).
- 🎨 **Modern Urdu Interface:** Clean Right-to-Left (RTL) layout with Google Noto Nastaliq Urdu typography and Tailwind CSS.
- 🎯 **Multi-Field Filtering:** Search by Book Title (`نامِ کتاب`), Author (`مصنف`), Publisher (`ناشر`), or Book ID (`#113`).
- 🔗 **Smart One-Click Actions:**
  - **کتاب و سنت صفحہ:** Opens the exact book on KitaboSunnat directly, bypassing their broken search.
  - **ڈاؤن لوڈ صفحہ:** Instant redirect to KitaboSunnat's official download page.
  - **Archive.org آئینہ:** Direct high-speed download mirrors on Internet Archive.
  - **لنک کاپی کریں:** One-click copy book URL to clipboard.
- 🔄 **Self-Updating Catalog:** Includes a GitHub Action workflow that checks KitaboSunnat every week, adds any newly uploaded books to `data/books.json`, and automatically redeploys GitHub Pages!

---

## 🚀 How to Deploy to GitHub Pages (2 Minutes)

### Step 1: Create a GitHub Repository
1. Go to [github.com/new](https://github.com/new) and create a repository named **`Better-KitaboSunnat`**.
2. Leave it empty (do NOT check "Add a README file").

### Step 2: Push this Repository
From this directory (`Better-KitaboSunnat`):
```bash
git remote add origin https://github.com/<YOUR-USERNAME>/Better-KitaboSunnat.git
git push -u origin main
```

### Step 3: Enable GitHub Pages
1. On GitHub, go to your repository **Settings** ➔ **Pages** (in the left sidebar).
2. Under **Build and deployment** ➔ **Source**:
   * Select **GitHub Actions** (the included workflow will build and publish automatically!).
   * *(Alternatively: select "Deploy from a branch" ➔ `main` ➔ `/ (root)`).*
3. Within 1 minute, your site will be live at:
   ```
   https://<YOUR-USERNAME>.github.io/Better-KitaboSunnat/
   ```

---

## 🔄 How the Self-Updating Catalog Works

KitaboSunnat updates their catalog export at `https://kitabosunnat.com/export_books_excel`.

You don't need to manually update anything:
* **Automated Weekly Sync ([`.github/workflows/sync-catalog.yml`](.github/workflows/sync-catalog.yml)):**
  Every Sunday at 02:00 UTC, a GitHub Action runs automatically. It downloads the newest catalog from KitaboSunnat, runs `sync_catalog.py` and `build_json.py`, commits any new books to `data/books.json`, and triggers a fresh deployment of your GitHub Pages site!
* **Manual Sync:**
  You can also trigger it anytime from your repository's **Actions** tab by clicking **Run workflow**.

---

## 💻 Optional: Running Locally

If you want to run or test the site locally on your computer:

```bash
# Using Python's built-in web server:
python -m http.server 8000
```
Then visit `http://localhost:8000` in your browser.

---

## 📁 Repository Structure

```
Better-KitaboSunnat/
├── index.html                 # Main static web application (GitHub Pages root)
├── data/
│   └── books.json             # Compact catalog of 9,314 books (~280 KB gzipped)
├── .github/
│   └── workflows/
│       ├── deploy-pages.yml   # Automatic deployment to GitHub Pages
│       └── sync-catalog.yml   # Weekly auto-update of new books from KitaboSunnat
├── build_json.py              # Compiles books into data/books.json
├── sync_catalog.py            # Fetches latest catalog from KitaboSunnat
├── build_database.py          # SQLite FTS5 database builder
├── books.xls                  # Official catalog spreadsheet
├── kitabosunnat.db            # SQLite database
├── requirements.txt           # Python tools dependencies
├── LICENSE                    # MIT License
└── README.md                  # Project documentation
```

---

## ⚖️ Disclaimer & License

This is an open-source research and preservation tool. All scanned texts and contents are distributed freely by **KitaboSunnat.com (مجلس التحقیق الاسلامی، لاہور)**.

Licensed under the [MIT License](LICENSE).
