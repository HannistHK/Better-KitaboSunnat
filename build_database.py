import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
import olefile
import xlrd
import urllib.parse
import re
import os

DB_PATH = 'kitabosunnat.db'
EXCEL_PATH = 'books.xls'
SITEMAP_PATH = 'sitemap_urls.txt'

def create_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create books table
    cursor.execute('''
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_no TEXT,
            title TEXT NOT NULL,
            author TEXT,
            publisher TEXT,
            slug TEXT,
            kitabosunnat_url TEXT,
            search_url TEXT,
            archive_search_url TEXT,
            local_pdf TEXT
        )
    ''')

    # Create FTS5 virtual table for lightning-fast search
    cursor.execute('''
        CREATE VIRTUAL TABLE books_fts USING fts5(
            title,
            author,
            publisher,
            serial_no,
            content='books',
            content_rowid='id'
        )
    ''')

    # Triggers to keep FTS in sync
    cursor.execute('''
        CREATE TRIGGER books_ai AFTER INSERT ON books BEGIN
            INSERT INTO books_fts(rowid, title, author, publisher, serial_no)
            VALUES (new.id, new.title, new.author, new.publisher, new.serial_no);
        END;
    ''')

    # Read slugs from sitemap
    slug_map = {}
    if os.path.exists(SITEMAP_PATH):
        with open(SITEMAP_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                u = line.strip()
                if u:
                    parts = u.replace('https://kitabosunnat.com/kutub-library/', '').split('/')
                    if len(parts) == 1:
                        raw_slug = parts[0]
                        decoded_slug = urllib.parse.unquote(raw_slug).strip().lower()
                        slug_map[decoded_slug] = u

    # Read Excel
    ole = olefile.OleFileIO(EXCEL_PATH)
    stream = ole.openstream('Workbook').read()
    wb = xlrd.open_workbook(file_contents=stream)
    sheet = wb.sheet_by_index(0)

    rows_to_insert = []
    for r in range(1, sheet.nrows):
        s_no_raw = sheet.cell_value(r, 0)
        # Format serial number cleanly (e.g., 113 instead of 113.0, but keep 7967.01)
        if isinstance(s_no_raw, float):
            if s_no_raw.is_integer():
                serial_no = str(int(s_no_raw))
            else:
                serial_no = f"{s_no_raw:.2f}".rstrip('0').rstrip('.')
        else:
            serial_no = str(s_no_raw).strip()

        title = str(sheet.cell_value(r, 1)).strip()
        author = str(sheet.cell_value(r, 2)).strip()
        publisher = str(sheet.cell_value(r, 3)).strip()

        if not title:
            continue

        # Clean search URL
        encoded_title = urllib.parse.quote(title)
        search_url = f"https://kitabosunnat.com/get-searched-book?searchword={encoded_title}"
        num_search_url = f"https://kitabosunnat.com/get-searched-book-by-number?searchword={serial_no}"
        archive_url = f"https://archive.org/search?query={urllib.parse.quote(title)}"

        # Default kitabosunnat_url to number search if direct slug not known yet
        kitabosunnat_url = num_search_url

        rows_to_insert.append((
            serial_no,
            title,
            author,
            publisher,
            None, # slug
            kitabosunnat_url,
            search_url,
            archive_url,
            None # local_pdf
        ))

    cursor.executemany('''
        INSERT INTO books (serial_no, title, author, publisher, slug, kitabosunnat_url, search_url, archive_search_url, local_pdf)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', rows_to_insert)

    conn.commit()

    # Index on author, publisher, serial_no
    cursor.execute('CREATE INDEX idx_books_serial ON books(serial_no)')
    cursor.execute('CREATE INDEX idx_books_author ON books(author)')
    cursor.execute('CREATE INDEX idx_books_publisher ON books(publisher)')

    count = cursor.execute('SELECT COUNT(*) FROM books').fetchone()[0]
    print(f"Successfully populated database with {count} books.")

    # Test an FTS search
    test_queries = ['قرآن', 'بخاری', 'سیالکوٹی', 'ابراہیم']
    for q in test_queries:
        res = cursor.execute('''
            SELECT b.id, b.serial_no, b.title, b.author 
            FROM books_fts f
            JOIN books b ON f.rowid = b.id
            WHERE books_fts MATCH ?
            LIMIT 3
        ''', (q,)).fetchall()
        print(f"\nSearch '{q}' returned {len(res)} sample matches:")
        for r in res:
            print(f"  #{r[1]} - {r[2]} ({r[3]})")

    conn.close()

if __name__ == '__main__':
    create_db()
