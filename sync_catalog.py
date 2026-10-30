import urllib.request
import os
import sys
import olefile
import xlrd
import sqlite3
import urllib.parse
import time

CATALOG_URL = 'https://kitabosunnat.com/export_books_excel'
EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'books.xls')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kitabosunnat.db')

def sync_catalog():
    print("Connecting to KitaboSunnat to fetch latest catalog...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(CATALOG_URL, headers=headers)
    
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
        
        with open(EXCEL_PATH, 'wb') as f:
            f.write(data)
        print(f"Downloaded books.xls ({len(data)} bytes) in {time.time() - t0:.2f}s.")
    except Exception as e:
        print(f"Failed to download catalog: {e}")
        return False

    print("Importing into database...")
    try:
        ole = olefile.OleFileIO(EXCEL_PATH)
        stream = ole.openstream('Workbook').read()
        wb = xlrd.open_workbook(file_contents=stream)
        sheet = wb.sheet_by_index(0)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        existing_serials = set(r[0] for r in c.execute('SELECT serial_no FROM books').fetchall())
        new_books = 0

        for r in range(1, sheet.nrows):
            s_no_raw = sheet.cell_value(r, 0)
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

            if not title or serial_no in existing_serials:
                continue

            encoded_title = urllib.parse.quote(title)
            search_url = f"https://kitabosunnat.com/get-searched-book?searchword={encoded_title}"
            num_search_url = f"https://kitabosunnat.com/get-searched-book-by-number?searchword={serial_no}"
            archive_url = f"https://archive.org/search?query={encoded_title}"

            c.execute('''
                INSERT INTO books (serial_no, title, author, publisher, kitabosunnat_url, search_url, archive_search_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (serial_no, title, author, publisher, num_search_url, search_url, archive_url))
            new_books += 1

        conn.commit()
        total = c.execute('SELECT COUNT(*) FROM books').fetchone()[0]
        conn.close()

        print(f"Sync complete! Added {new_books} new books. Total books: {total}.")
        return True
    except Exception as e:
        print(f"Error parsing/importing catalog: {e}")
        return False

if __name__ == '__main__':
    sync_catalog()
