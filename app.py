import os
import sqlite3
import urllib.parse
from flask import Flask, render_template, request, jsonify, send_from_directory
import download_manager
import sync_catalog
import threading

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'kitabosunnat.db')
PDF_DIR = os.path.join(BASE_DIR, 'library_pdfs')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def api_stats():
    conn = get_db()
    c = conn.cursor()
    total_books = c.execute('SELECT COUNT(*) FROM books').fetchone()[0]
    total_authors = c.execute('SELECT COUNT(DISTINCT author) FROM books WHERE author != ""').fetchone()[0]
    total_publishers = c.execute('SELECT COUNT(DISTINCT publisher) FROM books WHERE publisher != ""').fetchone()[0]
    
    # Check offline books
    offline_count = 0
    if os.path.exists(PDF_DIR):
        offline_count = len([f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')])

    # Top authors
    top_authors = [r[0] for r in c.execute('''
        SELECT author, COUNT(*) as cnt 
        FROM books 
        WHERE author != "" 
        GROUP BY author 
        ORDER BY cnt DESC 
        LIMIT 10
    ''').fetchall()]

    # Top publishers
    top_publishers = [r[0] for r in c.execute('''
        SELECT publisher, COUNT(*) as cnt 
        FROM books 
        WHERE publisher != "" 
        GROUP BY publisher 
        ORDER BY cnt DESC 
        LIMIT 10
    ''').fetchall()]

    conn.close()
    return jsonify({
        'total_books': total_books,
        'total_authors': total_authors,
        'total_publishers': total_publishers,
        'offline_books': offline_count,
        'top_authors': top_authors,
        'top_publishers': top_publishers
    })

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    author = request.args.get('author', '').strip()
    publisher = request.args.get('publisher', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 24))
    offset = (page - 1) * limit

    conn = get_db()
    c = conn.cursor()

    params = []
    where_clauses = []

    # If full text query provided
    if q:
        # Check if q is a pure number (book serial number)
        if q.isdigit() or ('.' in q and q.replace('.', '', 1).isdigit()):
            where_clauses.append('(b.serial_no = ? OR b.serial_no LIKE ?)')
            params.extend([q, f"{q}%"])
        else:
            # Prepare FTS query with prefix wildcard
            clean_q = ''.join(ch for ch in q if ch.isalnum() or ch.isspace()).strip()
            if clean_q:
                terms = clean_q.split()
                fts_query = ' '.join(f'"{t}"*' for t in terms)
                where_clauses.append('b.id IN (SELECT rowid FROM books_fts WHERE books_fts MATCH ?)')
                params.append(fts_query)
            else:
                where_clauses.append('(b.title LIKE ? OR b.author LIKE ?)')
                params.extend([f"%{q}%", f"%{q}%"])

    if author:
        where_clauses.append('b.author = ?')
        params.append(author)

    if publisher:
        where_clauses.append('b.publisher = ?')
        params.append(publisher)

    where_sql = ' AND '.join(where_clauses)
    if where_sql:
        where_sql = 'WHERE ' + where_sql

    # Total count query
    count_sql = f'SELECT COUNT(*) FROM books b {where_sql}'
    total_results = c.execute(count_sql, params).fetchone()[0]

    # Data query
    data_sql = f'''
        SELECT b.id, b.serial_no, b.title, b.author, b.publisher, 
               b.kitabosunnat_url, b.search_url, b.archive_search_url, b.local_pdf
        FROM books b
        {where_sql}
        ORDER BY CAST(b.serial_no AS REAL) DESC
        LIMIT ? OFFSET ?
    '''
    rows = c.execute(data_sql, params + [limit, offset]).fetchall()

    books = []
    for r in rows:
        book_dict = dict(r)
        # Check if local PDF exists on disk
        has_local = False
        if book_dict.get('local_pdf'):
            pdf_path = os.path.join(PDF_DIR, book_dict['local_pdf'])
            has_local = os.path.exists(pdf_path)
        book_dict['is_offline'] = has_local
        books.append(book_dict)

    conn.close()

    return jsonify({
        'results': books,
        'total': total_results,
        'page': page,
        'limit': limit,
        'total_pages': (total_results + limit - 1) // limit if limit > 0 else 1
    })

@app.route('/api/download/<int:book_id>', methods=['POST'])
def trigger_download(book_id):
    conn = get_db()
    c = conn.cursor()
    row = c.execute('SELECT serial_no, title FROM books WHERE id = ?', (book_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Book not found'}), 404

    download_manager.start_download_thread(book_id, row['serial_no'], row['title'])
    return jsonify({'status': 'started', 'message': 'ڈاؤن لوڈ شروع کر دیا گیا ہے...'})

@app.route('/api/download/status/<int:book_id>')
def download_status(book_id):
    status = download_manager.download_status.get(book_id, {'status': 'idle', 'progress': 0})
    return jsonify(status)

@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(PDF_DIR, filename)

@app.route('/api/sync', methods=['POST'])
def trigger_sync():
    t = threading.Thread(target=sync_catalog.sync_catalog, daemon=True)
    t.start()
    return jsonify({'status': 'started', 'message': 'کیٹلاگ اپ ڈیٹ ہو رہا ہے...'})

if __name__ == '__main__':
    print("Starting KitaboSunnat Local Search Engine...")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(host='127.0.0.1', port=5000, debug=False)
