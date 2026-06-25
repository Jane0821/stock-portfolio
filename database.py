import sqlite3

def get_db_connection():
    """連線到SQLite資料庫"""
    conn = sqlite3.connect('portfolio.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化資料庫：建立 holdings 表格"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            shares INTEGER NOT NULL,
            buy_price REAL NOT NULL,
            note TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ 資料庫初始化完成！")