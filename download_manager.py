import os
import re
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import sqlite3
import threading

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library_pdfs')
os.makedirs(PDF_DIR, exist_ok=True)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kitabosunnat.db')

download_status = {}

def get_direct_links_for_book(serial_no, title):
    """
    Attempts to find the direct book page and PDF download links on KitaboSunnat.
    """
    search_url = f"https://kitabosunnat.com/get-searched-book-by-number?searchword={serial_no}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    book_page_url = None
    pdf_urls = []
    
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            # Look for /kutub-library/<slug>
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/kutub-library/' in href:
                    parts = href.replace('https://kitabosunnat.com/kutub-library/', '').split('/')
                    if len(parts) == 1 and parts[0] != 'kutub-library':
                        book_page_url = href
                        break
    except Exception as e:
        print(f"Error fetching search page for #{serial_no}: {e}")

    # If book page found, fetch it to find direct PDF links
    if book_page_url:
        try:
            req2 = urllib.request.Request(urllib.parse.quote(book_page_url, safe=':/?=&'), headers=headers)
            with urllib.request.urlopen(req2, timeout=20) as resp2:
                p_html = resp2.read().decode('utf-8', errors='ignore')
                p_soup = BeautifulSoup(p_html, 'html.parser')
                for a in p_soup.find_all('a', href=True):
                    href = a['href']
                    if 'download-book-pdf?url=' in href:
                        # Extract the inner PDF url
                        match = re.search(r'url=([^&]+)', href)
                        if match:
                            raw_pdf = urllib.parse.unquote(urllib.parse.unquote(match.group(1)))
                            pdf_urls.append(raw_pdf)
                    elif 'archive.org/download/' in href and href.lower().endswith('.pdf'):
                        pdf_urls.append(href)
        except Exception as e:
            print(f"Error fetching book page {book_page_url}: {e}")

    return book_page_url, list(set(pdf_urls))

def download_book_task(book_id, serial_no, title):
    global download_status
    download_status[book_id] = {'status': 'fetching_links', 'progress': 0, 'message': 'ڈاؤن لوڈ لنکس تلاش کیے جا رہے ہیں...'}
    
    try:
        book_page_url, pdf_urls = get_direct_links_for_book(serial_no, title)
        
        # Save page url to DB if found
        if book_page_url:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE books SET kitabosunnat_url = ? WHERE id = ?', (book_page_url, book_id))
            conn.commit()
            conn.close()

        if not pdf_urls:
            download_status[book_id] = {
                'status': 'fallback',
                'progress': 0,
                'message': 'براہِ راست لنک دستیاب نہیں۔ کتاب و سنت کے صفحے پر جائیں۔',
                'page_url': book_page_url or f"https://kitabosunnat.com/get-searched-book-by-number?searchword={serial_no}"
            }
            return

        # Try downloading the first available PDF url
        pdf_url = pdf_urls[0]
        # Prefer archive.org if available because it's much faster
        for u in pdf_urls:
            if 'archive.org' in u:
                pdf_url = u
                break

        download_status[book_id] = {'status': 'downloading', 'progress': 5, 'message': 'پی ڈی ایف ڈاؤن لوڈ ہو رہی ہے...'}
        
        # Safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        filename = f"{serial_no}_{safe_title[:50]}.pdf"
        dest_path = os.path.join(PDF_DIR, filename)

        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(urllib.parse.quote(pdf_url, safe=':/?=&'), headers=headers)
        
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest_path, 'wb') as out_f:
            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0
            block_size = 64 * 1024
            while True:
                buf = resp.read(block_size)
                if not buf:
                    break
                out_f.write(buf)
                downloaded += len(buf)
                if total_size > 0:
                    pct = int((downloaded / total_size) * 90) + 5
                    download_status[book_id] = {'status': 'downloading', 'progress': pct, 'message': f'ڈاؤن لوڈنگ: {pct}%'}

        # Update DB with local path
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE books SET local_pdf = ? WHERE id = ?', (filename, book_id))
        conn.commit()
        conn.close()

        download_status[book_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'کامیابی سے محفوظ ہو گئی!',
            'filename': filename
        }

    except Exception as e:
        download_status[book_id] = {'status': 'error', 'progress': 0, 'message': f'غلطی: {str(e)}'}

def start_download_thread(book_id, serial_no, title):
    t = threading.Thread(target=download_book_task, args=(book_id, serial_no, title), daemon=True)
    t.start()
