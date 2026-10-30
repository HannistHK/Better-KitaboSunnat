import os
import sys
import argparse
import sqlite3
import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import re

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library_pdfs')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kitabosunnat.db')
os.makedirs(PDF_DIR, exist_ok=True)

def get_links_for_book(serial_no):
    search_url = f"https://kitabosunnat.com/get-searched-book-by-number?searchword={serial_no}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    book_page_url = None
    pdf_urls = []
    
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/kutub-library/' in href:
                    parts = href.replace('https://kitabosunnat.com/kutub-library/', '').split('/')
                    if len(parts) == 1 and parts[0] != 'kutub-library':
                        book_page_url = href
                        break
    except Exception as e:
        pass

    if book_page_url:
        try:
            req2 = urllib.request.Request(urllib.parse.quote(book_page_url, safe=':/?=&'), headers=headers)
            with urllib.request.urlopen(req2, timeout=20) as resp2:
                p_html = resp2.read().decode('utf-8', errors='ignore')
                p_soup = BeautifulSoup(p_html, 'html.parser')
                for a in p_soup.find_all('a', href=True):
                    href = a['href']
                    if 'download-book-pdf?url=' in href:
                        match = re.search(r'url=([^&]+)', href)
                        if match:
                            raw_pdf = urllib.parse.unquote(urllib.parse.unquote(match.group(1)))
                            pdf_urls.append(raw_pdf)
                    elif 'archive.org/download/' in href and href.lower().endswith('.pdf'):
                        pdf_urls.append(href)
        except Exception as e:
            pass

    return book_page_url, list(set(pdf_urls))

def download_book(book_id, serial_no, title):
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    filename = f"{serial_no}_{safe_title[:50]}.pdf"
    dest_path = os.path.join(PDF_DIR, filename)

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
        print(f"[{serial_no}] Already downloaded: {filename}")
        return True

    print(f"[{serial_no}] Resolving download link for: {title}...")
    book_page, pdf_urls = get_links_for_book(serial_no)
    
    if not pdf_urls:
        print(f"[{serial_no}] No direct PDF URL found. Page: {book_page}")
        return False

    # Prefer archive.org mirror
    pdf_url = pdf_urls[0]
    for u in pdf_urls:
        if 'archive.org' in u:
            pdf_url = u
            break

    print(f"[{serial_no}] Downloading from: {pdf_url[:70]}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(urllib.parse.quote(pdf_url, safe=':/?=&'), headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest_path, 'wb') as out_f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                out_f.write(chunk)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE books SET local_pdf = ? WHERE id = ?', (filename, book_id))
        conn.commit()
        conn.close()

        print(f"[{serial_no}] Download complete: {filename} ({os.path.getsize(dest_path) / 1024 / 1024:.1f} MB)")
        return True
    except Exception as e:
        print(f"[{serial_no}] Download error: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def main():
    parser = argparse.ArgumentParser(description="KitaboSunnat Bulk PDF Downloader")
    parser.add_argument('--author', help='Download all books by specific author')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of books to download')
    parser.add_argument('--query', help='Search term to filter books to download')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if args.author:
        books = c.execute('SELECT id, serial_no, title FROM books WHERE author LIKE ? LIMIT ?', (f"%{args.author}%", args.limit)).fetchall()
    elif args.query:
        books = c.execute('SELECT id, serial_no, title FROM books WHERE title LIKE ? LIMIT ?', (f"%{args.query}%", args.limit)).fetchall()
    else:
        books = c.execute('SELECT id, serial_no, title FROM books ORDER BY CAST(serial_no AS REAL) DESC LIMIT ?', (args.limit,)).fetchall()

    conn.close()

    print(f"Found {len(books)} books to download.")
    for b in books:
        download_book(b[0], b[1], b[2])
        time.sleep(1)

if __name__ == '__main__':
    main()
