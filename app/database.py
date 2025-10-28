import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data' / 'finance.db'
PHOTO_DIR = Path(__file__).parent / 'data' / 'photos'

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
PHOTO_DIR.mkdir(parents=True, exist_ok=True)


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS accounts(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT, balance REAL)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS transactions(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT, account_id INTEGER,
                        category TEXT, amount REAL,
                        comment TEXT,
                        photo_path TEXT)''')  # добавили фото
        self.conn.commit()

    def add_account(self, name, balance=0):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO accounts(name,balance) VALUES(?,?)', (name, balance))
        self.conn.commit()

    def list_accounts(self):
        return self.conn.execute('SELECT * FROM accounts').fetchall()

    def add_transaction(self, date, account_id, category, amount, comment, photo_path=None):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO transactions(date, account_id, category, amount, comment, photo_path) VALUES (?, ?, ?, ?, ?, ?)',
            (date, account_id, category, amount, comment, photo_path)
        )
        self.conn.commit()

    def list_transactions(self):
        q = '''SELECT t.id,t.date,a.name as account,t.category,t.amount,t.comment,t.photo_path
               FROM transactions t JOIN accounts a ON a.id=t.account_id'''
        return self.conn.execute(q).fetchall()

    def update_account_balance(self, account_id, delta):
        cur = self.conn.cursor()
        cur.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (delta, account_id))
        self.conn
