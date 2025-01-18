import sqlite3

conn = sqlite3.connect("bot_data.db")
cursor = conn.cursor()

def initialize_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS broadcasts (id INTEGER PRIMARY KEY, text TEXT)''')
    conn.commit()

def broadcast(content):
    cursor.execute("INSERT INTO broadcasts (text) VALUES (?)", (content,))
    conn.commit()
def last_news():
    cursor.execute("SELECT text FROM broadcasts ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    return result
def total():
    return cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]

def insert_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_all_users():
    return cursor.execute("SELECT user_id FROM users").fetchall() or []

def get_last_broadcast():
    cursor.execute("SELECT text FROM broadcasts ORDER BY id DESC LIMIT 1")
    return cursor.fetchone()

def insert_broadcast(text):
    cursor.execute("INSERT INTO broadcasts (text) VALUES (?)", (text,))
    conn.commit()

def delete_broadcast(news_id):
    cursor.execute("DELETE FROM broadcasts WHERE id=?", (news_id,))
    conn.commit()
    
def get_last_news_from_db():
    try:
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM broadcasts ORDER BY id DESC LIMIT 1")
        news = cursor.fetchall()
        conn.close()
        return news
    except Exception as e:
        print(f"Ошибка при извлечении новостей: {e}")
        return []

def add_broadcast(title, content):
    try:
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO broadcasts (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        conn.close()
        print("Новость успешно добавлена.")
    except Exception as e:
        print(f"Ошибка при добавлении новости: {e}")
