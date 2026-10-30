import os
import sys
import time
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import sqlite3
import olefile
import xlrd
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, 'books.xls')
SITEMAP_PATH = os.path.join(BASE_DIR, 'images-sitemap.xml')
DB_PATH = os.path.join(BASE_DIR, 'kitabosunnat.db')

EXCEL_URL = 'https://kitabosunnat.com/export_books_excel'
SITEMAP_URL = 'https://kitabosunnat.com/images-sitemap.xml'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def normalize(text):
    if not text:
        return ""
    text = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]', '', text)
    text = re.sub(r'[\u0622\u0623\u0625\u0671]', '\u0627', text)
    text = re.sub(r'[\u0649\u06CC]', '\u064A', text)
    text = re.sub(r'[\u06C1\u06C2\u06C3\u0629]', '\u0647', text)
    text = re.sub(r'[\u06A9]', '\u0643', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def download_file(url, dest_path, description):
    print(f"Downloading latest {description} from {url}...")
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=45) as resp:
            content = resp.read()
        
        # Write only if non-empty
        if len(content) > 1000:
            with open(dest_path, 'wb') as f:
                f.write(content)
            print(f"Successfully updated {description} ({len(content)/1024:.1f} KB) in {time.time() - t0:.2f}s.")
            return True
        else:
            print(f"Warning: Downloaded content for {description} is too small ({len(content)} bytes), keeping existing.")
            return False
    except Exception as e:
        print(f"Notice: Could not download {description} ({e}). Using existing local file if available.")
        return False

def parse_sitemap(sitemap_path):
    if not os.path.exists(sitemap_path):
        print(f"Sitemap file not found at {sitemap_path}")
        return []

    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing sitemap XML: {e}")
        return []

    sitemap_items = []
    for u in root:
        loc_elem = u.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        page_url = loc_elem.text if loc_elem is not None else ""
        imgs = u.findall('{http://www.google.com/schemas/sitemap-image/1.1}image')
        for img in imgs:
            img_title_elem = img.find('{http://www.google.com/schemas/sitemap-image/1.1}title')
            raw_title = img_title_elem.text if img_title_elem is not None and img_title_elem.text else ""
            if '|' in raw_title:
                eng_part, urdu_part = raw_title.split('|', 1)
                eng_name = eng_part.strip()
                urdu_name = urdu_part.strip()
            else:
                eng_name = raw_title.strip()
                urdu_name = raw_title.strip()
            
            sitemap_items.append({
                'page_url': page_url,
                'eng_name': eng_name,
                'urdu_name': urdu_name,
                'norm_urdu': normalize(urdu_name)
            })

    print(f"Parsed {len(sitemap_items)} sitemap entries from {sitemap_path}.")
    return sitemap_items

def sync():
    print("=== KitaboSunnat Catalog Synchronizer ===")
    
    # 1. Fetch latest Excel and Sitemap
    download_file(EXCEL_URL, EXCEL_PATH, "books.xls")
    download_file(SITEMAP_URL, SITEMAP_PATH, "images-sitemap.xml")

    # 2. Parse Sitemap
    sitemap_items = parse_sitemap(SITEMAP_PATH)

    # 3. Read Excel catalog
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: {EXCEL_PATH} does not exist.")
        return

    ole = olefile.OleFileIO(EXCEL_PATH)
    stream = ole.openstream('Workbook').read()
    wb = xlrd.open_workbook(file_contents=stream)
    sheet = wb.sheet_by_index(0)

    # 4. Open SQLite Database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure table and columns exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_no TEXT UNIQUE,
            title TEXT NOT NULL,
            author TEXT,
            publisher TEXT,
            slug TEXT,
            kitabosunnat_url TEXT,
            search_url TEXT,
            archive_search_url TEXT,
            local_pdf TEXT,
            download_url TEXT
        )
    ''')
    cols = [col[1] for col in c.execute("PRAGMA table_info(books)").fetchall()]
    if 'download_url' not in cols:
        c.execute("ALTER TABLE books ADD COLUMN download_url TEXT")

    # Index existing books by serial_no
    db_books = {}
    for row in c.execute("SELECT id, serial_no, title, author, publisher, kitabosunnat_url, download_url FROM books").fetchall():
        db_books[row[1]] = {
            'id': row[0],
            'serial_no': row[1],
            'title': row[2],
            'author': row[3],
            'publisher': row[4],
            'kitabosunnat_url': row[5],
            'download_url': row[6]
        }

    # Insert any new books from Excel
    new_books_count = 0
    excel_books_list = []

    for r in range(1, sheet.nrows):
        s_raw = sheet.cell_value(r, 0)
        if isinstance(s_raw, float):
            serial = str(int(s_raw)) if s_raw.is_integer() else f"{s_raw:.2f}".rstrip('0').rstrip('.')
        else:
            serial = str(s_raw).strip()
        
        title = str(sheet.cell_value(r, 1)).strip()
        author = str(sheet.cell_value(r, 2)).strip()
        publisher = str(sheet.cell_value(r, 3)).strip()

        if not title:
            continue

        excel_books_list.append({
            'serial': serial,
            'title': title,
            'author': author,
            'publisher': publisher,
            'norm_title': normalize(title)
        })

        if serial not in db_books:
            encoded_title = urllib.parse.quote(title)
            default_page = f"https://kitabosunnat.com/get-searched-book-by-number?searchword={serial}"
            search_url = f"https://kitabosunnat.com/get-searched-book?searchword={encoded_title}"
            archive_url = f"https://archive.org/search?query={encoded_title}"

            c.execute('''
                INSERT INTO books (serial_no, title, author, publisher, kitabosunnat_url, search_url, archive_search_url, download_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            ''', (serial, title, author, publisher, default_page, search_url, archive_url))

            db_books[serial] = {
                'id': c.lastrowid,
                'serial_no': serial,
                'title': title,
                'author': author,
                'publisher': publisher,
                'kitabosunnat_url': default_page,
                'download_url': None
            }
            new_books_count += 1

    conn.commit()
    print(f"Excel inspection: {len(excel_books_list)} books found in Excel. Inserted {new_books_count} new books into DB.")

    # 5. Build sitemap lookup
    # Group Excel books by title and norm_title, sorted by serial ascending
    excel_by_clean = defaultdict(list)
    excel_by_norm = defaultdict(list)
    for b in excel_books_list:
        excel_by_clean[b['title'].strip()].append(b)
        excel_by_norm[b['norm_title']].append(b)

    for k in excel_by_clean:
        excel_by_clean[k].sort(key=lambda x: float(x['serial']) if x['serial'].replace('.','',1).isdigit() else 999999)
    for k in excel_by_norm:
        excel_by_norm[k].sort(key=lambda x: float(x['serial']) if x['serial'].replace('.','',1).isdigit() else 999999)

    matched_from_sitemap = {}
    for sm in sitemap_items:
        candidates = excel_by_clean.get(sm['urdu_name']) or excel_by_norm.get(sm['norm_urdu'])
        if not candidates:
            sub = re.sub(r'\(.*?\)', '', sm['urdu_name']).strip()
            candidates = excel_by_clean.get(sub) or excel_by_norm.get(normalize(sub))
        
        if not candidates:
            continue

        chosen = None
        for cand in candidates:
            if cand['serial'] not in matched_from_sitemap:
                chosen = cand
                break
        if not chosen:
            chosen = candidates[0]

        matched_from_sitemap[chosen['serial']] = sm

    # 6. Check all books in DB: if download_url is missing, check if sitemap now has it!
    newly_resolved_links = 0
    updates = []

    for serial, sm in matched_from_sitemap.items():
        existing = db_books.get(serial)
        if not existing:
            continue

        # If download_url was missing, or page was fallback searchword
        if not existing['download_url'] or 'searchword=' in str(existing['kitabosunnat_url']):
            page_url = sm['page_url']
            eng_name = sm['eng_name']

            inner_pdf_url = f"https://books.kitabosunnat.com/Books_Data/{serial}/{urllib.parse.quote(eng_name)}.pdf"
            download_url = f"https://kitabosunnat.com/download-book-pdf?url={urllib.parse.quote(inner_pdf_url, safe='')}"

            updates.append((page_url, download_url, serial))
            newly_resolved_links += 1

    if updates:
        c.executemany("UPDATE books SET kitabosunnat_url = ?, download_url = ? WHERE serial_no = ?", updates)
        conn.commit()
        print(f"Updated {len(updates)} books with new direct book page and PDF download links!")

    # 7. Summary counts
    total_books = c.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    direct_pdfs = c.execute("SELECT COUNT(*) FROM books WHERE download_url IS NOT NULL AND download_url != ''").fetchone()[0]
    conn.close()

    print(f"\nSync complete!")
    print(f"  Total books in catalog: {total_books}")
    print(f"  Books with direct PDF links: {direct_pdfs} ({direct_pdfs/total_books*100:.1f}%)")
    print(f"  New books added in this run: {new_books_count}")
    print(f"  Previously missing links newly resolved: {newly_resolved_links}")

    # 8. Rebuild data/books.json
    print("\nRegenerating data/books.json...")
    import build_json
    build_json.generate_json_from_db()

if __name__ == '__main__':
    sync()
