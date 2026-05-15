from flask import Flask, render_template, request, redirect, session, Response
import sqlite3, hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'libra_secret_2024'
DB = 'library.db'

# ── Database Initialisation ────────────────────────────────────────────────────
def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(
                 username TEXT PRIMARY KEY,
                 password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS books(
                 id       INTEGER PRIMARY KEY AUTOINCREMENT,
                 title    TEXT,
                 author   TEXT,
                 quantity INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS issued(
                 id         INTEGER PRIMARY KEY AUTOINCREMENT,
                 book_id    INTEGER,
                 student    TEXT,
                 issue_date TEXT,
                 due_date   TEXT)''')
    c.execute('INSERT OR IGNORE INTO users VALUES (?,?)',
              ('admin', hash_password('1234')))
    conn.commit()
    return conn

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        conn = connect()
        user = conn.execute(
            'SELECT * FROM users WHERE username=? AND password=?',
            (request.form['username'], hash_password(request.form['password']))
        ).fetchone()
        conn.close()
        if user:
            session['user'] = user['username']
            return redirect('/dashboard')
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = connect()
        conn.execute('INSERT OR IGNORE INTO users VALUES (?,?)',
                     (request.form['username'], hash_password(request.form['password'])))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    conn  = connect()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('dashboard.html', books=books, user=session['user'])

@app.route('/add', methods=['POST'])
def add_book():
    if 'user' not in session:
        return redirect('/')
    conn = connect()
    conn.execute('INSERT INTO books (title, author, quantity) VALUES (?,?,?)',
                 (request.form['title'], request.form['author'], int(request.form['quantity'])))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/delete/<int:bid>')
def delete_book(bid):
    if 'user' not in session:
        return redirect('/')
    conn = connect()
    conn.execute('DELETE FROM books WHERE id=?', (bid,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/search', methods=['POST'])
def search():
    if 'user' not in session:
        return redirect('/')
    q     = '%' + request.form['search'] + '%'
    conn  = connect()
    books = conn.execute(
        'SELECT * FROM books WHERE title LIKE ? OR author LIKE ?', (q, q)
    ).fetchall()
    conn.close()
    return render_template('dashboard.html', books=books, user=session['user'])

@app.route('/issue/<int:bid>', methods=['POST'])
def issue_book(bid):
    if 'user' not in session:
        return redirect('/')
    conn = connect()
    book = conn.execute('SELECT * FROM books WHERE id=?', (bid,)).fetchone()
    if book and book['quantity'] > 0:
        today = datetime.now().strftime('%Y-%m-%d')
        due   = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        conn.execute(
            'INSERT INTO issued (book_id, student, issue_date, due_date) VALUES (?,?,?,?)',
            (bid, request.form['student'], today, due)
        )
        conn.execute('UPDATE books SET quantity = quantity - 1 WHERE id=?', (bid,))
        conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/return/<int:iid>')
def return_book(iid):
    if 'user' not in session:
        return redirect('/')
    conn = connect()
    rec  = conn.execute('SELECT * FROM issued WHERE id=?', (iid,)).fetchone()
    if rec:
        due  = datetime.strptime(rec['due_date'], '%Y-%m-%d')
        fine = max(0, (datetime.now() - due).days) * 5
        conn.execute('UPDATE books SET quantity = quantity + 1 WHERE id=?', (rec['book_id'],))
        conn.execute('DELETE FROM issued WHERE id=?', (iid,))
        conn.commit()
    conn.close()
    return redirect('/issued')

@app.route('/issued')
def issued():
    if 'user' not in session:
        return redirect('/')
    conn    = connect()
    records = conn.execute(
        '''SELECT i.id, b.title, i.student, i.issue_date, i.due_date
           FROM issued i JOIN books b ON i.book_id = b.id
           ORDER BY i.due_date ASC'''
    ).fetchall()
    conn.close()
    return render_template('issued.html', records=records, user=session['user'])

@app.route('/overdue')
def overdue():
    if 'user' not in session:
        return redirect('/')
    today   = datetime.now().strftime('%Y-%m-%d')
    conn    = connect()
    records = conn.execute(
        '''SELECT i.id, b.title, i.student, i.issue_date, i.due_date,
                  CAST((julianday(?) - julianday(i.due_date)) AS INTEGER) AS days_overdue
           FROM issued i JOIN books b ON i.book_id = b.id
           WHERE i.due_date < ?
           ORDER BY i.due_date ASC''',
        (today, today)
    ).fetchall()
    conn.close()
    return render_template('overdue.html', records=records, user=session['user'])

@app.route('/export')
def export():
    if 'user' not in session:
        return redirect('/')
    conn  = connect()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    def generate():
        yield 'ID,Title,Author,Quantity\n'
        for b in books:
            yield f'{b["id"]},{b["title"]},{b["author"]},{b["quantity"]}\n'
    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=books.csv'})

@app.route('/admin')
def admin():
    if session.get('user') != 'admin':
        return redirect('/dashboard')
    today         = datetime.now().strftime('%Y-%m-%d')
    conn          = connect()
    users         = conn.execute('SELECT username FROM users').fetchall()
    books_count   = conn.execute('SELECT COUNT(*) as c FROM books').fetchone()['c']
    issued_count  = conn.execute('SELECT COUNT(*) as c FROM issued').fetchone()['c']
    overdue_count = conn.execute(
        'SELECT COUNT(*) as c FROM issued WHERE due_date < ?', (today,)
    ).fetchone()['c']
    conn.close()
    return render_template('admin.html',
                           users=users,
                           books_count=books_count,
                           issued_count=issued_count,
                           overdue_count=overdue_count,
                           user=session['user'])

if __name__ == '__main__':
    app.run(debug=True)
