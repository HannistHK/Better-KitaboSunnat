# 📚 Better KitaboSunnat (بہتر کتاب و سنت)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask-green.svg)](https://flask.palletsprojects.com/)
[![SQLite FTS5](https://img.shields.io/badge/search-SQLite%20FTS5-orange.svg)](https://www.sqlite.org/fts5.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Catalog Sync](https://github.com/your-username/Better-KitaboSunnat/actions/workflows/sync-catalog.yml/badge.svg)](https://github.com/your-username/Better-KitaboSunnat/actions/workflows/sync-catalog.yml)

A high-performance, modern, open-source web interface and search engine for **[KitaboSunnat.com](https://kitabosunnat.com/)** (کتاب و سنت لائبریری / محدث میڈیا).

KitaboSunnat hosts the world's largest digital repository of free Islamic books in Urdu and Arabic (over **9,300+ titles**). However, its online search frequently hangs, times out, or fails due to unindexed database queries.

**Better KitaboSunnat** indexes the entire library locally into an **SQLite Full-Text Search (FTS5)** engine, delivering **sub-millisecond search (< 5ms)**, direct one-click download redirects, and automated catalog syncing.

---

## ✨ Features

- ⚡ **Zero-Lag Search (< 5ms):** Instant full-text search across 9,300+ books with prefix matching in Urdu, Arabic, English/Roman, or Book ID.
- 🎨 **Modern Urdu UI:** Clean, responsive Right-to-Left (RTL) interface with Google Noto Nastaliq typography and Tailwind CSS.
- 🎯 **Multi-Field Filtering:** Search and filter by Book Title (`نامِ کتاب`), Author (`مصنف`), Publisher (`ناشر`), or Serial Number (`#113`).
- 🔗 **Smart One-Click Redirects:**
  - **کتاب و سنت پر دیکھیں:** Opens the exact book page on KitaboSunnat directly without navigating their slow search.
  - **ڈاؤن لوڈ صفحہ:** Instant redirect to KitaboSunnat's official download page.
  - **Archive.org آئینہ:** Direct access to Internet Archive high-speed download mirrors.
- 📥 **Local Hard Drive Downloader:** Download books locally into `library_pdfs/` on-demand or in bulk. Once downloaded, an **"آف لائن پڑھیں"** button lets you read directly offline!
- 🔄 **Automated Weekly Sync:** Built-in GitHub Actions workflow and CLI script that automatically fetches new book releases from KitaboSunnat and updates the database.

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Better-KitaboSunnat.git
cd Better-KitaboSunnat
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```

Open your browser at:
```
http://127.0.0.1:5000
```

---

## 🐳 Running with Docker

Run with a single command:
```bash
docker-compose up -d
```
The application will be live at `http://localhost:5000`.

---

## 🔄 How Catalog Updates Work

When new books are uploaded to KitaboSunnat, you have **three easy ways** to update your website:

### Option A: From the Web UI (One-Click)
Click the **"کیٹلاگ اپ ڈیٹ" (Sync Catalog)** button in the top navigation bar. It contacts KitaboSunnat's catalog endpoint in the background and inserts any new books into your SQLite database without restarting the server.

### Option B: Automatic GitHub Actions (Hands-Free)
This repository includes a scheduled GitHub Action ([`.github/workflows/sync-catalog.yml`](.github/workflows/sync-catalog.yml)) that runs **every Sunday at 02:00 UTC**. It:
1. Downloads the latest catalog export from `https://kitabosunnat.com/export_books_excel`.
2. Adds any newly added books into `kitabosunnat.db`.
3. Commits and pushes the updated database directly back to your repository!

### Option C: Via Command Line
Run the sync script directly:
```bash
python sync_catalog.py
```

---

## 💽 Building Your Own Offline Hard Drive

If you want to build a personal offline library of PDFs:

```bash
# Download books by a specific author (e.g. Dr. Israr Ahmed)
python bulk_downloader.py --author "ڈاکٹر اسرار احمد" --limit 25

# Download books matching a query (e.g. Sahih Bukhari)
python bulk_downloader.py --query "صحیح بخاری" --limit 10

# Download latest 50 uploaded books
python bulk_downloader.py --limit 50
```

Downloaded PDFs are stored in `library_pdfs/`, and the web interface automatically detects them and displays an offline reading button.

---

## ☁️ 1-Click Cloud Deployment

### Deploy to Render / Railway / Fly.io
1. Push this repository to your GitHub account.
2. In [Render](https://render.com) or [Railway](https://railway.app), create a new **Web Service** connected to your repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn --bind 0.0.0.0:$PORT app:app`

---

## 📁 Project Structure

```
Better-KitaboSunnat/
├── .github/
│   └── workflows/
│       └── sync-catalog.yml   # Automatic weekly GitHub Action sync
├── templates/
│   └── index.html            # Clean, responsive RTL Urdu web interface
├── library_pdfs/
│   └── .gitkeep              # Folder for local PDF storage
├── app.py                    # Flask web application & REST API
├── build_database.py         # SQLite & FTS5 database builder
├── sync_catalog.py           # Catalog synchronization utility
├── download_manager.py       # In-app background PDF downloader
├── bulk_downloader.py        # Command-line batch PDF downloader
├── test_app.py               # Test suite
├── books.xls                 # Official catalog snapshot (9,314 books)
├── kitabosunnat.db           # Pre-compiled SQLite FTS5 database
├── requirements.txt          # Python dependencies
├── Dockerfile                # Production Docker container
├── docker-compose.yml        # Docker compose specification
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
└── README.md                 # Project documentation
```

---

## ⚖️ Disclaimer & License

This project is an open-source community tool designed to make Islamic literature accessible to researchers and students. All books, scans, and intellectual properties belong to their respective authors and publishers, and are hosted by **KitaboSunnat.com (مجلس التحقیق الاسلامی، لاہور)**.

Distributed under the [MIT License](LICENSE).
