import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
import json
import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
JSON_PATH = os.path.join(DATA_DIR, 'books.json')
DB_PATH = os.path.join(BASE_DIR, 'kitabosunnat.db')

def generate_json_from_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute('''
        SELECT serial_no, title, author, publisher, kitabosunnat_url, download_url 
        FROM books 
        ORDER BY CAST(serial_no AS REAL) DESC
    ''').fetchall()
    conn.close()

    books = []
    authors_set = set()
    publishers_set = set()
    direct_pdf_count = 0

    for r in rows:
        serial_no = r[0]
        title = r[1]
        author = r[2] if r[2] else ""
        publisher = r[3] if r[3] else ""
        page_url = r[4] if r[4] else f"https://kitabosunnat.com/get-searched-book-by-number?searchword={serial_no}"
        download_url = r[5] if r[5] else None
        
        if author:
            authors_set.add(author)
        if publisher:
            publishers_set.add(publisher)
        if download_url:
            direct_pdf_count += 1

        b = {
            's': serial_no,
            't': title,
            'a': author,
            'p': publisher,
            'u': page_url
        }
        if download_url:
            b['d'] = download_url

        books.append(b)

    author_counts = Counter(b['a'] for b in books if b['a'])
    publisher_counts = Counter(b['p'] for b in books if b['p'])

    data = {
        'total': len(books),
        'direct_pdf_count': direct_pdf_count,
        'authors_count': len(authors_set),
        'publishers_count': len(publishers_set),
        'top_authors': [a[0] for a in author_counts.most_common(12)],
        'top_publishers': [p[0] for p in publisher_counts.most_common(12)],
        'books': books
    }

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = os.path.getsize(JSON_PATH) / 1024
    print(f"Generated {JSON_PATH} with {len(books)} books ({size_kb:.1f} KB). Direct PDF count: {direct_pdf_count}.")

if __name__ == '__main__':
    generate_json_from_db()
