import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
import json
import os
import olefile
import xlrd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
JSON_PATH = os.path.join(DATA_DIR, 'books.json')
EXCEL_PATH = os.path.join(BASE_DIR, 'books.xls')
DB_PATH = os.path.join(BASE_DIR, 'kitabosunnat.db')

def generate_json_from_db():
    if not os.path.exists(DB_PATH):
        print("Database not found, generating from Excel...")
        import build_database
        build_database.create_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute('''
        SELECT serial_no, title, author, publisher 
        FROM books 
        ORDER BY CAST(serial_no AS REAL) DESC
    ''').fetchall()
    conn.close()

    books = []
    authors_set = set()
    publishers_set = set()

    for r in rows:
        serial_no = r[0]
        title = r[1]
        author = r[2] if r[2] else ""
        publisher = r[3] if r[3] else ""
        
        if author:
            authors_set.add(author)
        if publisher:
            publishers_set.add(publisher)

        books.append({
            's': serial_no,
            't': title,
            'a': author,
            'p': publisher
        })

    # Find top 15 authors and publishers
    from collections import Counter
    author_counts = Counter(b['a'] for b in books if b['a'])
    publisher_counts = Counter(b['p'] for b in books if b['p'])

    data = {
        'total': len(books),
        'authors_count': len(authors_set),
        'publishers_count': len(publishers_set),
        'top_authors': [a[0] for a in author_counts.most_common(12)],
        'top_publishers': [p[0] for p in publisher_counts.most_common(12)],
        'books': books
    }

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = os.path.getsize(JSON_PATH) / 1024
    print(f"Generated {JSON_PATH} with {len(books)} books ({size_kb:.1f} KB).")

if __name__ == '__main__':
    generate_json_from_db()
